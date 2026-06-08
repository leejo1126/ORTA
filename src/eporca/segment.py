"""
Step 1: 3D nuclear segmentation with Cellpose-SAM (runs in the cellpose-gpu env).

Reads the DAPI channel from a FOV's OME-Zarr, segments nuclei in 3D, applies
size/circularity filters, and writes a (scaled-resolution) label volume + a
per-nucleus metrics CSV. Carries over the environment fixes found during
development:
  * torch 1.13 has no bf16 F.interpolate kernel -> run float32 (config use_bf16).
  * pin to the bf16/fast GPU via CUDA_VISIBLE_DEVICES (config gpu_index).
  * cellpose 4.0.5 casts mask indices to int32; torch 1.13 needs int64 -> shim.

The mask is stored at the rescaled working resolution (z, y', x') together with
the pxScale and full-resolution (y, x) shape in attrs; foci.py upscales it to
full xy on demand (keeps per-FOV masks ~20 MB instead of ~435 MB).
"""

from __future__ import annotations

import os
import numpy as np
import scipy.ndimage

from .config import Config
from .io_zarr import read_channel


def _patch_get_masks_torch_for_old_torch() -> None:
    import torch
    if int(torch.__version__.split(".")[0]) >= 2:
        return
    import cellpose.dynamics as cpdyn
    if getattr(cpdyn.get_masks_torch, "_eporca_patched", False):
        return
    _orig = cpdyn.get_masks_torch

    def _patched(pt, *args, **kwargs):
        return _orig(pt.long(), *args, **kwargs)

    _patched._eporca_patched = True
    cpdyn.get_masks_torch = _patched


def _exclude_edge_labels(masks: np.ndarray) -> None:
    edge = np.concatenate([
        masks[:, 0, :].ravel(), masks[:, -1, :].ravel(),
        masks[:, :, 0].ravel(), masks[:, :, -1].ravel(),
    ])
    edge = np.unique(edge)
    edge = edge[edge != 0]
    if len(edge):
        masks[np.isin(masks, edge)] = 0


def _nucleus_metrics(masks, voxel_um3, px_scale, z_um, pixel_um, seg):
    """Per-nucleus volume + xy-footprint circularity + centroid (full-res um),
    with a keep/exclude decision from the size & circularity thresholds."""
    from skimage.measure import regionprops

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

        foot = sub.any(axis=0).astype(np.uint8)
        props = regionprops(foot)
        if props and props[0].perimeter > 0:
            circ = float(4.0 * np.pi * props[0].area / (props[0].perimeter ** 2))
        else:
            circ = 0.0

        zz, yy, xx = np.nonzero(sub)
        cz = zz.mean() + sl[0].start                  # scaled-z (== trimmed plane)
        cy = (yy.mean() + sl[1].start) / px_scale     # full-res y
        cx = (xx.mean() + sl[2].start) / px_scale     # full-res x

        keep = True
        if seg.min_volume_um3 is not None and vol_um3 < seg.min_volume_um3:
            keep = False
        if seg.max_volume_um3 is not None and vol_um3 > seg.max_volume_um3:
            keep = False
        if seg.min_circularity is not None and circ < seg.min_circularity:
            keep = False
        if seg.max_circularity is not None and circ > seg.max_circularity:
            keep = False

        metrics.append({
            "label": int(L), "volume_vox": vol_vox,
            "volume_um3": round(vol_um3, 3), "circularity": round(circ, 4),
            "com_z_um": round(cz * z_um, 4),
            "com_y_um": round(cy * pixel_um, 4),
            "com_x_um": round(cx * pixel_um, 4),
            "kept": int(keep),
        })
        if not keep:
            removed.add(int(L))
    return metrics, removed


def _save_mask_zarr(path, masks, attrs):
    import zarr
    import numcodecs
    root = zarr.open_group(path, mode="w")
    root.create_dataset(
        "0", data=masks, chunks=(min(8, masks.shape[0]), 512, 512),
        compressor=numcodecs.Blosc("zstd", clevel=5), overwrite=True,
    )
    root.attrs.update(attrs)


def _save_metrics_csv(path, metrics):
    cols = ["label", "volume_vox", "volume_um3", "circularity",
            "com_z_um", "com_y_um", "com_x_um", "kept"]
    with open(path, "w") as fh:
        fh.write(",".join(cols) + "\n")
        for m in metrics:
            fh.write(",".join(str(m[c]) for c in cols) + "\n")


def segment_fov(cfg: Config, fov: int) -> dict:
    """Segment nuclei for one FOV; write mask zarr + metrics CSV; return summary."""
    seg = cfg.segmentation
    os.environ["CUDA_VISIBLE_DEVICES"] = str(seg.gpu_index)

    from cellpose import models  # imported after CUDA_VISIBLE_DEVICES is set
    _patch_get_masks_torch_for_old_torch()

    pixel_um = cfg.acquisition.pixel_size_um
    z_um = cfg.acquisition.z_um

    img = read_channel(cfg, fov, seg.channel_marker, trim=True).astype(np.float32)
    full_yx = img.shape[1:]                                   # (Y, X) full res
    if np.any(img == 0):
        img[img == 0] = np.quantile(img[img > 0], 0.01)

    px_scale = pixel_um * seg.cellpose_diam_px / seg.diam_um
    new_xy_um = pixel_um / px_scale
    anisotropy = z_um / new_xy_um
    img_scaled = scipy.ndimage.zoom(img, (1.0, px_scale, px_scale), order=1)
    if seg.blur_factor > 0:
        img_scaled = scipy.ndimage.gaussian_filter(
            img_scaled, (0, seg.blur_factor, seg.blur_factor))

    model = models.CellposeModel(gpu=True, use_bfloat16=seg.use_bf16)
    masks, _flows, _styles = model.eval(
        img_scaled, diameter=seg.cellpose_diam_px, do_3D=True,
        anisotropy=anisotropy, flow_threshold=seg.flow_threshold,
        cellprob_threshold=seg.cellprob_threshold, z_axis=0,
        channel_axis=None, batch_size=seg.batch_size,
    )
    masks = masks.astype(np.uint32)
    if seg.exclude_edge:
        _exclude_edge_labels(masks)

    voxel_um3 = new_xy_um * new_xy_um * z_um
    metrics, removed = _nucleus_metrics(masks, voxel_um3, px_scale, z_um, pixel_um, seg)
    if removed:
        masks[np.isin(masks, np.asarray(list(removed), dtype=masks.dtype))] = 0
    n_kept = len(metrics) - len(removed)

    dtype = np.uint16 if masks.max() <= 65535 else np.uint32
    _save_mask_zarr(cfg.mask_path(fov), masks.astype(dtype), {
        "fov": fov, "px_scale": float(px_scale), "anisotropy": float(anisotropy),
        "full_yx": [int(full_yx[0]), int(full_yx[1])], "trim_z": cfg.acquisition.trim_z,
        "n_nuclei": int(n_kept), "z_um": z_um, "pixel_size_um": pixel_um,
    })
    _save_metrics_csv(cfg.mask_metrics_path(fov), metrics)
    return {"fov": fov, "n_total": len(metrics), "n_kept": n_kept,
            "n_excluded": len(removed), "scaled_shape": tuple(map(int, masks.shape))}
