"""
Interactive 3D viewer for foci/condensate calls. Loads a FOV's raw channel, the
SAVED foci label volume, and the nucleus masks into napari with correct anisotropic
voxel scaling (z step vs xy pixel), so you can visually confirm calling in 3D
without working with OME-Zarr directly.

    python IF/scripts/view_foci.py --config IF/config/config.yaml --fov 0 --marker Sc35
    python IF/scripts/view_foci.py --config IF/config/config.yaml --fov 0 --marker Sc35,Brd4

In napari:
  - it opens in 3D; drag to rotate, or use the 2D/3D toggle (bottom-left) to flip.
  - each marker contributes a raw image layer (additive blending) + a "foci" labels
    layer (each focus its own color); the nucleus mask is added hidden by default.
  - toggle/adjust layers in the left panel; the labels join the per_spot CSV by id.

Needs a desktop session (opens a Qt window); it will not render headless.
"""

from __future__ import annotations

import argparse

import numpy as np
import zarr

from eporca.config import Config
from eporca.io_zarr import read_channel
from eporca.foci import load_nuclear_labels_3d, subtract_background


def _load_labels(cfg: Config, fov: int, marker: str) -> np.ndarray:
    path = cfg.foci_label_path(fov, marker)
    try:
        return np.asarray(zarr.open_group(path, mode="r")["0"])
    except Exception as e:                                            # noqa: BLE001
        raise SystemExit(f"No saved foci labels for {marker} at {path}; run "
                         f"`eporca foci --config <cfg> --fov {fov}` (save_labels) first. [{e}]")


def main() -> None:
    ap = argparse.ArgumentParser(description="napari 3D viewer for foci/condensate calls")
    ap.add_argument("--config", default="IF/config/config.yaml")
    ap.add_argument("--fov", type=int, default=0)
    ap.add_argument("--marker", default="Sc35", help="comma-separated markers (e.g. Sc35,Brd4)")
    ap.add_argument("--raw", choices=["bgsub", "raw"], default="bgsub",
                    help="show background-subtracted (default) or unmodified raw intensity")
    ap.add_argument("--no-nuclei", action="store_true", help="skip the nucleus-mask layer")
    args = ap.parse_args()

    import napari  # late import: heavy, and only needed when actually opening the GUI

    cfg = Config.load(args.config)
    px, zum = cfg.acquisition.pixel_size_um, cfg.acquisition.z_um
    scale = (zum, px, px)                                  # (z, y, x) microns -> right 3D aspect

    viewer = napari.Viewer(ndisplay=3, title=f"ORTA foci  fov {args.fov:03d}")
    shape = None
    for marker in [m.strip() for m in args.marker.split(",") if m.strip()]:
        raw = read_channel(cfg, args.fov, marker, trim=True).astype(np.float32)
        if args.raw == "bgsub":
            raw = subtract_background(raw, cfg.foci.background)
        shape = raw.shape
        viewer.add_image(
            raw, name=f"{marker} raw", scale=scale, blending="additive", rendering="mip",
            contrast_limits=[float(np.percentile(raw, 1)), float(np.percentile(raw, 99.8))],
        )
        lab = _load_labels(cfg, args.fov, marker)
        viewer.add_labels(lab.astype(np.int32), name=f"{marker} foci", scale=scale, opacity=0.5)

    if not args.no_nuclei and shape is not None:
        nuc = load_nuclear_labels_3d(cfg, args.fov, shape)
        viewer.add_labels(nuc.astype(np.int32), name="nuclei", scale=scale,
                          opacity=0.25, visible=False)

    napari.run()


if __name__ == "__main__":
    main()
