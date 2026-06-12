"""
Detector primitives for the autofoci spec DSL. Six families, each a pure function
``detect_<family>(img, nuc, p) -> int label volume`` on a cropped nucleus. ``img`` is
background-subtracted float (z,y,x); ``nuc`` is the boolean mask; ``p`` is a validated,
defaulted param dict (see ``spec.PARAM_SPACE``).

mean_fold / mad_tophat delegate to the production detectors in ``eporca.foci`` so the
search's reproduction of the current pipeline is exact. The other four wrap standard
skimage/scipy ops (no new dependency); the wavelet family is an à-trous multiscale-product
detector implemented from separable convolutions.
"""

from __future__ import annotations

import numpy as np
import scipy.ndimage as ndi
from scipy.stats import median_abs_deviation
from skimage.feature import blob_log, blob_dog, peak_local_max
from skimage.morphology import h_maxima
from skimage.segmentation import watershed
from skimage.measure import label as sklabel
from skimage.filters import threshold_otsu, threshold_local

from ..config import FociParams
from ..foci import detect_foci_meanfold, detect_foci_3d, _size_filter


# ------------------------------------------------------------------------ helpers
def _empty(img):
    return np.zeros(img.shape, dtype=np.int32)


def _norm(img, nuc):
    """Scale in-nucleus intensities to ~[0,1] (by the 99.9th pct) so blob/h-dome/wavelet
    thresholds are intensity-scale-stable across cells and markers."""
    v = img[nuc]
    hi = float(np.percentile(v, 99.9)) if v.size else 1.0
    return np.clip(img / (hi if hi > 0 else 1.0), 0, 1).astype(np.float32)


def _floor_mask(img, nuc, pct):
    """Foreground mask bounding region growth: in-nucleus and above an intensity percentile."""
    floor = float(np.percentile(img[nuc], pct)) if nuc.any() else 0.0
    return nuc & (img > floor)


def _label_from_seeds(markers, intensity, mask, do_ws):
    if do_ws and markers.max() > 0:
        return watershed(-intensity, markers, mask=mask)
    return sklabel(mask, connectivity=1)


# ---------------------------------------------------------- families (delegating two)
def detect_mean_fold(img, nuc, p):
    fp = FociParams(mode="mean_fold", threshold=p["threshold"], abs_floor=p["abs_floor"],
                    blur_sigma=p["blur_sigma"], marker_h=p["marker_h"],
                    watershed=p["watershed"], min_size=p["min_size"],
                    max_size=p.get("max_size"))
    return detect_foci_meanfold(img, nuc, fp)


def detect_mad_tophat(img, nuc, p):
    fp = FociParams(mode="mad", tophat_radius=p["tophat_radius"], noise_k=p["noise_k"],
                    seed_h_k=p["seed_h_k"], blur_sigma=p["blur_sigma"],
                    min_size=p["min_size"])
    return detect_foci_3d(img, nuc, fp)


# ------------------------------------------------------------- families (new four)
def detect_log_dog(img, nuc, p):
    imn = np.where(nuc, _norm(img, nuc), 0.0)
    if p["variant"] == "log":
        blobs = blob_log(imn, min_sigma=p["min_sigma"], max_sigma=p["max_sigma"],
                         num_sigma=int(p["num_sigma"]), threshold=p["threshold"])
    else:
        blobs = blob_dog(imn, min_sigma=p["min_sigma"], max_sigma=p["max_sigma"],
                         threshold=p["threshold"])
    if len(blobs) == 0:
        return _empty(img)
    mask = _floor_mask(img, nuc, p["fg_floor_pct"])
    markers = _empty(img)
    for i, b in enumerate(blobs, start=1):
        z, y, x = int(b[0]), int(b[1]), int(b[2])
        if mask[z, y, x]:
            markers[z, y, x] = i
    if markers.max() == 0:
        return _empty(img)
    lab = watershed(-img, markers, mask=mask)
    return _size_filter(lab.astype(np.int32), p["min_size"], None)


def detect_h_dome(img, nuc, p):
    imn = np.where(nuc, _norm(img, nuc), 0.0)
    domes = h_maxima(imn, max(p["h"], 1e-6)) > 0
    if not domes.any():
        return _empty(img)
    peaks = peak_local_max(imn, min_distance=int(p["min_distance"]),
                           labels=domes.astype(np.int32))
    mask = _floor_mask(img, nuc, p["fg_floor_pct"])
    markers = _empty(img)
    for i, c in enumerate(peaks, start=1):
        z, y, x = int(c[0]), int(c[1]), int(c[2])
        if mask[z, y, x]:
            markers[z, y, x] = i
    lab = _label_from_seeds(markers, img, mask, p["watershed"])
    return _size_filter(lab.astype(np.int32), p["min_size"], None)


def detect_otsu_adaptive(img, nuc, p):
    vals = img[nuc]
    if vals.size == 0 or float(vals.max()) <= float(vals.min()):
        return _empty(img)
    if p["method"] == "otsu":
        thr = threshold_otsu(vals)
        binary = (img > thr) & nuc
    else:
        bs = int(p["block_size"]); bs += (bs % 2 == 0)        # must be odd
        noise = float(vals.std()) or 1.0
        binary = np.zeros(img.shape, bool)
        for z in range(img.shape[0]):
            if not nuc[z].any():
                continue
            loc = threshold_local(img[z], block_size=bs)
            binary[z] = (img[z] > loc + p["offset_k"] * noise) & nuc[z]
    if not binary.any():
        return _empty(img)
    if p["watershed"]:
        seeds = h_maxima(np.where(binary, img, 0.0), max(p["marker_h"], 1e-6)) > 0
        markers = sklabel(seeds)
        lab = (watershed(-img, markers, mask=binary) if markers.max() > 0
               else sklabel(binary, connectivity=1))
    else:
        lab = sklabel(binary, connectivity=1)
    return _size_filter(lab.astype(np.int32), p["min_size"], None)


def _atrous_details(plane, n_levels):
    """À-trous (stationary) wavelet detail planes 1..n_levels via a dilated B3-spline."""
    taps = np.array([1, 4, 6, 4, 1], dtype=np.float32) / 16.0
    cur = plane.astype(np.float32)
    details = []
    for lvl in range(n_levels):
        step = 2 ** lvl
        w = np.zeros(4 * step + 1, dtype=np.float32)
        for t, off in zip(taps, (-2, -1, 0, 1, 2)):
            w[2 * step + off * step] = t
        sm = ndi.convolve1d(cur, w, axis=0, mode="reflect")
        sm = ndi.convolve1d(sm, w, axis=1, mode="reflect")
        details.append(cur - sm)
        cur = sm
    return details


def detect_wavelet(img, nuc, p):
    lo, hi = (int(x) for x in p["levels"].split("-"))
    binary = np.zeros(img.shape, bool)
    for z in range(img.shape[0]):
        if not nuc[z].any():
            continue
        details = _atrous_details(img[z], hi)
        sel = [np.clip(details[i - 1], 0, None) for i in range(lo, hi + 1)]
        prod = np.prod(sel, axis=0)
        v = prod[nuc[z]]
        pos = v[v > 0]
        if pos.size == 0:
            continue
        mad = median_abs_deviation(pos, scale="normal")
        thr = p["k"] * (mad if mad > 0 else float(pos.std()) + 1e-9)
        binary[z] = (prod > thr) & nuc[z]
    if not binary.any():
        return _empty(img)
    if p["watershed"]:
        peaks = peak_local_max(np.where(binary, img, 0.0), min_distance=2,
                               labels=binary.astype(np.int32))
        markers = _empty(img)
        for i, c in enumerate(peaks, start=1):
            markers[int(c[0]), int(c[1]), int(c[2])] = i
        lab = (watershed(-img, markers, mask=binary) if markers.max() > 0
               else sklabel(binary, connectivity=1))
    else:
        lab = sklabel(binary, connectivity=1)
    return _size_filter(lab.astype(np.int32), p["min_size"], None)
