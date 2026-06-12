"""
QC montage built from the SAVED foci label volumes (not by re-detecting), so it
verifies the on-disk per-focus geometry. For a few nuclei, shows each marker's raw
(background-subtracted) with every focus filled in its own random color at the
nucleus mid-z.

    python IF/scripts/qc/overlay_from_labels.py --config IF/config/config.yaml --fov 0
    python IF/scripts/qc/overlay_from_labels.py --config IF/config/config.yaml --fov 0 --cells 17,44 --mag 5
"""

from __future__ import annotations

import argparse
import numpy as np
import scipy.ndimage as ndi
import zarr
from PIL import Image, ImageDraw

from eporca.config import Config
from eporca.io_zarr import read_channel
from eporca.foci import load_nuclear_labels_3d, subtract_background, _expand_slices


def stretch(img, lo=1.0, hi=99.8):
    a, b = np.percentile(img, [lo, hi])
    if b <= a:
        b = a + 1
    return (np.clip((img.astype(np.float32) - a) / (b - a), 0, 1) * 255).astype(np.uint8)


def colorize(gray, lab2d, rng, alpha=0.55):
    base = np.stack([gray] * 3, -1).astype(np.float32)
    out = base.copy()
    for i in np.unique(lab2d):
        if i == 0:
            continue
        m = lab2d == i
        out[m] = (1 - alpha) * base[m] + alpha * rng.integers(60, 256, 3)
    return out.astype(np.uint8)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--fov", type=int, default=0)
    ap.add_argument("--cells", default=None)
    ap.add_argument("--n", type=int, default=3)
    ap.add_argument("--mag", type=int, default=4)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    cfg = Config.load(args.config)
    markers = cfg.markers
    ref = read_channel(cfg, args.fov, markers[0], trim=True)
    nuc = load_nuclear_labels_3d(cfg, args.fov, ref.shape)
    slices = ndi.find_objects(nuc)
    if args.cells:
        cells = [int(x) for x in args.cells.split(",")]
    else:
        counts = np.bincount(nuc.ravel()); counts[0] = 0
        order = np.argsort(counts)[::-1]
        cells = [int(L) for L in order
                 if 1 <= L <= len(slices) and slices[L - 1] is not None][: args.n]

    # load each marker's raw (bg-subtracted) + saved label volume
    raws, labs = {}, {}
    for m in markers:
        raws[m] = subtract_background(read_channel(cfg, args.fov, m, trim=True).astype(np.float32),
                                      cfg.foci.background)
        labs[m] = np.asarray(zarr.open_group(cfg.foci_label_path(args.fov, m), mode="r")["0"])

    rng = np.random.default_rng(0)
    rows = []
    for L in cells:
        sl = _expand_slices(slices[L - 1], ref.shape, (1, 8, 8))
        subnuc = nuc[sl] == L
        zs = np.where(subnuc.any(axis=(1, 2)))[0]
        zmid = int(zs[len(zs) // 2]) if len(zs) else subnuc.shape[0] // 2
        panels = []
        for m in markers:
            lab2d = labs[m][sl][zmid]
            n_here = len(np.unique(lab2d)) - (1 if (lab2d == 0).any() else 0)
            ov = colorize(stretch(raws[m][sl][zmid]), lab2d, rng)
            img = Image.fromarray(ov).resize((ov.shape[1] * args.mag, ov.shape[0] * args.mag),
                                             Image.NEAREST)
            ImageDraw.Draw(img).text((4, 4), f"{m} (saved labels, z-slice n={n_here})",
                                     fill=(255, 255, 0))
            panels.append(img)
        h = max(p.height for p in panels)
        w = sum(p.width for p in panels) + 6 * (len(panels) - 1)
        row = Image.new("RGB", (w, h), (15, 15, 15))
        x = 0
        for p in panels:
            row.paste(p, (x, 0)); x += p.width + 6
        rows.append((L, row))

    W = max(r.width for _, r in rows)
    H = sum(r.height + 18 for _, r in rows) + 6 * len(rows)
    canvas = Image.new("RGB", (W, H), (15, 15, 15))
    y = 0
    for L, r in rows:
        ImageDraw.Draw(canvas).text((4, y), f"FOV {args.fov} cell {L}", fill=(0, 255, 0))
        y += 16
        canvas.paste(r, (0, y)); y += r.height + 6

    cfg.figures_dir().mkdir(parents=True, exist_ok=True)
    out = args.out or str(cfg.figures_dir() / f"overlay_labels_fov{args.fov:03d}.png")
    canvas.save(out)
    print("saved", out, "| cells", cells)


if __name__ == "__main__":
    main()
