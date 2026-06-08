"""
Cross-modality bead registration: align the separate post-bleach 561 acquisition
(clean Pol2, zscan_561) to the interleaved 4-channel frame (which provides the
DAPI nuclei). Fluorescent beads are bright point sources present in BOTH
acquisitions; we detect them, match them robustly (RANSAC), and fit a transform
that maps clean-561 coordinates into the interleaved frame.

Robustness ideas:
  * True beads are broadband -> they appear as bright peaks in ALL interleaved
    channels at once, while biological signal is channel-specific. So interleaved
    beads = peaks co-localized across all 4 channels (rejects Brd4/Pol2/etc.).
  * A coarse shift (phase cross-correlation of the two 561 MIPs) seeds the match;
    RANSAC then fits an affine transform and rejects beads that moved / were lost.

This is a standalone workflow (CLI: `eporca register --fov N`). Applying the
transform to Pol2 foci coordinates is a later integration step; parameters use
sensible defaults and can be promoted to config once validated on real bead data.

NOTE: untested on this dataset's beads yet — bead brightness/density unknown.
Inspect the QC overlay (data/registration/fov_xxx_qc.png) before trusting it.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from skimage.feature import peak_local_max
from skimage.registration import phase_cross_correlation
from skimage.measure import ransac
from skimage.transform import AffineTransform
from scipy.spatial import cKDTree

from .config import Config
from .dax_reader import read_dax_multichannel


def _peaks(mip, min_distance=5, thresh_pct=99.5, max_n=400):
    """Bright point-source candidates in a 2D MIP, with sub-pixel centroids."""
    thr = np.percentile(mip, thresh_pct)
    pk = peak_local_max(mip, min_distance=min_distance, threshold_abs=thr, num_peaks=max_n)
    # sub-pixel refine via local centroid in a 3x3 window
    refined = []
    for y, x in pk:
        y0, y1 = max(0, y - 1), min(mip.shape[0], y + 2)
        x0, x1 = max(0, x - 1), min(mip.shape[1], x + 2)
        w = mip[y0:y1, x0:x1].astype(float)
        s = w.sum()
        if s <= 0:
            refined.append((y, x)); continue
        yy, xx = np.mgrid[y0:y1, x0:x1]
        refined.append((float((yy * w).sum() / s), float((xx * w).sum() / s)))
    return np.array(refined, dtype=float) if refined else np.empty((0, 2))


def detect_interleaved_beads(cfg: Config, fov: int, coloc_radius=3.0, **kw):
    """Beads in the interleaved frame = bright peaks present in ALL channels."""
    vol, _ = read_dax_multichannel(cfg.interleaved_path(fov), cfg.acquisition.n_interleaved_channels)
    mips = [np.asarray(vol[:, c]).max(axis=0) for c in range(cfg.acquisition.n_interleaved_channels)]
    base = _peaks(mips[0], **kw)
    if len(base) == 0:
        return base, mips
    trees = [cKDTree(_peaks(m, **kw)) for m in mips[1:]]
    keep = []
    for p in base:
        if all(len(t.data) and t.query(p)[0] <= coloc_radius for t in trees):
            keep.append(p)
    return (np.array(keep) if keep else np.empty((0, 2))), mips


def detect_clean561_beads(cfg: Config, fov: int, **kw):
    """Beads in the clean-561 (Pol2) acquisition: bright point sources in its MIP."""
    from .io_zarr import read_channel
    mip = read_channel(cfg, fov, "Pol2", trim=False).max(axis=0)
    return _peaks(np.asarray(mip), **kw), np.asarray(mip)


def register_fov(cfg: Config, fov: int, min_inliers: int = 5,
                 residual_threshold: float = 2.0) -> dict:
    """Estimate the clean-561 -> interleaved affine transform from beads; save it
    plus a QC overlay. Returns a summary dict (n_inliers, residual, transform)."""
    ref_beads, ref_mips = detect_interleaved_beads(cfg, fov)
    mov_beads, mov_mip = detect_clean561_beads(cfg, fov)
    ref_561 = ref_mips[1]  # interleaved 561 channel

    result = {"fov": fov, "n_ref_beads": int(len(ref_beads)),
              "n_mov_beads": int(len(mov_beads)), "status": "ok"}
    if len(ref_beads) < min_inliers or len(mov_beads) < min_inliers:
        result["status"] = "too_few_beads"
        _save(cfg, fov, None, result)
        return result

    # coarse shift from phase correlation of the two 561 MIPs
    shift, _, _ = phase_cross_correlation(ref_561, mov_mip, upsample_factor=10)
    mov_shifted = mov_beads + np.array(shift)        # (dy, dx)

    # nearest-neighbour match (moving -> ref) after coarse alignment
    tree = cKDTree(ref_beads)
    d, idx = tree.query(mov_shifted, k=1)
    keep = d <= 5.0
    if keep.sum() < min_inliers:
        result["status"] = "too_few_matches"; result["n_matches"] = int(keep.sum())
        _save(cfg, fov, None, result)
        return result
    src = mov_beads[keep][:, ::-1]                    # (x, y) for skimage transforms
    dst = ref_beads[idx[keep]][:, ::-1]

    model, inliers = ransac((src, dst), AffineTransform, min_samples=3,
                            residual_threshold=residual_threshold, max_trials=1000)
    result.update({
        "n_matches": int(keep.sum()), "n_inliers": int(inliers.sum()),
        "residual_px": float(np.sqrt(((model(src[inliers]) - dst[inliers]) ** 2).sum(1).mean())),
        "transform_matrix": model.params.tolist(),  # 3x3 affine (xy homogeneous)
    })
    if inliers.sum() < min_inliers:
        result["status"] = "ransac_failed"
    _save(cfg, fov, model, result, ref_561, ref_beads, mov_beads)
    return result


def _save(cfg, fov, model, result, ref_561=None, ref_beads=None, mov_beads=None):
    outdir = cfg.data_dir / "registration"
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / f"fov_{fov:03d}.json").write_text(json.dumps(result, indent=2))
    if model is None or ref_561 is None:
        return
    try:
        from PIL import Image, ImageDraw
        lo, hi = np.percentile(ref_561, [1, 99.8])
        g = (np.clip((ref_561 - lo) / max(hi - lo, 1), 0, 1) * 255).astype(np.uint8)
        rgb = np.stack([g] * 3, -1)
        img = Image.fromarray(rgb); d = ImageDraw.Draw(img)
        for y, x in ref_beads:                        # interleaved beads = red
            d.ellipse([x - 4, y - 4, x + 4, y + 4], outline=(255, 0, 0))
        for y, x in mov_beads:                         # transformed clean beads = green
            tx, ty = model([[x, y]])[0]
            d.ellipse([tx - 3, ty - 3, tx + 3, ty + 3], outline=(0, 255, 0))
        img.save(outdir / f"fov_{fov:03d}_qc.png")
    except Exception:
        pass


def load_transform(cfg: Config, fov: int):
    p = cfg.data_dir / "registration" / f"fov_{fov:03d}.json"
    if not p.exists():
        return None
    rec = json.loads(p.read_text())
    m = rec.get("transform_matrix")
    return AffineTransform(matrix=np.array(m)) if m else None


def apply_to_coords_xy(coords_xy: np.ndarray, model) -> np.ndarray:
    """Map clean-561 (x, y) pixel coords into the interleaved frame."""
    return model(coords_xy) if model is not None else coords_xy
