---
name: brd4-biology
description: Brd4 — BET bromodomain reader at active enhancers; dense small nuclear puncta, can phase-separate
type: biology
tags:
- Brd4
- marker
- condensate
- morphology
sources: []
links:
- mad-tophat-method
- log-dog-blob-method
- lit-condensate-transcription
# literature-derived soft expectations (per nucleus, 3D), used by the autofoci score
expectations:
  count: [300, 1500]          # hundreds to ~1000+ dense puncta (Sabari 2018)
  eq_diam_um: [0.15, 0.7]     # near-diffraction puncta; a few larger SE condensates
  coverage: [0.02, 0.40]      # dense but excludes the nucleolus; not space-filling
---

**What it is.** Brd4 is a BET-family bromodomain protein that reads acetylated histones
and concentrates at active enhancers / super-enhancers with transcriptional machinery.
At super-enhancers it can form phase-separated condensates.

**Expected appearance (control).** Many *small, punctate* nuclear foci — typically
**hundreds to ~1000+ per nucleus** in 3D, densely distributed through the nucleoplasm
and **excluded from nucleoli**. Individual puncta are near the diffraction limit; bright
super-enhancer condensates are somewhat larger.

**Perturbation behavior.** BET inhibition (JQ1) displaces Brd4 from chromatin → fewer,
dimmer foci. A good detector should track this drop.

**Common artifacts / detection pitfalls.** Dense puncta sit close together and **merge
easily** (under-splitting) — splitting matters. Over-aggressive thresholds fragment single
puncta into specks (over-split). Label counts can exceed uint16 per FOV. The nucleolar
hole should remain empty.
