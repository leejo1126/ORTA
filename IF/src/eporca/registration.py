"""
Registration via the 561 fiducial channel (beads).

The 561 channel is acquired in every round/modality and carries fluorescent beads
(added after fixation). Beads are the BRIGHTEST features in 561, so we simply take
the ~100 brightest non-saturated point sources as bead candidates. They are
localized in 3D (3D Gaussian fit on the z-stack, not the max-projection) for
sub-pixel xy precision. Across two acquisitions of the same FOV the beads are the
stable correspondences; biology differs between rounds, so a RANSAC Euclidean
(rigid: translation + rotation) fit locks onto the beads and rejects the rest.

Reference frame = the 561-only (clean) acquisition. For IF there are two rounds
(561-only and interleaved) with per-FOV stage drift, so each FOV gets its own
transform. No DAPI mask is used (future modalities won't have one).

CLI: `eporca register --fov N`.
"""

from __future__ import annotations

import json

import numpy as np
from scipy.optimize import curve_fit
from scipy.spatial import cKDTree
from skimage.feature import peak_local_max
from skimage.registration import phase_cross_correlation
from skimage.measure import ransac
from skimage.transform import EuclideanTransform

from .config import Config
from .dax_reader import read_dax_multichannel
from .io_zarr import read_channel


def _fit_gaussian_3d(subvol):
    """Fit an anisotropic 3D Gaussian; return (z0, y0, x0, amp, sxy, ok) in local coords."""
    nz, ny, nx = subvol.shape
    zz, yy, xx = np.mgrid[0:nz, 0:ny, 0:nx]
    p = subvol.astype(float)
    p0 = (p.max() - p.min(), nz / 2.0, ny / 2.0, nx / 2.0, 1.5, 2.0, p.min())

    def g(c, A, z0, y0, x0, sxy, sz, b):
        z, y, x = c
        return (A * np.exp(-((y - y0) ** 2 + (x - x0) ** 2) / (2 * sxy * sxy)
                           - (z - z0) ** 2 / (2 * sz * sz)) + b).ravel()

    try:
        popt, _ = curve_fit(g, (zz, yy, xx), p.ravel(), p0=p0, maxfev=4000)
        A, z0, y0, x0, sxy, sz, b = popt
        ok = (0 <= y0 < ny) and (0 <= x0 < nx) and (0 <= z0 < nz) and (0.6 < abs(sxy) < 3.5) and A > 0
        return z0, y0, x0, A, abs(sxy), ok
    except Exception:
        return nz / 2.0, ny / 2.0, nx / 2.0, 0.0, 0.0, False


def detect_beads(vol, n=100, min_distance=7, thresh_pct=99.0, saturation=64000,
                 win=5, zwin=3):
    """The ~`n` brightest non-saturated point sources (beads), localized in 3D.
    Returns (n, 2) sub-pixel (y, x)."""
    mip = vol.max(axis=0)
    thr = np.percentile(mip, thresh_pct)
    cand = peak_local_max(mip, min_distance=min_distance, threshold_abs=thr, num_peaks=500)
    cand = sorted(cand, key=lambda p: -mip[p[0], p[1]])     # brightest first
    Z, H, W = vol.shape
    beads = []
    for y, x in cand:
        if mip[y, x] >= saturation:
            continue                                        # saturated -> poor fit
        z = int(np.argmax(vol[:, y, x]))
        z0, z1 = max(0, z - zwin), min(Z, z + zwin + 1)
        y0, y1 = max(0, y - win), min(H, y + win + 1)
        x0, x1 = max(0, x - win), min(W, x + win + 1)
        fz, fy, fx, amp, sxy, ok = _fit_gaussian_3d(vol[z0:z1, y0:y1, x0:x1])
        if not ok:
            continue
        beads.append((y0 + fy, x0 + fx, amp))
        if len(beads) >= n:
            break                                           # candidates are brightest-first
    return np.array([[b[0], b[1]] for b in beads], dtype=float) if beads else np.empty((0, 2))


def register_549(ref_vol, mov_vol, n_beads=100, match_radius=10.0,
                 residual_threshold=1.0, min_inliers=4):
    """Fit moving-561 -> reference-561 rigid transform from 3D-localized beads.
    Returns (model_or_None, stats); transform maps moving (x, y) -> reference frame."""
    ref_mip, mov_mip = ref_vol.max(axis=0), mov_vol.max(axis=0)
    ref_pts = detect_beads(ref_vol, n=n_beads)
    mov_pts = detect_beads(mov_vol, n=n_beads)
    stats = {"n_ref_beads": int(len(ref_pts)), "n_mov_beads": int(len(mov_pts)), "status": "ok"}
    if len(ref_pts) < min_inliers or len(mov_pts) < min_inliers:
        stats["status"] = "too_few_beads"
        return None, stats, ref_mip, ref_pts, mov_pts

    shift, _, _ = phase_cross_correlation(ref_mip, mov_mip, upsample_factor=10)
    stats["coarse_shift_yx"] = [float(shift[0]), float(shift[1])]
    d, idx = cKDTree(ref_pts).query(mov_pts + np.array(shift), k=1)
    keep = d <= match_radius
    stats["n_matches"] = int(keep.sum())
    if keep.sum() < min_inliers:
        stats["status"] = "too_few_matches"
        return None, stats, ref_mip, ref_pts, mov_pts

    src = mov_pts[keep][:, ::-1]
    dst = ref_pts[idx[keep]][:, ::-1]
    model, inliers = ransac((src, dst), EuclideanTransform, min_samples=2,
                            residual_threshold=residual_threshold, max_trials=3000)
    res = np.sqrt(((model(src[inliers]) - dst[inliers]) ** 2).sum(1)) if inliers.sum() else np.array([])
    stats.update({
        "n_inliers": int(inliers.sum()),
        "rotation_deg": float(np.degrees(model.rotation)),
        "translation_px": [float(t) for t in model.translation],
        "residual_px": float(res.mean()) if res.size else None,
        "residual_p90_px": float(np.percentile(res, 90)) if res.size else None,
        "transform_matrix": model.params.tolist(),
    })
    if inliers.sum() < min_inliers:
        stats["status"] = "ransac_failed"
    return model, stats, ref_mip, ref_pts, mov_pts


def register_fov(cfg: Config, fov: int) -> dict:
    """Align interleaved-561 (moving) to the clean 561-only (reference) for one FOV
    using 3D-localized beads; save transform + QC overlay."""
    ref_vol = np.asarray(read_channel(cfg, fov, "Pol2", trim=False)).astype(np.float32)  # 561-only
    vol, _ = read_dax_multichannel(cfg.interleaved_path(fov), cfg.acquisition.n_interleaved_channels)
    mov_vol = np.asarray(vol[:, 1]).astype(np.float32)                                    # interleaved 561
    model, stats, ref_mip, ref_pts, mov_pts = register_549(ref_vol, mov_vol)
    stats["fov"] = fov
    _save(cfg, fov, model, stats, ref_mip, ref_pts, mov_pts)
    return stats


def _save(cfg, fov, model, stats, ref_mip=None, ref_pts=None, mov_pts=None):
    outdir = cfg.data_dir / "registration"
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / f"fov_{fov:03d}.json").write_text(json.dumps(stats, indent=2))
    if model is None or ref_mip is None:
        return
    try:
        from PIL import Image, ImageDraw
        lo, hi = np.percentile(ref_mip, [1, 99.9])
        g = (np.clip((ref_mip - lo) / max(hi - lo, 1), 0, 1) * 255).astype(np.uint8)
        img = Image.fromarray(np.stack([g] * 3, -1)); d = ImageDraw.Draw(img)
        for y, x in ref_pts:
            d.ellipse([x - 5, y - 5, x + 5, y + 5], outline=(255, 0, 0))       # reference beads
        for y, x in mov_pts:
            tx, ty = model([[x, y]])[0]
            d.ellipse([tx - 3, ty - 3, tx + 3, ty + 3], outline=(0, 255, 0))    # transformed moving
        img.save(outdir / f"fov_{fov:03d}_qc.png")
    except Exception:
        pass


def load_transform(cfg: Config, fov: int):
    p = cfg.data_dir / "registration" / f"fov_{fov:03d}.json"
    if not p.exists():
        return None
    m = json.loads(p.read_text()).get("transform_matrix")
    return EuclideanTransform(matrix=np.array(m)) if m else None


def apply_to_coords_xy(coords_xy: np.ndarray, model) -> np.ndarray:
    """Map moving-561 (x, y) pixel coords into the reference (561-only) frame."""
    return model(coords_xy) if model is not None else coords_xy
