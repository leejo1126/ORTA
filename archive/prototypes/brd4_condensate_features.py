"""
Brd4 condensate (nuclear puncta) feature extraction.

Pipeline (2D max-projection first pass):
  1. Restrict to nuclei using the DAPI Cellpose mask (upscaled to full xy).
  2. White top-hat to suppress the diffuse nucleoplasm, so detection does NOT
     depend on each nucleus' mean intensity (the weak point of a
     fold-over-mean threshold in densely-packed nuclei).
  3. Robust seeds: h-maxima on the top-hat image (prominence set from the noise
     MAD), which finds every peak that stands out by a height h -- so a merged
     condensate with several internal peaks yields several seeds.
  4. Watershed seeded by those maxima, masked by the top-hat threshold, to split
     touching / merged condensates.
  5. Per-condensate features (regionprops on raw intensity) + per-nucleus
     aggregates, including the partition coefficient and condensed fraction.

Run with the analysis venv:
    "EP-ORCA/.venv/Scripts/python.exe" brd4_condensate_features.py \
        "Z:/EPORCA/2026-04-16_IF/zscan_647_561_488_405_000.dax" \
        --mask "../output/masks_3d/zscan_647_561_488_405_000_c3_405_DAPI_masks3d.npz"
"""

from __future__ import annotations

import os
import time
import argparse

import numpy as np
import scipy.ndimage as ndi
from scipy.stats import median_abs_deviation
import tifffile
from PIL import Image

from skimage.morphology import white_tophat, disk, h_maxima
from skimage.segmentation import watershed, find_boundaries, relabel_sequential
from skimage.measure import regionprops, regionprops_table, label as sklabel

from dax_reader import read_dax_multichannel

PIXEL_SIZE_UM = 0.108  # full-res xy microns / pixel
Z_UM = 0.25            # z step (microns)
WAVELENGTHS = ["647", "561", "488", "405"]


def stretch_to_8bit(img, lo_pct=1, hi_pct=99.8):
    lo, hi = np.percentile(img, [lo_pct, hi_pct])
    if hi <= lo:
        hi = lo + 1
    return (np.clip((img.astype(np.float32) - lo) / (hi - lo), 0, 1) * 255).astype(np.uint8)


def load_nuclear_labels_2d(mask_npz, target_shape):
    """Load the scaled 3D DAPI mask, upscale xy to full res, project to 2D labels."""
    m = np.load(mask_npz)["masks"]                    # (z, y, x) at scaled res
    zoom = (1.0, target_shape[0] / m.shape[1], target_shape[1] / m.shape[2])
    full = ndi.zoom(m, zoom, order=0)                 # nearest -> keep label IDs
    return full.max(axis=0).astype(np.int32)          # (Y, X) 2D nuclear labels


def _robust_noise(th, nuc):
    """Top-hat noise scale, estimated from the *background* side of the in-nucleus
    distribution so the dense bright puncta don't inflate it (which would push the
    threshold up and drop dim puncta)."""
    vals = th[nuc]
    if vals.size == 0:
        return 1.0
    low = vals[vals <= np.median(vals)]               # exclude the bright tail
    mad = median_abs_deviation(low, scale="normal") if low.size else 0.0
    return mad if mad > 0 else max(median_abs_deviation(vals, scale="normal"), 1.0)


def _seed_and_watershed(th, nuc, mad, noise_k, seed_h_k, min_size):
    """Foreground = top-hat above noise_k*MAD; seeds = h-maxima with prominence
    seed_h_k*MAD (so merged condensates with multiple internal peaks get split);
    watershed assigns voxels to the nearest seed; objects below min_size voxels
    are dropped (removes over-split fragments) and labels relabelled 1..N."""
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
    return labels, thr


def detect_condensates(raw, nuc, tophat_radius, noise_k, seed_h_k, min_size, blur_sigma):
    """Return (labels, tophat, threshold) for condensates within the nuclei (2D).

    A small Gaussian is applied to the *detection* image only (smoother boundaries,
    fewer noise fragments); features are measured on the raw image by the caller."""
    th = white_tophat(raw, disk(tophat_radius))       # suppress diffuse background
    if blur_sigma > 0:
        th = ndi.gaussian_filter(th, blur_sigma)
    mad = _robust_noise(th, nuc)
    labels, thr = _seed_and_watershed(th, nuc, mad, noise_k, seed_h_k, min_size)
    return labels, th, thr


def extract_features(labels, raw, nuc_labels):
    """Per-condensate table + per-nucleus aggregates (incl. partition coeff)."""
    px_um2 = PIXEL_SIZE_UM ** 2
    if labels.max() == 0:
        return None, None

    t = regionprops_table(
        labels, intensity_image=raw,
        properties=("label", "area", "centroid", "weighted_centroid",
                    "mean_intensity", "max_intensity", "equivalent_diameter"),
    )
    cy = np.rint(t["centroid-0"]).astype(int)
    cx = np.rint(t["centroid-1"]).astype(int)
    nuc_id = nuc_labels[cy, cx]                        # which nucleus each spot is in

    per_spot = {
        "spot_label": t["label"],
        "nucleus": nuc_id,
        "area_um2": t["area"] * px_um2,
        "eq_diam_um": t["equivalent_diameter"] * PIXEL_SIZE_UM,
        "mean_intensity": t["mean_intensity"],
        "max_intensity": t["max_intensity"],
        "integrated_intensity": t["mean_intensity"] * t["area"],
        # intensity-weighted centre of mass (the key correlatable feature)
        "com_y_um": t["weighted_centroid-0"] * PIXEL_SIZE_UM,
        "com_x_um": t["weighted_centroid-1"] * PIXEL_SIZE_UM,
        "com_y_px": t["weighted_centroid-0"],
        "com_x_px": t["weighted_centroid-1"],
    }

    # Per-nucleus aggregates.
    cond_mask = labels > 0
    rows = []
    for nl in np.unique(nuc_labels):
        if nl == 0:
            continue
        in_nuc = nuc_labels == nl
        nuc_px = int(in_nuc.sum())
        cond_in = in_nuc & cond_mask
        nucleoplasm = in_nuc & ~cond_mask
        sel = nuc_id == nl
        n_cond = int(sel.sum())
        cond_int = float(raw[cond_in].sum())
        total_int = float(raw[in_nuc].sum())
        cond_mean = float(raw[cond_in].mean()) if cond_in.any() else 0.0
        nucpl_mean = float(raw[nucleoplasm].mean()) if nucleoplasm.any() else np.nan
        rows.append({
            "nucleus": int(nl),
            "nucleus_area_um2": nuc_px * px_um2,
            "n_condensates": n_cond,
            "density_per_um2": n_cond / (nuc_px * px_um2),
            "cond_area_frac": float(cond_in.sum()) / nuc_px,
            "condensed_fraction": cond_int / total_int if total_int else 0.0,
            "partition_coefficient": cond_mean / nucpl_mean if nucpl_mean else np.nan,
            "cond_mean_intensity": cond_mean,
            "nucleoplasm_mean_intensity": nucpl_mean,
        })
    return per_spot, rows


def expand_slices(slices, shape, pad):
    """Grow a tuple of slices by `pad` per axis, clipped to `shape`."""
    return tuple(slice(max(0, s.start - p), min(n, s.stop + p))
                 for s, p, n in zip(slices, pad, shape))


def load_nuclear_labels_3d(mask_npz, target_yx):
    """Load the scaled 3D DAPI mask and upscale xy to full res (z unchanged)."""
    m = np.load(mask_npz)["masks"]                    # (z, y, x) at scaled res
    zoom = (1.0, target_yx[0] / m.shape[1], target_yx[1] / m.shape[2])
    return ndi.zoom(m, zoom, order=0).astype(np.int32)


def detect_condensates_3d(raw, nuc, tophat_radius, noise_k, seed_h_k, min_size, blur_sigma):
    """3D detection: per-slice top-hat, optional xy Gaussian on the detection image,
    h-maxima seeds, 3D watershed. Features are measured on raw by the caller."""
    th = np.empty_like(raw)
    se = disk(tophat_radius)
    for z in range(raw.shape[0]):                      # top-hat per z-plane
        th[z] = white_tophat(raw[z], se)
    if blur_sigma > 0:
        th = ndi.gaussian_filter(th, (0, blur_sigma, blur_sigma))  # xy only
    mad = _robust_noise(th, nuc)
    labels, thr = _seed_and_watershed(th, nuc, mad, noise_k, seed_h_k, min_size)
    return labels, th, thr


def extract_features_3d(labels, raw, nuc_labels, voxel_um3):
    """Per-condensate table + per-nucleus aggregates in 3D."""
    if labels.max() == 0:
        return None, None
    t = regionprops_table(
        labels, intensity_image=raw,
        properties=("label", "area", "centroid", "weighted_centroid",
                    "mean_intensity", "max_intensity"),
    )
    zc = np.rint(t["centroid-0"]).astype(int)
    yc = np.rint(t["centroid-1"]).astype(int)
    xc = np.rint(t["centroid-2"]).astype(int)
    nuc_id = nuc_labels[zc, yc, xc]
    vol_um3 = t["area"] * voxel_um3
    per_spot = {
        "spot_label": t["label"],
        "nucleus": nuc_id,
        "volume_um3": vol_um3,
        "eq_diam_um": (6.0 * vol_um3 / np.pi) ** (1.0 / 3.0),  # sphere-equivalent
        "mean_intensity": t["mean_intensity"],
        "max_intensity": t["max_intensity"],
        "integrated_intensity": t["mean_intensity"] * t["area"],
        # intensity-weighted centre of mass (the key correlatable feature)
        "com_z_um": t["weighted_centroid-0"] * Z_UM,
        "com_y_um": t["weighted_centroid-1"] * PIXEL_SIZE_UM,
        "com_x_um": t["weighted_centroid-2"] * PIXEL_SIZE_UM,
        "com_z_px": t["weighted_centroid-0"],
        "com_y_px": t["weighted_centroid-1"],
        "com_x_px": t["weighted_centroid-2"],
    }

    cond_mask = labels > 0
    slices = ndi.find_objects(nuc_labels)
    rows = []
    for nl in np.unique(nuc_labels):
        if nl == 0:
            continue
        sl = slices[nl - 1]
        if sl is None:
            continue
        subn = nuc_labels[sl] == nl
        subr = raw[sl]
        subc = cond_mask[sl] & subn
        nucpl = subn & ~cond_mask[sl]
        nuc_vox = int(subn.sum())
        n_cond = int((nuc_id == nl).sum())
        cond_int = float(subr[subc].sum())
        total_int = float(subr[subn].sum())
        cond_mean = float(subr[subc].mean()) if subc.any() else 0.0
        nucpl_mean = float(subr[nucpl].mean()) if nucpl.any() else np.nan
        nuc_vol_um3 = nuc_vox * voxel_um3
        rows.append({
            "nucleus": int(nl),
            "nucleus_volume_um3": nuc_vol_um3,
            "n_condensates": n_cond,
            "density_per_um3": n_cond / nuc_vol_um3 if nuc_vol_um3 else 0.0,
            "cond_volume_frac": float(subc.sum()) / nuc_vox if nuc_vox else 0.0,
            "condensed_fraction": cond_int / total_int if total_int else 0.0,
            "partition_coefficient": cond_mean / nucpl_mean if nucpl_mean else np.nan,
            "cond_mean_intensity": cond_mean,
            "nucleoplasm_mean_intensity": nucpl_mean,
        })
    return per_spot, rows


def save_csv(path, colnames, columns):
    n = len(columns[colnames[0]])
    with open(path, "w") as fh:
        fh.write(",".join(colnames) + "\n")
        for i in range(n):
            fh.write(",".join(_fmt(columns[c][i]) for c in colnames) + "\n")


def save_dictrows_csv(path, rows):
    if not rows:
        open(path, "w").close()
        return
    cols = list(rows[0].keys())
    with open(path, "w") as fh:
        fh.write(",".join(cols) + "\n")
        for r in rows:
            fh.write(",".join(_fmt(r[c]) for c in cols) + "\n")


def _fmt(v):
    if isinstance(v, float):
        return f"{v:.4f}"
    return str(v)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dax_path")
    ap.add_argument("--mask", required=True, help="DAPI masks3d.npz (scaled)")
    ap.add_argument("--channel", type=int, default=0, help="Brd4 channel index")
    ap.add_argument("--mode", choices=["2d", "3d"], default="2d")
    ap.add_argument("--out", default=None)
    ap.add_argument("--trim-z", type=int, default=1)
    ap.add_argument("--tophat-radius", type=int, default=5)
    ap.add_argument("--noise-k", type=float, default=3.0,
                    help="foreground threshold = k * MAD of top-hat noise; "
                         "lower to include dimmer puncta")
    ap.add_argument("--seed-h-k", type=float, default=0.5,
                    help="h-maxima seed prominence = k * MAD; lower to split "
                         "merged condensates more aggressively")
    ap.add_argument("--min-size", type=int, default=10,
                    help="drop condensates smaller than this many voxels/pixels")
    ap.add_argument("--blur-sigma", type=float, default=0.3,
                    help="xy Gaussian sigma (px) on the detection image only, to "
                         "reduce patchy/pixelated boundaries; 0 disables. Features "
                         "(COM, intensities) always use the raw image.")
    ap.add_argument("--n-cells", type=int, default=None,
                    help="3D: process only N random nuclei (cropped per cell, "
                         "saving a raw+label TIFF pair each); fast + ImageJ-friendly")
    ap.add_argument("--seed", type=int, default=0, help="RNG seed for --n-cells")
    args = ap.parse_args()
    if args.n_cells:
        args.mode = "3d"  # per-cell analysis is inherently 3D

    if args.out is None:
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        args.out = os.path.join(root, "output", "condensates")
    os.makedirs(args.out, exist_ok=True)

    base = os.path.splitext(os.path.basename(args.dax_path))[0]
    wl = WAVELENGTHS[args.channel] if args.channel < len(WAVELENGTHS) else str(args.channel)
    prefix = os.path.join(args.out, f"{base}_c{args.channel}_{wl}_condensates_{args.mode}")

    timings = {}
    t = time.perf_counter()
    print(f"Reading channel c{args.channel} ({wl}) from {args.dax_path}  [mode={args.mode}]")
    vol, info = read_dax_multichannel(args.dax_path, len(WAVELENGTHS))
    ch = vol[:, args.channel]
    if args.trim_z > 0 and ch.shape[0] > 2 * args.trim_z:
        ch = ch[args.trim_z: ch.shape[0] - args.trim_z]

    # --- Per-cell mode: process N random nuclei in their own crops ---
    if args.n_cells:
        raw = np.asarray(ch, dtype=np.float32)                     # 3D volume
        nuc_labels = load_nuclear_labels_3d(args.mask, raw.shape[1:])
        labs = np.unique(nuc_labels); labs = labs[labs > 0]
        rng = np.random.default_rng(args.seed)
        sel = np.sort(rng.choice(labs, size=min(args.n_cells, len(labs)),
                                 replace=False))
        print(f"  Brd4 volume {raw.shape}; {len(labs)} nuclei -> "
              f"processing {len(sel)} random cells: {list(map(int, sel))}")
        timings["read+prep"] = time.perf_counter() - t; t = time.perf_counter()

        slices = ndi.find_objects(nuc_labels)
        voxel_um3 = PIXEL_SIZE_UM ** 2 * Z_UM
        cells_dir = prefix + "_cells"
        os.makedirs(cells_dir, exist_ok=True)
        all_spot, per_nuc, total = {}, [], 0
        for nl in sel:
            sl = expand_slices(slices[nl - 1], raw.shape, pad=(2, 15, 15))
            subraw = np.ascontiguousarray(raw[sl])
            subnuc = nuc_labels[sl] == nl
            labels_c, _, _ = detect_condensates_3d(
                subraw, subnuc, args.tophat_radius, args.noise_k, args.seed_h_k,
                args.min_size, args.blur_sigma)
            nlab = int(labels_c.max()); total += nlab
            nuc_img = subnuc.astype(np.int32) * int(nl)
            ps, pn = extract_features_3d(labels_c, subraw, nuc_img, voxel_um3)

            cp = os.path.join(cells_dir, f"cell{int(nl):04d}")
            tifffile.imwrite(cp + "_brd4_raw3d.tif",
                             subraw.astype(np.uint16), imagej=True)
            tifffile.imwrite(cp + "_labels.tif",
                             labels_c.astype(np.uint16), imagej=True)
            zmid = subraw.shape[0] // 2
            u8 = stretch_to_8bit(subraw[zmid])
            rgb = np.stack([u8] * 3, axis=-1)
            rgb[find_boundaries(subnuc[zmid], mode="outer")] = [180, 0, 0]
            rgb[find_boundaries(labels_c[zmid], mode="outer")] = [0, 255, 0]
            Image.fromarray(rgb).resize(
                (rgb.shape[1] * 3, rgb.shape[0] * 3), Image.NEAREST
            ).save(cp + "_midz_overlay.png")

            if ps is not None:
                # crop-local centres of mass -> full-image coordinates
                z0, y0, x0 = sl[0].start, sl[1].start, sl[2].start
                ps["com_z_px"] = ps["com_z_px"] + z0
                ps["com_y_px"] = ps["com_y_px"] + y0
                ps["com_x_px"] = ps["com_x_px"] + x0
                ps["com_z_um"] = ps["com_z_px"] * Z_UM
                ps["com_y_um"] = ps["com_y_px"] * PIXEL_SIZE_UM
                ps["com_x_um"] = ps["com_x_px"] * PIXEL_SIZE_UM
                for k, v in ps.items():
                    all_spot.setdefault(k, []).extend(list(v))
                per_nuc.extend(pn)
            print(f"  cell {int(nl):4d}: {nlab:4d} condensates  crop(z,y,x)={subraw.shape}")
        timings["detect+features+save"] = time.perf_counter() - t; t = time.perf_counter()

        if all_spot:
            save_csv(prefix + "_per_spot.csv", list(all_spot.keys()),
                     {k: np.asarray(v) for k, v in all_spot.items()})
        save_dictrows_csv(prefix + "_per_nucleus.csv", per_nuc)

        if per_nuc:
            nc = np.array([r["n_condensates"] for r in per_nuc])
            pc = np.array([r["partition_coefficient"] for r in per_nuc], dtype=float)
            cf = np.array([r["condensed_fraction"] for r in per_nuc], dtype=float)
            print(f"  total condensates: {total}  | per-cell median={np.median(nc):.0f} "
                  f"[{nc.min()}-{nc.max()}]")
            print(f"  partition_coefficient median={np.nanmedian(pc):.2f}  | "
                  f"condensed_fraction median={np.nanmedian(cf):.2f}")
        total_t = sum(timings.values())
        print("\n  --- timing ---")
        for k, v in timings.items():
            print(f"  {k:22s}: {v:6.1f}s")
        print(f"  {'TOTAL':22s}: {total_t:6.1f}s")
        print(f"\nPer-cell raw+label TIFF pairs in: {cells_dir}")
        return

    if args.mode == "2d":
        raw = np.asarray(ch.max(axis=0), dtype=np.float32)         # 2D max projection
        print(f"  Brd4 max-proj: {raw.shape}")
        nuc_labels = load_nuclear_labels_2d(args.mask, raw.shape)
        nuc = nuc_labels > 0
        print(f"  nuclei: {len(np.unique(nuc_labels)) - 1}")
        timings["read+prep"] = time.perf_counter() - t; t = time.perf_counter()
        labels, th, thr = detect_condensates(raw, nuc, args.tophat_radius,
                                             args.noise_k, args.seed_h_k,
                                             args.min_size, args.blur_sigma)
        timings["detect"] = time.perf_counter() - t; t = time.perf_counter()
        per_spot, per_nuc = extract_features(labels, raw, nuc_labels)
        timings["features"] = time.perf_counter() - t; t = time.perf_counter()
    else:
        raw = np.asarray(ch, dtype=np.float32)                     # 3D volume (z,y,x)
        print(f"  Brd4 volume: {raw.shape}")
        nuc_labels = load_nuclear_labels_3d(args.mask, raw.shape[1:])
        nuc = nuc_labels > 0
        print(f"  nuclei: {len(np.unique(nuc_labels)) - 1}")
        timings["read+prep"] = time.perf_counter() - t; t = time.perf_counter()
        labels, th, thr = detect_condensates_3d(raw, nuc, args.tophat_radius,
                                                args.noise_k, args.seed_h_k,
                                                args.min_size, args.blur_sigma)
        timings["detect"] = time.perf_counter() - t; t = time.perf_counter()
        voxel_um3 = PIXEL_SIZE_UM ** 2 * Z_UM
        per_spot, per_nuc = extract_features_3d(labels, raw, nuc_labels, voxel_um3)
        timings["features"] = time.perf_counter() - t; t = time.perf_counter()

    n_cond = int(labels.max())
    print(f"  top-hat radius={args.tophat_radius}px  noise_k={args.noise_k}  "
          f"threshold={thr:.1f}  -> {n_cond} condensates")

    # --- Save label image (each condensate a unique value) ---
    # ImageJ TIFF supports only uint8/uint16/float32, so for >65535 labels write a
    # standard (non-ImageJ) multipage uint32 TIFF, which Fiji still opens as a stack.
    if n_cond <= 65535:
        tifffile.imwrite(prefix + "_labels.tif", labels.astype(np.uint16), imagej=True)
    else:
        tifffile.imwrite(prefix + "_labels.tif", labels.astype(np.uint32))
    if per_spot is not None:
        save_csv(prefix + "_per_spot.csv", list(per_spot.keys()), per_spot)
        save_dictrows_csv(prefix + "_per_nucleus.csv", per_nuc)

    if args.mode == "3d":
        # Save the matching (trimmed) raw Brd4 stack so the labels overlay 1:1.
        tifffile.imwrite(prefix + "_brd4_raw3d.tif",
                         np.asarray(ch, dtype=np.uint16), imagej=True)
        # Mid-z overlay for a quick look.
        zmid = raw.shape[0] // 2
        u8 = stretch_to_8bit(raw[zmid])
        rgb = np.stack([u8] * 3, axis=-1)
        rgb[find_boundaries(nuc_labels[zmid], mode="outer")] = [180, 0, 0]
        rgb[find_boundaries(labels[zmid], mode="outer")] = [0, 255, 0]
        Image.fromarray(rgb).save(prefix + "_midz_overlay.png")
    else:
        u8 = stretch_to_8bit(raw)
        rgb = np.stack([u8] * 3, axis=-1)
        rgb[find_boundaries(nuc_labels, mode="outer")] = [180, 0, 0]
        rgb[find_boundaries(labels, mode="outer")] = [0, 255, 0]
        Image.fromarray(rgb).save(prefix + "_overlay.png")
        if per_nuc:
            busiest = max(per_nuc, key=lambda r: r["n_condensates"])["nucleus"]
            ys, xs = np.where(nuc_labels == busiest)
            pad = 15
            crop = rgb[max(0, ys.min() - pad):ys.max() + pad,
                       max(0, xs.min() - pad):xs.max() + pad]
            Image.fromarray(crop).resize(
                (crop.shape[1] * 3, crop.shape[0] * 3), Image.NEAREST
            ).save(prefix + "_zoom.png")

    if per_nuc:
        nc = np.array([r["n_condensates"] for r in per_nuc])
        pc = np.array([r["partition_coefficient"] for r in per_nuc], dtype=float)
        cf = np.array([r["condensed_fraction"] for r in per_nuc], dtype=float)
        print(f"  per-nucleus n_condensates : median={np.median(nc):.0f} "
              f"[{nc.min()}-{nc.max()}]")
        print(f"  partition_coefficient     : median={np.nanmedian(pc):.2f}")
        print(f"  condensed_fraction        : median={np.nanmedian(cf):.2f}")

    timings["save+overlay"] = time.perf_counter() - t
    total = sum(timings.values())
    print("\n  --- timing ---")
    for k, v in timings.items():
        print(f"  {k:14s}: {v:6.1f}s")
    print(f"  {'TOTAL':14s}: {total:6.1f}s")
    print(f"\nOutputs in: {args.out}")


if __name__ == "__main__":
    main()
