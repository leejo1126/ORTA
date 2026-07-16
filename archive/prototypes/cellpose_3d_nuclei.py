"""
3D nuclear segmentation of a 4-channel .dax with Cellpose-SAM, run per channel
so we can compare which channel segments nuclei best.

Modeled on the lab's 2D DAPI workflow
(sample script/2027-07-19_cellpose_dapi_Masks_for_ep_orca.py), which comes from
the same Pol2/Brd4/Sc35 IF assay, so its calibration is reused:
    pixelSize = 0.108 um/px, expected nuclear diameter diam_um = 15 um.

Key ideas carried over from the sample:
  * Resize image so nuclei are ~30 px (Cellpose's trained size):
        pxScale = pixelSize * 30 / diam_um
  * Replace pure-black (0) pixels with the 1% intensity quantile.
  * Optional gaussian blur.
  * Evaluate with diameter=30, flow_threshold=0.4, cellprob_threshold=0.0.
  * Exclude masks touching the (xy) image border.

Differences here:
  * 3D: de-interleave the .dax into (z, channel, y, x), run do_3D on each channel.
  * Downsample only in xy (keep z); pass anisotropy = z_um / new_xy_um so Cellpose
    handles the z scaling.
  * Run for any subset of the 4 channels and report nuclei counts for comparison.

Run with the cellpose-gpu env, e.g.:
    C:\\ProgramData\\Anaconda3\\envs\\cellpose-gpu\\python.exe cellpose_3d_nuclei.py \\
        "Z:\\EPORCA\\2026-04-16_IF\\zscan_647_561_488_405_000.dax" --channels 3
"""

from __future__ import annotations

import os
import sys
import time
import argparse

import numpy as np
import scipy.ndimage
import tifffile
from PIL import Image
from skimage.measure import regionprops

from cellpose import models, utils
import cellpose.dynamics as _cpdyn

from dax_reader import read_dax_multichannel


def _patch_get_masks_torch_for_old_torch():
    """torch<2 only allows int64/bool tensors as indices, but cellpose 4.0.5
    casts pixel coordinates to int32 (torch.int) before using them to index in
    get_masks_torch -> IndexError. Cast those indices to long first. Newer torch
    accepts int32 indexing, so this shim is a harmless no-op there."""
    import torch
    if int(torch.__version__.split(".")[0]) >= 2:
        return
    _orig = _cpdyn.get_masks_torch

    def _patched(pt, *args, **kwargs):
        return _orig(pt.long(), *args, **kwargs)

    _cpdyn.get_masks_torch = _patched


_patch_get_masks_torch_for_old_torch()

# --- Acquisition / assay parameters (from the matching IF assay + .xml) ---
WAVELENGTHS = ["647", "561", "488", "405"]          # channel order in the .dax
MARKERS = {"647": "Brd4", "561": "Pol2", "488": "Sc35", "405": "DAPI"}
PIXEL_SIZE_UM = 0.108     # xy microns / pixel
Z_UM = 0.25               # z step (from xml software_z_scan step_size = 250 nm)
DIAM_UM = 15.0            # expected nuclear diameter (from sample script)
CELLPOSE_DIAM_PX = 30     # size Cellpose is trained for

# --- Segmentation parameters (from sample) ---
FLOW_THRESHOLD = 0.4
CELLPROB_THRESHOLD = 0.0
BLUR_FACTOR = 1.0         # gaussian sigma in xy after rescale; 0 to disable


def stretch_to_8bit(img, low_pct=0.5, high_pct=99.5):
    lo, hi = np.percentile(img, [low_pct, high_pct])
    if hi <= lo:
        hi = lo + 1
    scaled = np.clip((img.astype(np.float32) - lo) / (hi - lo), 0, 1)
    return (scaled * 255).astype(np.uint8)


def overlay_outlines(img2d_u8, mask2d, removed=None):
    """Grayscale slice with mask outlines: kept nuclei red, excluded blue."""
    rgb = np.stack([img2d_u8] * 3, axis=-1)
    outlines = utils.masks_to_outlines(mask2d)
    if removed:
        rem = np.isin(mask2d, np.asarray(list(removed), dtype=mask2d.dtype))
    else:
        rem = np.zeros_like(mask2d, dtype=bool)
    rgb[outlines & ~rem] = [255, 0, 0]
    rgb[outlines & rem] = [0, 128, 255]
    return rgb


def nucleus_metrics(masks, voxel_um3, args):
    """Per-nucleus volume (um^3) and xy-footprint circularity, with a keep/exclude
    decision from the size & circularity thresholds in args. Does NOT modify masks.

    Circularity = 4*pi*area / perimeter^2 of the nucleus' xy max-projection
    footprint (1.0 = perfect disk; lower = elongated/lobed). Computed on each
    nucleus' isolated crop so overlapping neighbours don't interfere.

    Returns (metrics_list, removed_set).
    """
    counts = np.bincount(masks.ravel())
    labels = np.nonzero(counts)[0]
    labels = labels[labels != 0]
    slices = scipy.ndimage.find_objects(masks)

    metrics, removed = [], set()
    for L in labels:
        sl = slices[L - 1]
        if sl is None:
            continue
        sub = masks[sl] == L
        vol_vox = int(counts[L])
        vol_um3 = vol_vox * voxel_um3

        foot = sub.any(axis=0).astype(np.uint8)   # xy footprint
        props = regionprops(foot)
        if props and props[0].perimeter > 0:
            area, perim = props[0].area, props[0].perimeter
            circ = float(4.0 * np.pi * area / (perim * perim))
        else:
            circ = 0.0

        keep = True
        if args.min_volume_um3 is not None and vol_um3 < args.min_volume_um3:
            keep = False
        if args.max_volume_um3 is not None and vol_um3 > args.max_volume_um3:
            keep = False
        if args.min_circularity is not None and circ < args.min_circularity:
            keep = False
        if args.max_circularity is not None and circ > args.max_circularity:
            keep = False

        metrics.append({"label": int(L), "volume_vox": vol_vox,
                        "volume_um3": round(vol_um3, 3),
                        "circularity": round(circ, 4), "kept": int(keep)})
        if not keep:
            removed.add(int(L))
    return metrics, removed


def save_metrics_csv(path, metrics):
    with open(path, "w") as fh:
        fh.write("label,volume_vox,volume_um3,circularity,kept\n")
        for m in metrics:
            fh.write(f"{m['label']},{m['volume_vox']},{m['volume_um3']},"
                     f"{m['circularity']},{m['kept']}\n")


def print_metric_summary(metrics, args):
    if not metrics:
        print("  (no nuclei to summarize)")
        return
    vols = np.array([m["volume_um3"] for m in metrics])
    circ = np.array([m["circularity"] for m in metrics])

    def pct(a):
        return " ".join(f"p{p}={np.percentile(a, p):.2f}" for p in (5, 25, 50, 75, 95))

    print(f"  volume_um3 : {pct(vols)}")
    print(f"  circularity: {pct(circ)}")
    if any(v is not None for v in (args.min_volume_um3, args.max_volume_um3,
                                   args.min_circularity, args.max_circularity)):
        print(f"  filters    : vol_um3 in [{args.min_volume_um3}, {args.max_volume_um3}], "
              f"circularity in [{args.min_circularity}, {args.max_circularity}]")


def segment_channel(vol_zyx, out_dir, base, wl, model, args):
    """Segment one channel volume (z, y, x) in 3D and save results."""
    marker = MARKERS.get(wl, wl)
    tag = f"c{args._ch_index} {wl} {marker}"
    print(f"\n=== {tag} ===")

    img = vol_zyx.astype(np.float32)
    print(f"  original volume (z,y,x): {img.shape}")

    # Cellpose dislikes pure-black pixels: replace 0s with the 1% quantile.
    if np.any(img == 0):
        low_val = np.quantile(img[img > 0], 0.01)
        img[img == 0] = low_val

    # Resize xy so nuclei ~30 px; keep z. Cellpose handles z via anisotropy.
    pxScale = PIXEL_SIZE_UM * CELLPOSE_DIAM_PX / DIAM_UM
    new_xy_um = PIXEL_SIZE_UM / pxScale
    anisotropy = Z_UM / new_xy_um
    img_scaled = scipy.ndimage.zoom(img, (1.0, pxScale, pxScale), order=1)
    print(f"  pxScale={pxScale:.4f}  scaled (z,y,x)={img_scaled.shape}  "
          f"new_xy={new_xy_um:.3f}um  anisotropy={anisotropy:.3f}")

    if BLUR_FACTOR > 0:
        img_scaled = scipy.ndimage.gaussian_filter(img_scaled, (0, BLUR_FACTOR, BLUR_FACTOR))

    t0 = time.time()
    masks, flows, styles = model.eval(
        img_scaled,
        diameter=CELLPOSE_DIAM_PX,
        do_3D=True,
        anisotropy=anisotropy,
        flow_threshold=FLOW_THRESHOLD,
        cellprob_threshold=CELLPROB_THRESHOLD,
        z_axis=0,
        channel_axis=None,
        batch_size=args.batch_size,
    )
    dt = time.time() - t0
    masks = masks.astype(np.uint32)

    # Exclude nuclei touching the xy border (in the scaled volume).
    if args.exclude_edge:
        edge = np.concatenate([
            masks[:, 0, :].ravel(), masks[:, -1, :].ravel(),
            masks[:, :, 0].ravel(), masks[:, :, -1].ravel(),
        ])
        edge = np.unique(edge)
        edge = edge[edge != 0]
        if len(edge):
            masks[np.isin(masks, edge)] = 0

    # Per-nucleus size & shape metrics, then optional mitotic filtering.
    voxel_um3 = new_xy_um * new_xy_um * Z_UM
    metrics, removed = nucleus_metrics(masks, voxel_um3, args)
    n_total = len(metrics)

    prefix = os.path.join(out_dir, f"{base}_c{args._ch_index}_{wl}_{marker}")

    # Mid-z overlay (kept red, excluded blue) BEFORE dropping excluded labels.
    zmid = img_scaled.shape[0] // 2
    img_u8 = stretch_to_8bit(img_scaled[zmid])
    Image.fromarray(overlay_outlines(img_u8, masks[zmid], removed)).save(
        prefix + "_midz_overlay.png")

    # Apply the filter: drop excluded nuclei.
    if removed:
        masks[np.isin(masks, np.asarray(list(removed), dtype=masks.dtype))] = 0
    n_kept = n_total - len(removed)
    print(f"  -> {n_kept} nuclei kept, {len(removed)} excluded (of {n_total})  ({dt:.1f}s)")

    # --- Save filtered masks (scaled resolution) + per-nucleus metrics ---
    tifffile.imwrite(prefix + "_masks3d.tif", masks.astype(np.uint16), imagej=True)
    np.savez_compressed(prefix + "_masks3d.npz", masks=masks.astype(np.uint16),
                        anisotropy=anisotropy, pxScale=pxScale)
    save_metrics_csv(prefix + "_nuclei_metrics.csv", metrics)
    print_metric_summary(metrics, args)

    return {"channel": args._ch_index, "wl": wl, "marker": marker,
            "n_nuclei": n_kept, "n_excluded": len(removed), "seconds": round(dt, 1),
            "scaled_shape": img_scaled.shape, "overlay": prefix + "_midz_overlay.png"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dax_path")
    ap.add_argument("--out", default=None, help="output dir")
    ap.add_argument("--channels", default="all",
                    help="comma-separated channel indices (0..3) or 'all'")
    ap.add_argument("--batch-size", type=int, default=8)
    ap.add_argument("--no-exclude-edge", dest="exclude_edge", action="store_false")
    ap.add_argument("--bf16", action="store_true",
                    help="use bfloat16 (needs torch with bf16 F.interpolate; "
                         "torch 1.13 does not, so default is float32)")
    ap.add_argument("--trim-z", type=int, default=1,
                    help="drop this many dead z-slices from each end of the "
                         "stack before segmenting (default 1; 0 to keep all)")
    # Size & circularity filters to exclude mitotic / mis-segmented nuclei.
    # All optional: if unset, metrics are still computed/saved but nothing is dropped.
    ap.add_argument("--min-volume-um3", type=float, default=None,
                    help="drop nuclei smaller than this volume (um^3)")
    ap.add_argument("--max-volume-um3", type=float, default=None,
                    help="drop nuclei larger than this volume (um^3)")
    ap.add_argument("--min-circularity", type=float, default=None,
                    help="drop nuclei with xy-footprint circularity below this (0-1)")
    ap.add_argument("--max-circularity", type=float, default=None,
                    help="drop nuclei with xy-footprint circularity above this")
    ap.set_defaults(exclude_edge=True)
    args = ap.parse_args()

    if args.out is None:
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        args.out = os.path.join(root, "output", "masks_3d")
    os.makedirs(args.out, exist_ok=True)

    if args.channels == "all":
        ch_indices = list(range(len(WAVELENGTHS)))
    else:
        ch_indices = [int(c) for c in args.channels.split(",")]

    base = os.path.splitext(os.path.basename(args.dax_path))[0]
    print(f"Reading {args.dax_path}")
    vol, info = read_dax_multichannel(args.dax_path, len(WAVELENGTHS))  # (z, c, y, x)
    print(f"  de-interleaved: {info['n_z']} z-planes x {info['n_channels']} channels, "
          f"{info['height']}x{info['width']}")

    # First/last z-planes are dead frames; drop them before segmenting.
    if args.trim_z > 0:
        if vol.shape[0] > 2 * args.trim_z:
            vol = vol[args.trim_z: vol.shape[0] - args.trim_z]
            print(f"  trimmed {args.trim_z} dead z-slice(s) from each end "
                  f"-> {vol.shape[0]} z-planes")
        else:
            print(f"  WARNING: only {vol.shape[0]} z-planes; skipping --trim-z")

    # Cellpose-SAM defaults to bfloat16, but torch 1.13.1 has no bfloat16 kernel
    # for F.interpolate (used in the SAM encoder's relative-position resize), so
    # inference crashes regardless of GPU. Run in float32 unless --bf16 is passed
    # (re-enable once on a newer torch that implements the bf16 upsample kernel).
    print(f"Loading Cellpose-SAM model (gpu, bfloat16={args.bf16})...")
    model = models.CellposeModel(gpu=True, use_bfloat16=args.bf16)

    summary = []
    for ci in ch_indices:
        args._ch_index = ci
        wl = WAVELENGTHS[ci]
        res = segment_channel(vol[:, ci], args.out, base, wl, model, args)
        summary.append(res)

    print("\n================ SUMMARY ================")
    for r in summary:
        print(f"  c{r['channel']} {r['wl']} {r['marker']:5s}: "
              f"{r['n_nuclei']:4d} kept / {r['n_excluded']:3d} excluded  "
              f"({r['seconds']}s)  -> {os.path.basename(r['overlay'])}")
    print(f"\nOutputs in: {args.out}")


if __name__ == "__main__":
    main()
