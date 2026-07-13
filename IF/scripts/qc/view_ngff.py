"""
Open a packaged OME-NGFF store (from `eporca package`) in napari: the multi-channel image
plus every labels/* (nuclei + per-marker foci) as colored label layers, with correct
anisotropic voxel scaling. Reads the store directly (no napari-ome-zarr plugin needed).

    python IF/scripts/qc/view_ngff.py --store IF/data/packaged/fov_000.ome.zarr
    python IF/scripts/qc/view_ngff.py --config IF/config/config.yaml --fov 0   # resolve path

In napari: opens in 3D; each channel is an additive image layer, each labels layer is
toggleable (left panel). Needs a desktop session (Qt window); won't render headless.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import zarr


def main() -> None:
    ap = argparse.ArgumentParser(description="napari viewer for a packaged OME-NGFF FOV")
    ap.add_argument("--store", default=None, help="path to a fov_NNN.ome.zarr")
    ap.add_argument("--config", default="IF/config/config.yaml")
    ap.add_argument("--fov", type=int, default=0)
    args = ap.parse_args()

    store = args.store
    if store is None:
        from eporca.config import Config
        store = str(Config.load(args.config).data_dir / "packaged" / f"fov_{args.fov:03d}.ome.zarr")

    import napari  # late import: heavy, only needed for the GUI

    r = zarr.open_group(store, mode="r")
    scale = r.attrs["multiscales"][0]["datasets"][0]["coordinateTransformations"][0]["scale"]
    zyx = tuple(scale[1:])                                  # (z, y, x) microns
    img = np.asarray(r["0"])                                # (c, z, y, x)
    channels = ([c["label"] for c in r.attrs.get("omero", {}).get("channels", [])]
                or [f"c{i}" for i in range(img.shape[0])])

    v = napari.Viewer(ndisplay=3, title=Path(store).name)
    for i, name in enumerate(channels):
        v.add_image(img[i], name=name, scale=zyx, blending="additive", rendering="mip",
                    contrast_limits=[float(np.percentile(img[i], 1)),
                                     float(np.percentile(img[i], 99.8))], visible=(i == 0))
    lg = r["labels"]
    for name in lg.attrs["labels"]:
        v.add_labels(np.asarray(lg[name]["0"]).astype(np.int32), name=name, scale=zyx,
                     opacity=0.5, visible=(name == "nuclei"))
    napari.run()


if __name__ == "__main__":
    main()
