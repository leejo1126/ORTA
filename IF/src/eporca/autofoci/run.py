"""
Executor for the autofoci search: run a detector spec over a fixed panel of nuclei and
return **agnostic proxy metrics** (no target count) + a QC montage. The proxies score
"does this look like real foci" from image evidence alone -- focus contrast/SNR, count
reproducibility across cells, fill sanity, and size-distribution sanity -- and are made
**SNR-aware** (at low image SNR, contrast/stability are weighted more), per Smal 2010.

A spec that produces degenerate output (nothing, or space-filling) fails a validity gate
and is scored ~0 without needing an LLM look.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import scipy.ndimage as ndi
from PIL import Image, ImageDraw

from ..config import Config
from ..io_zarr import read_channel
from ..foci import subtract_background, load_nuclear_labels_3d, _expand_slices
from .spec import Spec, detect_core


@dataclass
class Panel:
    marker: str
    fov: int
    cells: list[int]
    raw: np.ndarray          # background-subtracted (z,y,x)
    nuc: np.ndarray          # nucleus labels (z,y,x)
    slices: list             # ndi.find_objects output
    image_snr: float         # panel-level SNR (p99 - bg_med)/bg_mad
    voxel_um3: float = 1.0   # physical voxel volume (px*px*z), for eq-diameter


def build_panel(cfg: Config, marker: str, fov: int = 0, n: int = 6,
                cells: list[int] | None = None) -> Panel:
    """Deterministic panel: the n largest nuclei in a FOV (same picking as the tuning
    tool), the background-subtracted channel, and a panel-level SNR estimate."""
    raw = subtract_background(
        read_channel(cfg, fov, marker, trim=True).astype(np.float32), cfg.foci.background)
    nuc = load_nuclear_labels_3d(cfg, fov, raw.shape)
    slices = ndi.find_objects(nuc)
    if cells is None:
        counts = np.bincount(nuc.ravel()); counts[0] = 0
        cells = [int(c) for c in np.argsort(counts)[::-1][:n]]
    innuc = raw[nuc > 0]
    bg_med = float(np.median(innuc)) if innuc.size else 0.0
    bg_mad = float(np.median(np.abs(innuc - bg_med))) * 1.4826 if innuc.size else 1.0
    p99 = float(np.percentile(innuc, 99)) if innuc.size else 1.0
    snr = (p99 - bg_med) / (bg_mad if bg_mad > 0 else 1.0)
    px, zum = cfg.acquisition.pixel_size_um, cfg.acquisition.z_um
    return Panel(marker, fov, cells, raw, nuc, slices, snr, voxel_um3=px * px * zum)


def _bump(x, lo, hi):
    """1 inside [lo,hi], linearly decaying to 0 by a decade outside; 0 at x<=0."""
    if x <= 0:
        return 0.0
    if lo <= x <= hi:
        return 1.0
    if x < lo:
        return max(0.0, 1.0 - (np.log10(lo) - np.log10(x)))
    return max(0.0, 1.0 - (np.log10(x) - np.log10(hi)))


def _cell_metrics(lab, subraw, subnuc):
    """Per-cell proxy ingredients computed on one nucleus."""
    n = int(lab.max())
    nucvol = int(subnuc.sum()) or 1
    fg = (lab > 0) & subnuc
    fill = float(fg.sum()) / nucvol
    bg = subraw[subnuc & (lab == 0)]
    bg_med = float(np.median(bg)) if bg.size else 0.0
    bg_mad = (float(np.median(np.abs(bg - bg_med))) * 1.4826) if bg.size else 1.0
    bg_mad = bg_mad if bg_mad > 0 else 1.0
    vols, contrasts = [], []
    if n:
        # volume + mean intensity per label in one pass
        means = ndi.mean(subraw, labels=lab, index=np.arange(1, n + 1))
        counts = np.bincount(lab.ravel())[1:n + 1]
        for m, v in zip(np.atleast_1d(means), np.atleast_1d(counts)):
            if v <= 0:
                continue
            vols.append(int(v))
            contrasts.append((float(m) - bg_med) / bg_mad)
    return {"count": n, "fill": fill, "vols": vols, "contrasts": contrasts, "nucvol": nucvol}


def _range_score(x, lo, hi, under_pow=1.5):
    """1 inside [lo,hi]; below lo decays as (x/lo)**under_pow (steeper => punishes
    under-detection / false negatives harder); above hi decays as hi/x."""
    if x <= 0:
        return 0.0
    if x < lo:
        return float((x / lo) ** under_pow)
    if x > hi:
        return float(max(0.0, hi / x))
    return 1.0


def _eq_diam_um(vol_voxels, voxel_um3):
    """Equivalent-sphere diameter (um) of a region of `vol_voxels` voxels."""
    v_um3 = vol_voxels * voxel_um3
    return float((6.0 * v_um3 / np.pi) ** (1.0 / 3.0)) if v_um3 > 0 else 0.0


def proxy_metrics(per_cell: list[dict], image_snr: float, voxel_um3: float = 1.0,
                  expect: dict | None = None) -> dict:
    """Aggregate per-cell ingredients into metrics + a single score in [0,1].

    Two scoring modes:
      - `expect` given (literature-anchored, the default for the search): combine
        count / shape / coverage scored against the marker's expected ranges, with the
        **count term asymmetric to punish under-detection (false negatives)**.
      - `expect` None (agnostic fallback): the original contrast/reproducibility/
        fill/size composite.
    """
    counts = np.array([c["count"] for c in per_cell], dtype=float)
    fills = np.array([c["fill"] for c in per_cell], dtype=float)
    all_vols = np.array([v for c in per_cell for v in c["vols"]], dtype=float)
    all_con = np.array([x for c in per_cell for x in c["contrasts"]], dtype=float)

    median_count = float(np.median(counts)) if counts.size else 0.0
    count_cv = float(np.std(counts) / np.mean(counts)) if counts.size and counts.mean() > 0 else 9.9
    median_fill = float(np.median(fills)) if fills.size else 0.0
    median_contrast = float(np.median(all_con)) if all_con.size else 0.0
    median_vol = float(np.median(all_vols)) if all_vols.size else 0.0
    median_eq_diam = _eq_diam_um(median_vol, voxel_um3)
    frac_tiny = float(np.mean(all_vols < 3)) if all_vols.size else 1.0
    nucvol = float(np.median([c["nucvol"] for c in per_cell])) if per_cell else 1.0
    frac_huge = float(np.mean(all_vols > 0.05 * nucvol)) if all_vols.size else 0.0

    valid = (median_count >= 1) and (median_fill < 0.6) and (median_count < 5000)
    contrast_term = float(np.tanh(median_contrast / 5.0))
    repro_term = 1.0 / (1.0 + count_cv)
    out = {
        "valid": bool(valid), "median_count": median_count, "count_cv": round(count_cv, 3),
        "median_fill": round(median_fill, 4), "median_contrast": round(median_contrast, 2),
        "median_vol": median_vol, "median_eq_diam_um": round(median_eq_diam, 3),
        "frac_tiny": round(frac_tiny, 3), "frac_huge": round(frac_huge, 3),
        "image_snr": round(image_snr, 2),
    }

    if expect:
        c_lo, c_hi = expect.get("count", [1, 5000])
        d_lo, d_hi = expect.get("eq_diam_um", [0.0, 1e9])
        v_lo, v_hi = expect.get("coverage", [0.0, 1.0])
        count_s = _range_score(median_count, c_lo, c_hi)        # FN-punishing
        diam_s = _range_score(median_eq_diam, d_lo, d_hi)
        clean = (1.0 - frac_tiny) * (1.0 - frac_huge)           # specks/merged penalty
        shape_s = 0.6 * diam_s + 0.4 * clean
        cov_s = _range_score(median_fill, v_lo, v_hi)
        quality = 0.5 * contrast_term + 0.5 * repro_term        # tie-breaker
        score = 0.85 * (0.45 * count_s + 0.30 * shape_s + 0.25 * cov_s) + 0.15 * quality
        out.update({"count_score": round(count_s, 3), "shape_score": round(shape_s, 3),
                    "coverage_score": round(cov_s, 3), "anchored": True})
    else:
        fill_term = _bump(median_fill, 0.002, 0.25)
        size_term = (1.0 - frac_tiny) * (1.0 - frac_huge)
        low = image_snr < 8.0
        w = ({"c": 0.45, "r": 0.30, "f": 0.10, "s": 0.15} if low
             else {"c": 0.30, "r": 0.20, "f": 0.25, "s": 0.25})
        score = (w["c"] * contrast_term + w["r"] * repro_term +
                 w["f"] * fill_term + w["s"] * size_term)
        out["anchored"] = False

    if not valid:
        score *= 0.05
    out["score"] = round(score, 4)
    return out


# ------------------------------------------------------------------------ montage
def _stretch(img, lo=1.0, hi=99.8):
    a, b = np.percentile(img, [lo, hi])
    b = b if b > a else a + 1
    return (np.clip((img.astype(np.float32) - a) / (b - a), 0, 1) * 255).astype(np.uint8)


def _colorize(gray, lab2d, rng, alpha=0.55):
    base = np.stack([gray] * 3, -1).astype(np.float32)
    out = base.copy()
    for i in np.unique(lab2d):
        if i == 0:
            continue
        m = lab2d == i
        out[m] = (1 - alpha) * base[m] + alpha * rng.integers(60, 256, 3)
    return out.astype(np.uint8)


def run_spec(panel: Panel, spec: Spec, out_png: str | None = None, mag: int = 4,
             expect: dict | None = None) -> dict:
    """Run a spec over the panel; return proxy metrics (+ montage path if out_png).
    `expect` (literature ranges) anchors the score to count/shape/coverage."""
    rng = np.random.default_rng(0)
    per_cell, panels = [], []
    for L in panel.cells:
        sl = _expand_slices(panel.slices[L - 1], panel.raw.shape, (1, 8, 8))
        subnuc = panel.nuc[sl] == L
        subraw = np.ascontiguousarray(panel.raw[sl])
        lab = detect_core(spec, subraw, subnuc)
        per_cell.append(_cell_metrics(lab, subraw, subnuc))
        if out_png:
            zs = np.where(subnuc.any(axis=(1, 2)))[0]
            zmid = int(zs[len(zs) // 2]) if len(zs) else subnuc.shape[0] // 2
            ov = _colorize(_stretch(subraw[zmid]), lab[zmid], rng)
            im = Image.fromarray(ov).resize((ov.shape[1] * mag, ov.shape[0] * mag), Image.NEAREST)
            ImageDraw.Draw(im).text((4, 4), f"{spec.family} c{L} n={int(lab.max())}",
                                    fill=(255, 255, 0))
            panels.append(im)

    metrics = proxy_metrics(per_cell, panel.image_snr, panel.voxel_um3, expect)
    metrics["family"] = spec.family
    metrics["params"] = spec.validated().with_defaults()
    metrics["per_cell_counts"] = [c["count"] for c in per_cell]
    if out_png and panels:
        w = sum(p.width for p in panels) + 6 * (len(panels) - 1)
        mont = Image.new("RGB", (w, max(p.height for p in panels)), (15, 15, 15))
        x = 0
        for p in panels:
            mont.paste(p, (x, 0)); x += p.width + 6
        mont.save(out_png)
        metrics["montage_path"] = out_png
    return metrics
