---
name: lit-spot-detection-tools
description: Modern spot tools — big-fish/TrackMate use LoG+threshold; deepBlink/Piscis/Spotiflow are DL but 2D-only (relevant to our 3D data)
type: reference
tags:
- spot-detection
- software
- LoG
- deepBlink
- reference
sources:
- FISH-quant v2, Imbert et al. 2022, RNA 28:786-795, https://pmc.ncbi.nlm.nih.gov/articles/PMC9074904/
- big-fish, https://github.com/fish-quant/big-fish
- deepBlink, Eichenberger et al. 2021, Nat Commun
links:
- log-dog-blob-method
---

Established spot-detection software: **big-FISH** (smFISH toolbox) and **TrackMate** detect
spots with **LoG + intensity thresholding**; **deepBlink** offers **threshold-independent**
deep-learning detection. Comparative tests (TrueSpot) put deepBlink, big-FISH and TrackMate
all at high F1 on simulated data.

**Implication for autofoci.** (1) **LoG + threshold** is the field-standard baseline → a
strong default arm. (2) The leading DL detectors (deepBlink, Piscis, Spotiflow) **operate on
2D images only** — our data is 3D z-stacks, so classical **3D** detectors (3D LoG/DoG,
h-dome, watershed) are the practical choice; a DL detector would require per-slice 2D
application and 3D re-linking (out of scope for the first search).
