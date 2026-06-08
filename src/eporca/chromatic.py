"""
Chromatic-aberration correction.

Each channel is offset by a small, optics-fixed (z, y, x) shift relative to a
reference channel. Single-channel foci detection runs on native data; we correct
only when comparing positions across channels (colocalization), by shifting each
channel's centre-of-mass coordinates into the reference frame.

Offsets live in config (``chromatic.offsets_vox``, in voxels) and default to 0
until bead/fiducial calibration is available.
"""

from __future__ import annotations

import numpy as np

from .config import Config


def offset_um(cfg: Config, marker: str) -> np.ndarray:
    """Return this marker's (dz, dy, dx) chromatic offset in micrometres."""
    dz, dy, dx = cfg.chromatic.offsets_vox.get(marker, [0.0, 0.0, 0.0])
    return np.array([
        dz * cfg.acquisition.z_um,
        dy * cfg.acquisition.pixel_size_um,
        dx * cfg.acquisition.pixel_size_um,
    ], dtype=float)


def correct_coms_um(coms_zyx_um: np.ndarray, cfg: Config, marker: str) -> np.ndarray:
    """Bring (N, 3) COM coordinates (z,y,x µm) into the reference channel frame."""
    if coms_zyx_um.size == 0:
        return coms_zyx_um
    return coms_zyx_um - offset_um(cfg, marker)
