---
name: mad-tophat-method
description: Per-slice white top-hat + MAD-relative threshold + h-maxima seeds + watershed (dense puncta)
type: method
tags:
- mad
- tophat
- watershed
- algorithm
sources: []
links:
- brd4-biology
---

**Idea.** Per-z **white top-hat** (structuring element radius ≈ spot size) removes smooth
background; a robust **MAD noise scale** is estimated from the background side of the
in-nucleus distribution (so bright foci don't inflate it); foreground = `top-hat >
noise_k × MAD`; **h-maxima** seeds (prominence `seed_h_k × MAD`) drive a **watershed** split;
min-size filter. (The other detector currently in `eporca.foci`; the tuned Brd4 default.)

**Assumptions.** Foci are small relative to the top-hat radius and brighter than a
noise-scaled local background.

**Strengths.** Excellent for **dense, punctate** markers (Brd4); local background handling
via top-hat; threshold is noise-relative (adapts per cell); watershed separates touching
puncta.

**Failure modes.** Densely packed puncta still **merge**; `tophat_radius` must match the spot
scale (too small clips real puncta, too large lets background through); low `noise_k`
produces many **specks** (over-split). Less suited to large irregular bodies (speckles).

**Key params.** `tophat_radius`, `noise_k`, `seed_h_k`, `min_size`, `blur_sigma`.
