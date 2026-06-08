"""
Reader for .dax movie files (Zhuang lab / STORM format).

A .dax file is raw binary image data accompanied by a sidecar .inf text file
that describes the frame dimensions, number of frames, pixel data type and
byte order. This module parses the .inf and memory-maps the .dax so large
z-stacks can be read without loading everything into RAM at once.

Example .inf contents:
    binning = 1 x 1
    data type = 16 bit integers (binary, little endian)
    frame dimensions = 2304 x 2304
    number of frames = 43
"""

from __future__ import annotations

import os
import re
import numpy as np


def _parse_inf(inf_path: str) -> dict:
    """Parse a .inf sidecar file into a dict of useful fields."""
    with open(inf_path, "r") as fh:
        text = fh.read()

    # frame dimensions = 2304 x 2304   (note: written as width x height)
    m = re.search(r"frame dimensions\s*=\s*(\d+)\s*x\s*(\d+)", text)
    if not m:
        raise ValueError(f"Could not find frame dimensions in {inf_path}")
    width, height = int(m.group(1)), int(m.group(2))

    m = re.search(r"number of frames\s*=\s*(\d+)", text)
    if not m:
        raise ValueError(f"Could not find number of frames in {inf_path}")
    n_frames = int(m.group(1))

    # endianness: "little endian" -> '<', "big endian"/"high" -> '>'
    little = ("little" in text.lower()) or ("low" in text.lower())
    endian = "<" if little else ">"
    dtype = np.dtype(endian + "u2")  # 16-bit unsigned integers

    return {
        "width": width,
        "height": height,
        "n_frames": n_frames,
        "dtype": dtype,
        "endian": endian,
    }


def read_dax(dax_path: str) -> tuple[np.ndarray, dict]:
    """
    Read a .dax file into a (n_frames, height, width) numpy array.

    Returns a tuple (data, info). The companion .inf file is expected to sit
    next to the .dax with the same basename.
    """
    inf_path = os.path.splitext(dax_path)[0] + ".inf"
    if not os.path.exists(inf_path):
        raise FileNotFoundError(f"Missing sidecar .inf for {dax_path}")

    info = _parse_inf(inf_path)
    arr = np.memmap(
        dax_path,
        dtype=info["dtype"],
        mode="r",
        shape=(info["n_frames"], info["height"], info["width"]),
    )
    return arr, info


def max_projection(dax_path: str) -> np.ndarray:
    """Return the maximum-intensity projection over the z (frame) axis."""
    arr, _ = read_dax(dax_path)
    # Cast to native byte order so downstream tools (tifffile/PIL) are happy.
    return np.asarray(arr.max(axis=0), dtype=np.uint16)


def read_dax_multichannel(dax_path: str, n_channels: int) -> tuple[np.ndarray, dict]:
    """
    Read a channel-interleaved .dax into a (n_z, n_channels, height, width) array.

    These acquisitions store one frame per channel at each z-step, in sequence,
    so the channel index is the fastest-varying axis:
        frame[i] -> channel = i % n_channels, z = i // n_channels
    """
    arr, info = read_dax(dax_path)
    n_frames = info["n_frames"]
    if n_frames % n_channels != 0:
        raise ValueError(
            f"{n_frames} frames is not divisible by {n_channels} channels in {dax_path}"
        )
    n_z = n_frames // n_channels
    reshaped = arr[: n_z * n_channels].reshape(
        n_z, n_channels, info["height"], info["width"]
    )
    info = dict(info, n_z=n_z, n_channels=n_channels)
    return reshaped, info


def max_projection_multichannel(dax_path: str, n_channels: int) -> np.ndarray:
    """
    Return per-channel max-intensity projections, shape (n_channels, height, width).
    """
    arr, _ = read_dax_multichannel(dax_path, n_channels)
    # Max over the z axis (axis 0); result is (n_channels, H, W).
    return np.asarray(arr.max(axis=0), dtype=np.uint16)
