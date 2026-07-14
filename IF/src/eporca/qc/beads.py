"""Flag fiducial-bead / bright-artifact foci.

Panchromatic fiducial beads (on the coverslip, outside nuclei) bleed into the
fluorescence channels -- most into Pol2 (561 nm) and its spectral neighbour Sc35 --
and get detected as spuriously ultra-bright foci. By count they are rare (~0.5-0.8%
of Pol2 foci) but each is ~8x brighter than a real focus, so they dominate intensity
metrics (up to ~72% of a condition's Pol2 integrated intensity). They must be excluded
from per-nucleus intensity aggregates.

Beads are identified by **extreme per-marker brightness**, which -- unlike cross-channel
co-location -- is condition- and modality-independent (validated 2026-07-13: beads per
nucleus are uniform across drug conditions, CV~0.16; a co-location-gated detector was
condition-biased because it needs partner foci that transcription inhibitors deplete).

Reusable for RNA/DNA foci: set per-marker thresholds in ``config.qc.beads.max_intensity``.
The intensity distribution is bimodal (biology peak, trough, then a flat bead shelf to
detector saturation); put the threshold at the trough. Defaults calibrated for this IF
dataset: Pol2 2000, DAPI 1500 (clean gaps); Sc35 12000, Brd4 20000 (conservative -- real
speckle/Brd4 foci are genuinely bright, and beads barely bleed into the Brd4 channel).
"""

from __future__ import annotations

import pandas as pd

from ..config import Config


def flag_beads(spots: pd.DataFrame, cfg: Config) -> pd.Series:
    """Per-focus boolean Series: True = bead / ultra-bright artifact.

    A focus is a bead if its brightness (``config.qc.beads.intensity_col``) is at or
    above the per-marker threshold, optionally AND its ``eq_diam_um`` exceeds
    ``min_eq_diam_um`` (beads bloom large). Empty- and missing-column-safe; returns
    all-False when disabled, unconfigured, or the intensity column is absent.
    """
    flag = pd.Series(False, index=spots.index)
    bead = cfg.qc.beads
    if not bead.enabled or spots.empty:
        return flag
    col = bead.intensity_col
    if col not in spots.columns or "marker" not in spots.columns:
        return flag
    inten = pd.to_numeric(spots[col], errors="coerce")
    diam = (pd.to_numeric(spots["eq_diam_um"], errors="coerce")
            if bead.min_eq_diam_um is not None and "eq_diam_um" in spots.columns else None)
    for marker, thr in bead.max_intensity.items():
        sel = (spots["marker"] == marker) & (inten >= float(thr))
        if diam is not None:
            sel &= diam >= bead.min_eq_diam_um
        flag |= sel.fillna(False)
    return flag
