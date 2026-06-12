"""
Export a FOV's foci/condensate calls as an ImageJ/Fiji hyperstack TIFF, so you can
inspect calling in 3D without touching OME-Zarr. Writes one TIFF per marker with
channels = [raw (bg-subtracted), foci labels, (optional) nuclei], calibrated in
microns (xy from pixel_size_um, z spacing from z_um) so the z:xy aspect is correct.

    python IF/scripts/export_foci_tiff.py --config IF/config/config.yaml --fov 0 --marker Sc35
    python IF/scripts/export_foci_tiff.py --config IF/config/config.yaml --fov 0 --marker Sc35,Brd4 --with-nuclei

In Fiji:
  - File > Open the .tif (opens as a composite hyperstack: C channels x Z slices).
  - For the labels channel, Image > Lookup Tables > glasbey (or "3-3-2 RGB") to see
    each focus in its own color; the raw channel keeps a Grays LUT.
  - 3D view: Image > Stacks > 3D Project (quick), or Plugins > 3D Viewer (add the
    labels channel as a surface over the raw volume). Calibration is read from the
    TIFF, so proportions are right.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import zarr
import tifffile

from eporca.config import Config
from eporca.io_zarr import read_channel
from eporca.foci import load_nuclear_labels_3d, subtract_background


def main() -> None:
    ap = argparse.ArgumentParser(description="Export foci calls as a Fiji hyperstack TIFF")
    ap.add_argument("--config", default="IF/config/config.yaml")
    ap.add_argument("--fov", type=int, default=0)
    ap.add_argument("--marker", default="Sc35", help="comma-separated markers (e.g. Sc35,Brd4)")
    ap.add_argument("--out", default=None, help="output dir (default: <data>/figures)")
    ap.add_argument("--with-nuclei", action="store_true", help="add a nucleus-mask channel")
    args = ap.parse_args()

    cfg = Config.load(args.config)
    px, zum = cfg.acquisition.pixel_size_um, cfg.acquisition.z_um
    out_dir = Path(args.out) if args.out else cfg.figures_dir()
    out_dir.mkdir(parents=True, exist_ok=True)

    for marker in [m.strip() for m in args.marker.split(",") if m.strip()]:
        raw = read_channel(cfg, args.fov, marker, trim=True).astype(np.float32)
        raw = subtract_background(raw, cfg.foci.background)
        raw = np.clip(raw, 0, 65535).astype(np.uint16)                # (z, y, x)

        path = cfg.foci_label_path(args.fov, marker)
        try:
            lab = np.asarray(zarr.open_group(path, mode="r")["0"]).astype(np.uint16)
        except Exception as e:                                        # noqa: BLE001
            raise SystemExit(f"No saved foci labels for {marker} at {path}; run "
                             f"`eporca foci --config {args.config} --fov {args.fov}` first. [{e}]")

        chans, names = [raw, lab], ["raw", "foci_labels"]
        if args.with_nuclei:
            chans.append(load_nuclear_labels_3d(cfg, args.fov, raw.shape).astype(np.uint16))
            names.append("nuclei")

        stack = np.stack(chans, axis=1)                               # (Z, C, Y, X) ImageJ order
        out = out_dir / f"foci_fiji_fov{args.fov:03d}_{marker}.tif"
        tifffile.imwrite(
            str(out), stack, imagej=True,
            resolution=(1.0 / px, 1.0 / px),
            metadata={"spacing": zum, "unit": "um", "axes": "ZCYX", "Labels": names},
        )
        print(f"wrote {out}  (Z,C,Y,X)={stack.shape}  channels={names}  "
              f"foci={int(lab.max())}")


if __name__ == "__main__":
    main()
