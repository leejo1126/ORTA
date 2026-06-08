"""
Deterministic tools the agents can call. These wrap the `eporca` pipeline so the
LLM never touches numbers directly — it picks parameters; these functions run the
detector and return measurements + a QC image for the agent to look at.

Runnable in the analysis venv (or cellpose-gpu env) where `eporca` is installed.
"""

from __future__ import annotations

import numpy as np
import scipy.ndimage as ndi
from PIL import Image, ImageDraw

from eporca.config import Config
from eporca.io_zarr import read_channel
from eporca.foci import (load_nuclear_labels_3d, detect_foci, subtract_background,
                         _expand_slices)


def _stretch(img, lo=1.0, hi=99.8):
    a, b = np.percentile(img, [lo, hi])
    if b <= a:
        b = a + 1
    return (np.clip((img.astype(np.float32) - a) / (b - a), 0, 1) * 255).astype(np.uint8)


def _colorize(gray, lab2d, rng, alpha=0.55):
    base = np.stack([gray] * 3, -1).astype(np.float32)
    out = base.copy()
    for i in np.unique(lab2d):
        if i == 0:
            continue
        m = lab2d == i
        out[m] = (1 - alpha) * base[m] + alpha * rng.integers(60, 256, 3)
    return out.astype(np.uint8)


def sample_and_qc(config_path: str, marker: str, overrides: dict | None = None,
                  fov: int = 0, cells: list[int] | None = None, n: int = 6,
                  mag: int = 4, out_png: str | None = None) -> dict:
    """Run foci detection for `marker` with `overrides` applied to its params on a
    few sample nuclei; return per-cell count stats + a QC montage path. This is the
    image analyst's core tool and the cell biologist's input."""
    cfg = Config.load(config_path)
    params = cfg.foci_params(marker).model_copy(update=overrides or {})

    raw = subtract_background(
        read_channel(cfg, fov, marker, trim=True).astype(np.float32), cfg.foci.background)
    nuc = load_nuclear_labels_3d(cfg, fov, raw.shape)
    slices = ndi.find_objects(nuc)
    if cells is None:
        counts = np.bincount(nuc.ravel()); counts[0] = 0
        cells = [int(c) for c in np.argsort(counts)[::-1][:n]]

    rng = np.random.default_rng(0)
    per_cell, panels = [], []
    for L in cells:
        sl = _expand_slices(slices[L - 1], raw.shape, (1, 8, 8))
        subnuc = nuc[sl] == L
        subraw = np.ascontiguousarray(raw[sl])
        lab = detect_foci(subraw, subnuc, params)
        per_cell.append(int(lab.max()))
        zs = np.where(subnuc.any(axis=(1, 2)))[0]
        zmid = int(zs[len(zs) // 2]) if len(zs) else subnuc.shape[0] // 2
        ov = _colorize(_stretch(subraw[zmid]), lab[zmid], rng)
        img = Image.fromarray(ov).resize((ov.shape[1] * mag, ov.shape[0] * mag), Image.NEAREST)
        ImageDraw.Draw(img).text((4, 4), f"{marker} cell {L} n3D={int(lab.max())}", fill=(255, 255, 0))
        panels.append(img)

    w = sum(p.width for p in panels) + 6 * (len(panels) - 1)
    mont = Image.new("RGB", (w, max(p.height for p in panels)), (15, 15, 15))
    x = 0
    for p in panels:
        mont.paste(p, (x, 0)); x += p.width + 6
    out_png = out_png or str(cfg.figures_dir() / f"agent_tune_{marker}.png")
    cfg.figures_dir().mkdir(parents=True, exist_ok=True)
    mont.save(out_png)

    arr = np.array(per_cell, dtype=float)
    return {
        "marker": marker, "params": params.model_dump(), "cells": cells,
        "per_cell_counts": per_cell,
        "per_cell_median": float(np.median(arr)) if arr.size else 0.0,
        "per_cell_iqr": [float(np.percentile(arr, 25)), float(np.percentile(arr, 75))]
                        if arr.size else [0.0, 0.0],
        "montage_path": out_png,
    }


def propose_config_diff(config_path: str, marker: str, params: dict) -> str:
    """Render (but do NOT apply) the YAML diff a ParamProposal would make. Applying
    to the canonical config is a human-approved step."""
    cur = Config.load(config_path).foci_params(marker).model_dump()
    lines = [f"# proposed change to foci.per_marker.{marker}:"]
    for k, v in params.items():
        lines.append(f"  {k}: {cur.get(k)!r} -> {v!r}")
    return "\n".join(lines)
