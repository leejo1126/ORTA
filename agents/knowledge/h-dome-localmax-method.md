---
name: h-dome-localmax-method
description: Contrast-based extended maxima / h-domes + local-maxima seeds, grown by threshold or watershed
type: method
tags:
- h-dome
- h-maxima
- local-maxima
- prominence
- algorithm
sources: []
links:
- pol2-biology
- sc35-biology
---

**Idea.** Detect foci by **intensity prominence**: the h-dome transform (`skimage.morphology`
reconstruction, or `h_maxima` / `extrema.h_maxima`) keeps only maxima whose contrast above
their surroundings exceeds `h`; `peak_local_max` gives discrete seeds with a minimum spacing.
Seeds are grown by a local threshold or watershed into label volumes. (skimage built-ins;
no new dependency.)

**Assumptions.** Foci are **local intensity prominences** of contrast ≥ `h` above a
slowly-varying background — independent of absolute brightness or exact shape/scale.

**Strengths.** Scale-free and contrast-based, so robust to a high or uneven diffuse
background — a good fit for **Pol2** (where fold-over-mean is cliff-like) and for variable-size
bright bodies. The prominence `h` is intuitive and stable.

**Failure modes.** `h` too small → noise maxima counted; flat-topped or merged bodies counted
as one; `min_distance` controls splitting and can over/under-split. Needs a region-growing
step for volumes.

**Key params.** `h` (dome prominence), `min_distance` / footprint (peaks), `threshold_abs`,
and the seed→region growth method.
