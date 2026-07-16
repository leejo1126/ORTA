"""
Make maximum-intensity z-projections from .dax files (single- or multi-channel).

Channel-interleaved acquisitions (filenames like zscan_647_561_488_405_NNN.dax)
store one frame per channel at each z-step. This script auto-detects the channel
count from the wavelength tokens in the filename and de-interleaves accordingly.

Saves, per input file:
  Single channel:
    - <base>_max.tif            full-precision 16-bit TIFF
    - <base>_max_preview.png    contrast-stretched 8-bit PNG preview
  Multi channel:
    - <base>_max_c<i>_<wl>.tif          per-channel 16-bit TIFF
    - <base>_max_c<i>_<wl>_preview.png  per-channel 8-bit PNG preview
    - <base>_max_grid.png               combined labeled grid (all channels)

Usage:
    python make_max_projection.py <dax_file_or_folder> [output_dir] [--channels N]

If no output_dir is given, results go to ../output/max_projections relative to
this script. Channel count is auto-detected from the filename unless --channels
is provided.
"""

from __future__ import annotations

import os
import re
import sys
import glob

import numpy as np
import tifffile
from PIL import Image, ImageDraw

from dax_reader import max_projection, max_projection_multichannel


def stretch_to_8bit(img: np.ndarray, low_pct: float = 0.5, high_pct: float = 99.5) -> np.ndarray:
    """Percentile contrast-stretch a 16-bit image to 8-bit for preview."""
    lo, hi = np.percentile(img, [low_pct, high_pct])
    if hi <= lo:
        hi = lo + 1
    scaled = np.clip((img.astype(np.float32) - lo) / (hi - lo), 0, 1)
    return (scaled * 255).astype(np.uint8)


def wavelengths_from_name(base: str) -> list[str]:
    """
    Extract wavelength tokens from a name like 'zscan_647_561_488_405_000'.
    Returns e.g. ['647','561','488','405']. Trailing acquisition index is ignored.
    """
    nums = re.findall(r"\d+", base)
    # Keep tokens that look like laser lines (3-digit, common fluorescence range).
    wls = [n for n in nums if len(n) == 3 and 300 <= int(n) <= 850]
    return wls


def save_grid(channels: np.ndarray, labels: list[str], out_path: str, downscale: int = 4) -> None:
    """Save a labeled grid PNG with one (contrast-stretched) panel per channel."""
    n = channels.shape[0]
    cols = int(np.ceil(np.sqrt(n)))
    rows = int(np.ceil(n / cols))
    h, w = channels.shape[1] // downscale, channels.shape[2] // downscale

    canvas = Image.new("L", (cols * w, rows * h), color=0)
    draw = ImageDraw.Draw(canvas)
    for i in range(n):
        panel = stretch_to_8bit(channels[i])[::downscale, ::downscale]
        img = Image.fromarray(panel)
        r, c = divmod(i, cols)
        canvas.paste(img, (c * w, r * h))
        draw.text((c * w + 6, r * h + 6), labels[i], fill=255)
    canvas.save(out_path)


def process_one(dax_path: str, out_dir: str, n_channels: int | None) -> None:
    base = os.path.splitext(os.path.basename(dax_path))[0]
    wls = wavelengths_from_name(base)

    # Resolve channel count: explicit flag > inferred from filename > single.
    if n_channels is None:
        nc = len(wls) if len(wls) >= 2 else 1
    else:
        nc = n_channels

    if nc <= 1:
        mip = max_projection(dax_path)
        tif_path = os.path.join(out_dir, base + "_max.tif")
        png_path = os.path.join(out_dir, base + "_max_preview.png")
        tifffile.imwrite(tif_path, mip)
        Image.fromarray(stretch_to_8bit(mip)).save(png_path)
        print(
            f"{base}: 1ch shape={mip.shape} dtype={mip.dtype} "
            f"min={mip.min()} max={mip.max()} median={int(np.median(mip))}"
        )
        print(f"  -> {tif_path}")
        print(f"  -> {png_path}")
        return

    channels = max_projection_multichannel(dax_path, nc)  # (nc, H, W)
    # Label each channel by wavelength when available, else by index.
    labels = [
        f"c{i} {wls[i]}" if i < len(wls) else f"c{i}" for i in range(nc)
    ]
    print(f"{base}: {nc}ch shape={channels.shape} dtype={channels.dtype}")
    for i in range(nc):
        ch = channels[i]
        wl = wls[i] if i < len(wls) else f"ch{i}"
        tif_path = os.path.join(out_dir, f"{base}_max_c{i}_{wl}.tif")
        png_path = os.path.join(out_dir, f"{base}_max_c{i}_{wl}_preview.png")
        tifffile.imwrite(tif_path, ch)
        Image.fromarray(stretch_to_8bit(ch)).save(png_path)
        print(
            f"  c{i} ({wl}): min={ch.min()} max={ch.max()} median={int(np.median(ch))}"
        )
        print(f"    -> {tif_path}")
        print(f"    -> {png_path}")

    grid_path = os.path.join(out_dir, f"{base}_max_grid.png")
    save_grid(channels, labels, grid_path)
    print(f"  grid -> {grid_path}")


def main() -> None:
    args = [a for a in sys.argv[1:]]
    n_channels = None
    if "--channels" in args:
        idx = args.index("--channels")
        n_channels = int(args[idx + 1])
        del args[idx : idx + 2]

    if not args:
        print(__doc__)
        sys.exit(1)

    target = args[0]
    if len(args) >= 2:
        out_dir = args[1]
    else:
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        out_dir = os.path.join(project_root, "output", "max_projections")

    os.makedirs(out_dir, exist_ok=True)

    if os.path.isdir(target):
        dax_files = sorted(glob.glob(os.path.join(target, "*.dax")))
        if not dax_files:
            print(f"No .dax files found in {target}")
            sys.exit(1)
        print(f"Found {len(dax_files)} .dax files in {target}")
        for f in dax_files:
            process_one(f, out_dir, n_channels)
    else:
        process_one(target, out_dir, n_channels)


if __name__ == "__main__":
    main()
