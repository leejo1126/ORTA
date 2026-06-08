"""
Registration via the 561 fiducial channel (beads).

The 561 channel is acquired in every round/modality and carries fluorescent beads
added after fixation, so beads sit in the BACKGROUND, never overlapping nuclei.
We align each acquisition's 561 to a reference 561 (the 561-only, post-bleach
acquisition is the master frame). For IF there are two rounds — 561-only and the
interleaved 4-channel — with per-FOV stage drift, so each FOV gets its own
rigid (translation + rotation) transform fitted from the beads.

Bead detection is MASK-FREE (future modalities won't have a DAPI mask): beads are
bright, small, point-like spots sitting in DARK BACKGROUND (cell-free) — so we keep
non-saturated point sources whose local surround (annulus) is near background,
which excludes in-nucleus biology without any mask. Each is localized by a 2D
Gaussian fit; keep the top ~20 brightest. Matching is coarse-aligned by phase
correlation then RANSAC-fit with a EuclideanTransform (rigid), which rejects beads
that moved or were lost.

CLI: `eporca register --fov N`. Standalone for now; applying the transform to put
Pol2 foci and DAPI nuclei in the shared 561-only frame is a later integration.
"""

from __future__ import annotations

import json

import numpy as np
import scipy.ndimage as ndi
from scipy.optimize import curve_fit
from scipy.spatial import cKDTree
from skimage.feature import peak_local_max
from skimage.registration import phase_cross_correlation
from skimage.measure import ransac
from skimage.transform import EuclideanTransform

from .config import Config
from .dax_reader import read_dax_multichannel
from .io_zarr import read_channel


def _fit_gaussian_2d(patch):
    """Fit A*exp(-r^2/2s^2)+b to a small patch; return (y0, x0, amp, sigma, ok)."""
    ny, nx = patch.shape
    yy, xx = np.mgrid[0:ny, 0:nx]
    p = patch.astype(float)
    p0 = (p.max() - p.min(), ny / 2.0, nx / 2.0, 1.5, p.min())

    def g(c, A, y0, x0, s, b):
        y, x = c
        return (A * np.exp(-((y - y0) ** 2 + (x - x0) ** 2) / (2 * s * s)) + b).ravel()

    try:
        popt, _ = curve_fit(g, (yy, xx), p.ravel(), p0=p0, maxfev=2000)
        A, y0, x0, s, b = popt
        ok = (0 <= y0 < ny) and (0 <= x0 < nx) and (0.6 < abs(s) < 3.5) and A > 0
        return y0, x0, A, abs(s), ok
    except Exception:
        return ny / 2.0, nx / 2.0, 0.0, 0.0, False


def _annulus_median(mip, y, x, r_in=4, r_out=9):
    """Median intensity in a ring around (y, x) — the local background level."""
    H, W = mip.shape
    y0, y1 = max(0, y - r_out), min(H, y + r_out + 1)
    x0, x1 = max(0, x - r_out), min(W, x + r_out + 1)
    yy, xx = np.mgrid[y0:y1, x0:x1]
    r = np.sqrt((yy - y) ** 2 + (xx - x) ** 2)
    ring = (r > r_in) & (r <= r_out)
    return float(np.median(mip[y0:y1, x0:x1][ring])) if ring.any() else float(mip[y, x])


def detect_beads(mip, n=100, min_distance=7, thresh_pct=99.0, saturation=64000,
                 win=5, bg_factor=1.5, exclude_mask=None):
    """Top-`n` bright, point-like, non-saturated beads in DARK BACKGROUND (no mask
    needed), localized by 2D Gaussian fit. A candidate is kept only if its local
    surround (annulus) is near the global background, which rejects in-nucleus
    biology. `exclude_mask` is optional and used only if provided. Returns (n,2)
    sub-pixel (y, x)."""
    thr = np.percentile(mip, thresh_pct)
    bg_level = np.percentile(mip, 20)                  # typical background
    cand = peak_local_max(mip, min_distance=min_distance, threshold_abs=thr, num_peaks=800)
    beads = []
    H, W = mip.shape
    for y, x in cand:
        if mip[y, x] >= saturation:
            continue                                   # saturated -> poor fit
        if exclude_mask is not None and exclude_mask[y, x]:
            continue
        if _annulus_median(mip, y, x) > bg_factor * bg_level + 1:
            continue                                   # bright surround -> inside a cell, not a bead
        y0, y1 = max(0, y - win), min(H, y + win + 1)
        x0, x1 = max(0, x - win), min(W, x + win + 1)
        fy, fx, amp, sig, ok = _fit_gaussian_2d(mip[y0:y1, x0:x1])
        if not ok:
            continue
        beads.append((y0 + fy, x0 + fx, amp))
    beads.sort(key=lambda b: -b[2])                    # brightest first
    return np.array([[b[0], b[1]] for b in beads[:n]], dtype=float) if beads else np.empty((0, 2))


def register_549(ref_mip, mov_mip, ref_excl=None, mov_excl=None,
                 n_beads=100, match_radius=10.0, residual_threshold=1.5, min_inliers=4):
    """Fit moving-561 -> reference-561 rigid transform from beads. Returns
    (model_or_None, stats); transform maps moving (x, y) into the reference frame."""
    ref_pts = detect_beads(ref_mip, n=n_beads, exclude_mask=ref_excl)
    mov_pts = detect_beads(mov_mip, n=n_beads, exclude_mask=mov_excl)
    stats = {"n_ref_beads": int(len(ref_pts)), "n_mov_beads": int(len(mov_pts)), "status": "ok"}
    if len(ref_pts) < min_inliers or len(mov_pts) < min_inliers:
        stats["status"] = "too_few_beads"
        return None, stats

    shift, _, _ = phase_cross_correlation(ref_mip, mov_mip, upsample_factor=10)
    stats["coarse_shift_yx"] = [float(shift[0]), float(shift[1])]
    d, idx = cKDTree(ref_pts).query(mov_pts + np.array(shift), k=1)
    keep = d <= match_radius
    stats["n_matches"] = int(keep.sum())
    if keep.sum() < min_inliers:
        stats["status"] = "too_few_matches"
        return None, stats

    src = mov_pts[keep][:, ::-1]                        # (x, y)
    dst = ref_pts[idx[keep]][:, ::-1]
    model, inliers = ransac((src, dst), EuclideanTransform, min_samples=2,
                            residual_threshold=residual_threshold, max_trials=2000)
    stats["n_inliers"] = int(inliers.sum())
    stats["rotation_deg"] = float(np.degrees(model.rotation))
    stats["translation_px"] = [float(t) for t in model.translation]
    stats["residual_px"] = float(
        np.sqrt(((model(src[inliers]) - dst[inliers]) ** 2).sum(1).mean())) if inliers.sum() else None
    stats["transform_matrix"] = model.params.tolist()
    if inliers.sum() < min_inliers:
        stats["status"] = "ransac_failed"
    return model, stats


def register_fov(cfg: Config, fov: int) -> dict:
    """Align the interleaved-561 (moving) to the clean 561-only (reference) for one
    FOV; save transform + QC overlay. Reference frame = the 561-only acquisition.
    Bead detection is mask-free (dark-background criterion)."""
    ref_mip = np.asarray(read_channel(cfg, fov, "Pol2", trim=False)).max(axis=0)  # 561-only
    vol, _ = read_dax_multichannel(cfg.interleaved_path(fov),
                                   cfg.acquisition.n_interleaved_channels)
    mov_mip = np.asarray(vol[:, 1]).max(axis=0)                                   # interleaved 561
    model, stats = register_549(ref_mip, mov_mip)
    stats["fov"] = fov
    _save(cfg, fov, model, stats, ref_mip, detect_beads(ref_mip), detect_beads(mov_mip))
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
            d.ellipse([x - 5, y - 5, x + 5, y + 5], outline=(255, 0, 0))      # reference beads
        for y, x in mov_pts:
            tx, ty = model([[x, y]])[0]
            d.ellipse([tx - 3, ty - 3, tx + 3, ty + 3], outline=(0, 255, 0))   # transformed moving
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
