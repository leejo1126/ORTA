---
name: sc35-biology
description: Sc35 (SRSF2) — canonical nuclear speckle marker; ~tens of compact irregular bright bodies
type: biology
tags:
- Sc35
- SRSF2
- marker
- speckle
- morphology
sources: []
links:
- mean-fold-method
- h-dome-localmax-method
- lit-nuclear-speckles
expectations:
  count: [20, 60]             # 20-50 speckles per nucleus (Spector & Lamond 2011)
  eq_diam_um: [0.3, 1.5]      # larger, irregular interchromatin granule clusters
  coverage: [0.01, 0.15]      # modest nuclear fraction; excludes nucleoli
---

**What it is.** Sc35 (SRSF2) is a serine/arginine-rich splicing factor and the canonical
marker of **nuclear speckles** (interchromatin granule clusters) — membraneless
compartments that store/modify splicing machinery.

**Expected appearance (control).** **~20–50 speckles per nucleus** in 3D: compact,
irregular-roundish bodies, distinctly brighter than the diffuse nucleoplasmic pool,
distributed through the nucleoplasm and **excluded from nucleoli**. Larger and fewer than
Brd4 puncta; brighter and more discrete than Pol2 clusters.

**Perturbation behavior.** Transcriptional inhibition (e.g. DRB, TSA effects) tends to
**round up and enlarge** speckles ("speckle rounding"). Detectors should tolerate a shift
toward larger, rounder bodies.

**Common artifacts / detection pitfalls.** Generally well-behaved. The main risk is
**over-splitting** large speckles into fragments under aggressive watershed; conversely
adjacent speckles can merge. This marker is the validation reference for the tuning loop.
