---
name: wavelet-spot-method
description: À-trous wavelet multiscale-product spot detection — robust at low SNR, threshold on detail coefficients (Olivo-Marin 2002)
type: method
tags:
- wavelet
- a-trous
- multiscale
- SNR
- algorithm
sources:
- Olivo-Marin 2002, Pattern Recognition 35:1989-1996 (multiscale-product spot extraction)
- Smal et al. 2010, IEEE TMI 29:282-301
links:
- lit-spot-detection-benchmark
- pol2-biology
---

**Idea.** Compute an **à-trous (stationary) wavelet transform**; spots appear as
significant **detail coefficients across scales**. Threshold each detail level relative to
its noise (e.g. k·MAD per level) and take the **product of adjacent detail levels** to
suppress noise (correlated across scales for real spots, uncorrelated for noise); the
surviving regions are the foci. Grow/label by connected components or watershed; size-gate.

**Assumptions.** Foci are localized intensity features spanning a small range of scales,
distinguishable from noise by cross-scale correlation rather than absolute brightness.

**Strengths.** **Most robust detector at low SNR** in the Smal 2010 benchmark; background-
and illumination-tolerant; scale-aware without an explicit blob model. A strong candidate
for **dim, diffuse-background markers (Pol2)** where fold-over-mean is cliff-like.

**Failure modes.** Per-level noise threshold `k` and which detail levels to multiply must be
chosen; very large bodies (speckles/chromocenters) span more scales and may need higher
levels; can fragment large objects if only fine levels are used.

**Key params.** number of detail levels, per-level threshold `k` (×noise), which levels to
multiply, `min_size`, `max_size`, watershed on/off. Implementable from
`scipy`/`skimage` wavelet/convolution primitives (no new dependency).
