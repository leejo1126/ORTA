---
name: mean-fold-method
description: Threshold at k×(in-nucleus mean) + size gating + optional intensity watershed (MATLAB findDensities port)
type: method
tags:
- mean_fold
- threshold
- watershed
- algorithm
sources: []
links:
- sc35-biology
- dapi-biology
- pol2-meanfold-cliff
---

**Idea.** Foreground = voxels brighter than `threshold × mean(in-nucleus MIP)` and above an
absolute floor; optionally split touching bodies with an intensity watershed (h-maxima
seeds, prominence `marker_h`); drop regions outside `[min_size, max_size]`. Operates on
background-subtracted data. (This is one of the two detectors currently in `eporca.foci`.)

**Assumptions.** A meaningful, stable in-nucleus mean (so background subtraction matters);
foci are a modest fraction of the nucleus so the mean reflects background, not signal.

**Strengths.** Simple, interpretable, few knobs; good for **sparse, compact, bright** bodies
(Sc35 speckles, DAPI chromocenters, bright Pol2 clusters).

**Failure modes.** **Cliff-like** when signal is diffuse (Pol2): a small `threshold` change
flips the count between ~0 and hundreds, because the fold-over-mean cutoff crosses the broad
nucleoplasmic distribution all at once. Sensitive to the MIP-mean estimate; a few bright
foci can inflate the mean and suppress detection.

**Key params.** `threshold` (×mean), `abs_floor`, `min_size`, `max_size`, `marker_h`,
`watershed`, `blur_sigma`.
