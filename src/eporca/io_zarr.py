"""
Step 0: convert interleaved .dax FOVs to single-scale OME-Zarr (OME-NGFF v0.4),
and provide reader helpers used by the segmentation and foci steps.

The OME-Zarr stores the *full* raw volume (no z-trim) as dims (c, z, y, x) with
physical scales in micrometres. Downstream steps apply ``trim_z`` on read so the
on-disk copy stays faithful to the raw acquisition.

Requires zarr v2 (`pip install "zarr<3" numcodecs`); the classic group/array API
is used here. Reading also works from the cellpose-gpu env (which has zarr too).
"""

from __future__ import annotations

import numpy as np
import zarr
import numcodecs

from .dax_reader import read_dax_multichannel
from .config import Config


def _compressor(cfg: Config):
    return numcodecs.Blosc(
        cname=cfg.zarr.compressor, clevel=cfg.zarr.clevel,
        shuffle=numcodecs.Blosc.SHUFFLE,
    )


def to_zarr(cfg: Config, fov: int, overwrite: bool = True) -> str:
    """Convert one FOV's .dax to a single-scale OME-Zarr; return the store path."""
    dax = cfg.dax_path(fov)
    vol, info = read_dax_multichannel(dax, cfg.n_channels)      # (z, c, y, x), memmap
    arr = np.ascontiguousarray(np.transpose(np.asarray(vol), (1, 0, 2, 3)))  # (c,z,y,x)

    out = cfg.zarr_path(fov)
    root = zarr.open_group(out, mode="w" if overwrite else "a")
    zc = cfg.zarr.chunk_zyx
    chunks = (1, min(zc[0], arr.shape[1]), min(zc[1], arr.shape[2]), min(zc[2], arr.shape[3]))
    root.create_dataset(
        "0", data=arr, chunks=chunks, compressor=_compressor(cfg),
        dtype=arr.dtype, overwrite=True,
    )

    px, zum = cfg.acquisition.pixel_size_um, cfg.acquisition.z_um
    root.attrs["multiscales"] = [{
        "version": "0.4",
        "name": f"fov_{fov:03d}",
        "axes": [
            {"name": "c", "type": "channel"},
            {"name": "z", "type": "space", "unit": "micrometer"},
            {"name": "y", "type": "space", "unit": "micrometer"},
            {"name": "x", "type": "space", "unit": "micrometer"},
        ],
        "datasets": [{
            "path": "0",
            "coordinateTransformations": [
                {"type": "scale", "scale": [1.0, zum, px, px]}
            ],
        }],
    }]
    root.attrs["omero"] = {
        "channels": [{"label": m} for m in cfg.markers],
    }
    root.attrs["eporca"] = {"fov": fov, "condition": cfg.condition_for_fov(fov)}
    return out


def open_fov(cfg: Config, fov: int):
    """Return the lazy zarr array for a FOV, shape (c, z, y, x)."""
    return zarr.open_group(cfg.zarr_path(fov), mode="r")["0"]


def read_channel(cfg: Config, fov: int, marker: str, trim: bool = True) -> np.ndarray:
    """Materialize one channel as (z, y, x) float-free uint array, z-trimmed by default."""
    ci = cfg.index_of(marker)
    arr = np.asarray(open_fov(cfg, fov)[ci])             # (z, y, x)
    t = cfg.acquisition.trim_z
    if trim and t > 0 and arr.shape[0] > 2 * t:
        arr = arr[t: arr.shape[0] - t]
    return arr
