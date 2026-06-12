---
name: pol2-meanfold-cliff
description: FINDING — mean_fold thresholding is cliff-like on Pol2; our tuning loop oscillated 6→75→2→56→0.5 and never converged
type: finding
tags:
- Pol2
- mean_fold
- threshold
- convergence
- finding
sources:
- "ORTA agents runs/tuning, run 20260612T061052Z (Pol2 tuning, 5 iterations)"
links:
- pol2-biology
- lit-pol2-clusters
- mean-fold-method
- wavelet-spot-method
- h-dome-localmax-method
---

**Observed (our data, FOV 0).** Tuning the `mean_fold` detector on Pol2 toward "~10
foci/nucleus" oscillated and never converged:

| threshold | min_size | median foci |
|-----------|----------|-------------|
| 1.70 | 8  | 6  |
| 1.45 | 5  | 75 |
| 1.85 | 15 | 2  |
| 1.45 | 8  | 56 |
| 1.85 | 20 | 0.5 |

**Why.** Pol2 sits on a **high, diffuse nucleoplasmic background** (see [[pol2-biology]],
[[lit-pol2-clusters]]), so a single fold-over-mean cutoff crosses the broad background
distribution all at once — tiny threshold moves flip the count between ~0 and hundreds.
The default 1.7 (→6) was actually the closest; the search moved away from it.

**Lessons.** (1) `mean_fold` is the wrong family for diffuse markers — prefer **contrast/
prominence-based** ([[h-dome-localmax-method]]) or **wavelet** ([[wavelet-spot-method]])
detectors. (2) A fixed count target for Pol2 is itself ill-posed ([[lit-pol2-clusters]]).
(3) Any parameter search here needs **trajectory memory + bracketing/bisection**, never a
blind directional nudge, or it will oscillate.
