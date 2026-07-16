---
name: otsu-adaptive-method
description: Global Otsu or local/adaptive thresholding → connected components / watershed → size gate
type: method
tags:
- otsu
- adaptive
- threshold
- algorithm
sources: []
links:
- dapi-biology
---

**Idea.** Pick the foreground threshold from the data: **global Otsu**
(`skimage.filters.threshold_otsu`) when the histogram is bimodal, or **local/adaptive**
thresholding (`threshold_local`) for uneven background; label connected components (or an
intensity watershed to split touching bodies); drop regions outside `[min_size, max_size]`.
(skimage built-ins; no new dependency.)

**Assumptions.** A separable foreground/background intensity distribution — global Otsu needs
a genuinely **bimodal** histogram; adaptive needs the foreground to be locally brighter than
its neighborhood.

**Strengths.** **Parameter-light** (global Otsu has no knobs) and data-driven; adaptive
handles uneven illumination. Reasonable for **DAPI chromocenters** (dense bright regions on a
bright but separable bulk) and other markers with clear bimodality.

**Failure modes.** Breaks when the foreground is a **small fraction** or the histogram is
**unimodal** (sparse foci → Otsu threshold lands in noise → over-detect, or in signal →
miss). Global Otsu is poor for diffuse markers (Pol2). Adaptive's `block_size`/`offset`
strongly shape results.

**Key params.** global Otsu: none; adaptive: `block_size`, `offset`, `method`; plus
`min_size`, `max_size`, `watershed`.
