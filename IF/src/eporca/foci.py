"""
Step 2: per-channel 3D foci / condensate detection.

Generalizes the tuned Brd4 pipeline to any channel via per-marker parameters
(config ``foci.per_marker``):

    per-slice white top-hat  ->  optional xy Gaussian on the DETECTION image only
    ->  h-maxima seeds  ->  3D watershed  ->  min-size filter

Detection is done **per nucleus** (cropping each nucleus from the upscaled DAPI
mask), which is what we validated during tuning and is far faster than running
the morphological ops over the whole field. All features (intensity-weighted
centre of mass, intensities, volume) are measured on the RAW data.

Writes one per-spot CSV per FOV x channel; the full-res label volume is only
written when ``save_labels=True`` (large; for QC).

Marker presets: Brd4/Pol2 = puncta (tuned defaults); Sc35 = speckles (larger,
less split); DAPI = chromocenters (large, bright, strict). See config.
"""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor

import numpy as np
import scipy.ndimage as ndi
from scipy.stats import median_abs_deviation
from skimage.morphology import white_tophat, disk, h_maxima
from skimage.segmentation import watershed, relabel_sequential
from skimage.measure import regionprops_table, label as sklabel

from .config import Config
from .io_zarr import read_channel


# --------------------------------------------------------------------- detection
def _robust_noise(th, nuc):
    """Top-hat noise scale from the background side of the in-nucleus distribution
    (so dense bright foci don't inflate it)."""
    vals = th[nuc]
    if vals.size == 0:
        return 1.0
    low = vals[vals <= np.median(vals)]
    mad = median_abs_deviation(low, scale="normal") if low.size else 0.0
    return mad if mad > 0 else max(median_abs_deviation(vals, scale="normal"), 1.0)


def _seed_and_watershed(th, nuc, mad, noise_k, seed_h_k, min_size):
    thr = noise_k * mad
    binary = (th > thr) & nuc
    th_in = np.where(nuc, th, 0.0)
    seeds = (h_maxima(th_in, max(seed_h_k * mad, 1e-6)) > 0) & binary
    markers = sklabel(seeds)
    labels = watershed(-th, markers, mask=binary)
    if min_size and min_size > 1:
        counts = np.bincount(labels.ravel())
        small = np.flatnonzero(counts < min_size)
        small = small[small != 0]
        if small.size:
            labels[np.isin(labels, small)] = 0
        labels, _, _ = relabel_sequential(labels)
    return labels


def detect_foci_3d(raw, nuc, params) -> np.ndarray:
    """MAD mode: top-hat + h-maxima + watershed (dense/space-filling markers)."""
    th = np.empty_like(raw, dtype=np.float32)
    se = disk(params.tophat_radius)
    for z in range(raw.shape[0]):
        th[z] = white_tophat(raw[z], se)
    if params.blur_sigma > 0:
        th = ndi.gaussian_filter(th, (0, params.blur_sigma, params.blur_sigma))
    mad = _robust_noise(th, nuc)
    return _seed_and_watershed(th, nuc, mad, params.noise_k, params.seed_h_k,
                               params.min_size)


def _size_filter(labels, min_size, max_size):
    """Drop labels with voxel count < min_size or > max_size; relabel 1..N."""
    counts = np.bincount(labels.ravel())
    bad = np.zeros(counts.shape[0], dtype=bool)
    if min_size:
        bad |= counts < min_size
    if max_size:
        bad |= counts > max_size
    bad[0] = False
    drop = np.flatnonzero(bad)
    if drop.size:
        labels[np.isin(labels, drop)] = 0
    labels, _, _ = relabel_sequential(labels)
    return labels


def detect_foci_meanfold(raw, nuc, params) -> np.ndarray:
    """mean_fold mode (MATLAB findDensities port): foreground = signal above
    threshold x mean(in-nucleus MIP) and an absolute floor; optional intensity
    watershed to split touching bodies; size-gated. ``raw`` is background-subtracted
    by the caller. Good for sparse markers (Pol2/Sc35/DAPI)."""
    img = raw
    if params.blur_sigma > 0:
        img = ndi.gaussian_filter(img, (0, params.blur_sigma, params.blur_sigma))
    mip = img.max(axis=0)
    nuc2d = nuc.any(axis=0)
    vals = mip[nuc2d & (mip > 0)]
    if vals.size == 0:
        return np.zeros(raw.shape, dtype=np.int32)
    thr = params.threshold * float(vals.mean())
    binary = (img > thr) & (img > params.abs_floor) & nuc
    if not binary.any():
        return np.zeros(raw.shape, dtype=np.int32)

    if params.watershed:
        seeds = h_maxima(np.where(binary, img, 0.0), max(params.marker_h, 1e-6)) > 0
        markers = sklabel(seeds)
        labels = (watershed(-img, markers, mask=binary) if markers.max() > 0
                  else sklabel(binary, connectivity=1))
    else:
        labels = sklabel(binary, connectivity=1)
    return _size_filter(labels.astype(np.int32), params.min_size, params.max_size)


def detect_foci(raw, nuc, params) -> np.ndarray:
    """Dispatch to the detector for this marker's mode."""
    if params.mode == "mean_fold":
        return detect_foci_meanfold(raw, nuc, params)
    return detect_foci_3d(raw, nuc, params)


def subtract_background(arr, bgcfg) -> np.ndarray:
    """Subtract per-channel background (camera offset + diffuse) and clip at 0."""
    if bgcfg.mode == "none":
        return arr
    bg = bgcfg.value if bgcfg.mode == "constant" else np.percentile(arr, bgcfg.percentile)
    out = arr - bg
    np.clip(out, 0, None, out=out)
    return out


# ----------------------------------------------------------------- nucleus masks
def _coerce_shape(arr, target):
    if arr.shape == target:
        return arr
    out = np.zeros(target, dtype=arr.dtype)
    sl = tuple(slice(0, min(a, b)) for a, b in zip(arr.shape, target))
    out[sl] = arr[sl]
    return out


def load_nuclear_labels_3d(cfg: Config, fov: int, target_zyx) -> np.ndarray:
    """Read the scaled DAPI mask and upscale xy to full res (z unchanged)."""
    import zarr
    root = zarr.open_group(cfg.mask_path(fov), mode="r")
    m = np.asarray(root["0"])                              # (z, y', x') scaled
    full_yx = root.attrs["full_yx"]
    zoom = (1.0, full_yx[0] / m.shape[1], full_yx[1] / m.shape[2])
    up = ndi.zoom(m, zoom, order=0).astype(np.int32)
    return _coerce_shape(up, target_zyx)


def _expand_slices(slices, shape, pad):
    return tuple(slice(max(0, s.start - p), min(n, s.stop + p))
                 for s, p, n in zip(slices, pad, shape))


# --------------------------------------------------------------------- per-spot
_SPOT_COLS = [
    "fov", "marker", "condition", "spot_label", "nucleus", "volume_um3",
    "eq_diam_um", "mean_intensity", "max_intensity", "integrated_intensity",
    "com_z_um", "com_y_um", "com_x_um", "com_z_px", "com_y_px", "com_x_px",
]


def _spots_from_labels(lab, subraw, voxel_um3, z_um, px, marker, fov, cond,
                       nucleus, origin, base_label):
    """Per-spot features for one nucleus crop, with COMs in full-FOV coordinates."""
    t = regionprops_table(
        lab, intensity_image=subraw,
        properties=("label", "area", "weighted_centroid", "mean_intensity",
                    "max_intensity"),
    )
    n = len(t["label"])
    if n == 0:
        return None
    z0, y0, x0 = origin
    cz = t["weighted_centroid-0"] + z0
    cy = t["weighted_centroid-1"] + y0
    cx = t["weighted_centroid-2"] + x0
    vol_um3 = t["area"] * voxel_um3
    return {
        "fov": np.full(n, fov),
        "marker": np.array([marker] * n, dtype=object),
        "condition": np.array([cond] * n, dtype=object),
        "spot_label": t["label"].astype(np.int64) + base_label,
        "nucleus": np.full(n, nucleus),
        "volume_um3": vol_um3,
        "eq_diam_um": (6.0 * vol_um3 / np.pi) ** (1.0 / 3.0),
        "mean_intensity": t["mean_intensity"],
        "max_intensity": t["max_intensity"],
        "integrated_intensity": t["mean_intensity"] * t["area"],
        "com_z_um": cz * z_um, "com_y_um": cy * px, "com_x_um": cx * px,
        "com_z_px": cz, "com_y_px": cy, "com_x_px": cx,
    }


def _process_nucleus(payload):
    """Pool worker: detect foci in one nucleus crop. Returns the per-spot table
    (local labels), plus the label crop + origin so the parent can paint the full
    label volume with IDs that match spot_label. Receives only the small crop, so
    inter-process transfer is cheap."""
    lab = detect_foci(payload["subraw"], payload["subnuc"], payload["params"])
    if int(lab.max()) == 0:
        return None
    spots = _spots_from_labels(
        lab, payload["subraw"], payload["voxel_um3"], payload["z_um"], payload["px"],
        payload["marker"], payload["fov"], payload["cond"], payload["nucleus"],
        payload["origin"], 0,
    )
    return {"spots": spots, "lab": lab.astype(np.uint32) if payload["return_labels"] else None,
            "origin": payload["origin"]}


def _concat(tables):
    tables = [t for t in tables if t is not None]
    if not tables:
        return {k: np.array([]) for k in _SPOT_COLS}
    return {k: np.concatenate([t[k] for t in tables]) for k in _SPOT_COLS}


def _save_spot_csv(path, table):
    n = len(table["spot_label"])
    with open(path, "w") as fh:
        fh.write(",".join(_SPOT_COLS) + "\n")
        for i in range(n):
            row = []
            for c in _SPOT_COLS:
                v = table[c][i]
                row.append(v if isinstance(v, str) else
                           (f"{v:.4f}" if isinstance(v, (float, np.floating)) else str(v)))
            fh.write(",".join(row) + "\n")


def _save_label_zarr(path, labels):
    import zarr
    import numcodecs
    dtype = np.uint16 if labels.max() <= 65535 else np.uint32
    root = zarr.open_group(path, mode="w")
    root.create_dataset("0", data=labels.astype(dtype),
                        chunks=(min(8, labels.shape[0]), 512, 512),
                        compressor=numcodecs.Blosc("zstd", clevel=5), overwrite=True)


def _assemble(results, shape, save_labels):
    """Renumber per-nucleus spot tables globally and (optionally) paint the full
    label volume with the SAME ids, so label values join the per_spot table by
    spot_label. Returns (table, full_lab_or_None)."""
    tables, base = [], 0
    full_lab = np.zeros(shape, np.uint32) if save_labels else None
    for r in results:
        if r is None:
            continue
        t = dict(r["spots"])
        k = len(t["spot_label"])
        if k == 0:
            continue
        t["spot_label"] = t["spot_label"] + base
        tables.append(t)
        if save_labels and r["lab"] is not None:
            lab, o = r["lab"], r["origin"]
            sl = (slice(o[0], o[0] + lab.shape[0]), slice(o[1], o[1] + lab.shape[1]),
                  slice(o[2], o[2] + lab.shape[2]))
            m = lab > 0
            full_lab[sl][m] = lab[m] + base
        base += k
    return _concat(tables), full_lab


def foci_fov(cfg: Config, fov: int, markers=None, save_labels: bool | None = None,
             workers: int | None = None) -> dict:
    """Detect foci per nucleus for the requested markers in one FOV. Writes a
    per-spot CSV and (if save_labels) a compressed label volume per channel whose
    voxel IDs join the CSV by spot_label -- the per-focus geometry used for
    cross-focus / DNA-locus analysis.

    ``workers`` (default config foci.workers) sets nucleus-level parallelism within
    the FOV (for testing); the batch keeps workers=1 and parallelizes across FOVs.
    """
    workers = cfg.foci.workers if workers is None else workers
    save_labels = cfg.foci.save_labels if save_labels is None else save_labels
    markers = markers or cfg.markers
    ref = read_channel(cfg, fov, markers[0], trim=True)
    nuc_labels = load_nuclear_labels_3d(cfg, fov, ref.shape)
    slices = ndi.find_objects(nuc_labels)
    present = [i + 1 for i, s in enumerate(slices) if s is not None]

    px = cfg.acquisition.pixel_size_um
    z_um = cfg.acquisition.z_um
    voxel_um3 = px * px * z_um
    cond = cfg.condition_for_fov(fov) or "unassigned"

    summary = {}
    for marker in markers:
        raw_full = read_channel(cfg, fov, marker, trim=True).astype(np.float32)
        raw_full = subtract_background(raw_full, cfg.foci.background)
        params = cfg.foci_params(marker)

        payloads = []
        for L in present:
            sl = _expand_slices(slices[L - 1], raw_full.shape, (1, 8, 8))
            subnuc = nuc_labels[sl] == L
            if not subnuc.any():
                continue
            payloads.append({
                "subraw": np.ascontiguousarray(raw_full[sl]),
                "subnuc": subnuc, "params": params, "marker": marker, "fov": fov,
                "cond": cond, "nucleus": L,
                "origin": (sl[0].start, sl[1].start, sl[2].start),
                "voxel_um3": voxel_um3, "z_um": z_um, "px": px,
                "return_labels": save_labels,
            })
        if workers and workers > 1:
            with ProcessPoolExecutor(max_workers=workers) as ex:
                results = list(ex.map(_process_nucleus, payloads, chunksize=2))
        else:
            results = [_process_nucleus(p) for p in payloads]

        table, full_lab = _assemble(results, raw_full.shape, save_labels)
        _save_spot_csv(cfg.foci_spot_csv(fov, marker), table)
        if save_labels:
            _save_label_zarr(cfg.foci_label_path(fov, marker), full_lab)
        summary[marker] = int(len(table["spot_label"]))
    return {"fov": fov, "n_foci": summary}
