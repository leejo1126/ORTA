"""
Package one FOV's raw image + nuclei mask + per-marker foci labels into a single
**OME-NGFF v0.4** store -- the standard bioimaging layout (an image with a `labels/`
subgroup) for sharing / BioImage-Archive deposition and for tools like napari that read
labels linked to their image.

This is a post-hoc *packaging* step: it only READS the pipeline's existing per-step
outputs (raw `fov_NNN.zarr`, nuclei mask, foci label zarrs) and writes a NEW store at
`<data_dir>/packaged/fov_NNN.ome.zarr` -- it never modifies pipeline outputs. Image and
labels share the trimmed `(z,y,x)` analysis grid, with physical scales in micrometres.

    eporca package --config config/config.yaml --fov 0
"""

from __future__ import annotations

import numpy as np
import zarr

from .config import Config
from .io_zarr import read_channel, _compressor
from .foci import load_nuclear_labels_3d


def _write_label(labels_grp, name: str, arr: np.ndarray, cfg: Config) -> None:
    """Write one label image (z,y,x) as an OME-NGFF labels/<name> subgroup."""
    px, zum = cfg.acquisition.pixel_size_um, cfg.acquisition.z_um
    g = labels_grp.create_group(name, overwrite=True)
    g.create_dataset("0", data=arr.astype(np.uint32),
                     chunks=(min(8, arr.shape[0]), 512, 512),
                     compressor=_compressor(cfg), overwrite=True)
    g.attrs["multiscales"] = [{
        "version": "0.4", "name": name,
        "axes": [{"name": "z", "type": "space", "unit": "micrometer"},
                 {"name": "y", "type": "space", "unit": "micrometer"},
                 {"name": "x", "type": "space", "unit": "micrometer"}],
        "datasets": [{"path": "0",
                      "coordinateTransformations": [{"type": "scale", "scale": [zum, px, px]}]}],
    }]
    g.attrs["image-label"] = {"version": "0.4", "source": {"image": "../../"}}


def package_fov(cfg: Config, fov: int) -> str:
    """Assemble fov's raw (c,z,y,x) + nuclei + foci labels into one OME-NGFF store."""
    px, zum = cfg.acquisition.pixel_size_um, cfg.acquisition.z_um
    markers = cfg.markers

    img = np.stack([read_channel(cfg, fov, m, trim=True) for m in markers], axis=0)  # (c,z,y,x)
    nuc = load_nuclear_labels_3d(cfg, fov, img.shape[1:])                            # (z,y,x)
    foci = {}
    for m in markers:
        try:
            foci[m] = np.asarray(zarr.open_group(cfg.foci_label_path(fov, m), mode="r")["0"])
        except Exception:                                                            # noqa: BLE001
            foci[m] = None                          # foci not computed / save_labels off / busy

    out = str(cfg.data_dir / "packaged" / f"fov_{fov:03d}.ome.zarr")
    root = zarr.open_group(out, mode="w")
    zc = cfg.zarr.chunk_zyx
    root.create_dataset(
        "0", data=img, dtype=img.dtype, compressor=_compressor(cfg), overwrite=True,
        chunks=(1, min(zc[0], img.shape[1]), min(zc[1], img.shape[2]), min(zc[2], img.shape[3])))
    root.attrs["multiscales"] = [{
        "version": "0.4", "name": f"fov_{fov:03d}",
        "axes": [{"name": "c", "type": "channel"},
                 {"name": "z", "type": "space", "unit": "micrometer"},
                 {"name": "y", "type": "space", "unit": "micrometer"},
                 {"name": "x", "type": "space", "unit": "micrometer"}],
        "datasets": [{"path": "0",
                      "coordinateTransformations": [{"type": "scale", "scale": [1.0, zum, px, px]}]}],
    }]
    root.attrs["omero"] = {"channels": [{"label": m} for m in markers]}
    root.attrs["eporca"] = {"fov": fov, "condition": cfg.condition_for_fov(fov)}

    labels_grp = root.create_group("labels", overwrite=True)
    names = ["nuclei"]
    _write_label(labels_grp, "nuclei", nuc, cfg)
    for m in markers:
        if foci[m] is not None:
            _write_label(labels_grp, f"{m}_foci", foci[m], cfg)
            names.append(f"{m}_foci")
    labels_grp.attrs["labels"] = names
    return out
