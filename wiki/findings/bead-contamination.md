---
name: bead-contamination
description: Fiducial beads bleed into the Pol2 (561) channel and are detected as spurious in-nucleus foci; Leiden cluster 10 is a bead artifact, not biology
type: finding
tags: [Pol2, Sc35, bead, fiducial, artifact, QC, intensity]
sources: []
links: [brd4-foci-are-real, if-data-map, pol2-biology]
---

Fiducial beads (on the coverslip, physically **outside** nuclei) are very bright in ~the Pol2 (561 nm)
channel and, being so bright, bleed into the other channels — they are NOT true panchromatic
fluorophores (user correction 2026-07-14). They get detected as spurious in-nucleus foci and are the
cause of Leiden **cluster 10** ("giant Pol2 condensate", ~989 nuclei, 2.9%).

**Signature (cluster-10 medoid fov164/n1):** the offending spot is ~207× the nuclear median in Pol2
AND ~21.5× in Sc35, but not in Brd4/DAPI, and is point-like in z (bright in ~4/33 planes,
diffraction-limited). A bead = extreme brightness + cross-channel co-located bleed + point-like z;
a real Pol2 condensate is Pol2-specific and z-extended.

**Quantified across 184 FOVs (from foci.parquet):** contamination is Pol2-specific — ~2.84% of Pol2
foci are beads but carry ~24% of *integrated* Pol2 intensity (beads ~8× brighter), hitting ~18% of
nuclei. Sc35 ~1%; DAPI/Brd4 negligible. So **count** metrics are safe (per-nucleus median unchanged),
but **integrated-intensity** metrics (partition coefficient, condensed fraction) are heavily distorted.

**Resolved (2026-07-14):** after the bead filter + re-run, the triptolide "Pol2 intensity −60%" result
**survives** (Cliff's δ −0.81 → −0.86) — real biology. Median-based differentials were already
bead-robust (beads hit only ~6% of nuclei); the filter mainly cleans integrated-intensity metrics and
removes cluster-10 artifacts, and generalizes to RNA/DNA.

**Current filter (commit 328ed81):** per-marker `max_intensity` brightness cut (Pol2 2000, DAPI 1500,
Sc35 12000, Brd4 20000) in `eporca/qc/beads.py`; excluded from per-nucleus intensity aggregates. A
colocalization-gated detector would be **condition-biased** (fewer Sc35 partners under DRB/triptolide) —
a reusable filter must key on **extreme brightness + point-like morphology**, cross-channel co-location
only confirmatory.

**Deferred refinements:** (1) distance-to-nuclear-boundary (needs foci detected beyond the mask);
(2) overlapping-bright-peaks across channels as a bead score for the gray zone near the 2000 cut
(biology impact tiny, ~0.06 beads/nucleus). **Apply:** treat clusters 10 (and likely 9) as technical;
exclude from Pol2 biological conclusions.
