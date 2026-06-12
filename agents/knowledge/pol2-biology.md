---
name: pol2-biology
description: Pol2 (RNA Pol II) — transcription clusters/factories; sparse discrete foci on a high diffuse background
type: biology
tags:
- Pol2
- marker
- transcription
- morphology
sources: []
links:
- h-dome-localmax-method
- wavelet-spot-method
- log-dog-blob-method
- pol2-meanfold-cliff
- lit-pol2-clusters
---

**What it is.** RNA Polymerase II forms transient transcription "factories" / clusters
(phospho-CTD Ser5/Ser2). The discrete clusters sit on top of a substantial **diffuse
nucleoplasmic background** of unengaged polymerase.

**Expected appearance (control).** **Sparse, discrete** foci — on the order of **~10
prominent clusters per nucleus** (more if dimmer clusters are counted). Not space-filling.

**Perturbation behavior.** Transcription inhibitors (DRB, triptolide) reduce/redistribute
clusters. In this dataset Pol2 is imaged on a **separate 561 acquisition** (the interleaved
561 suffers 647/Brd4 bleed-through) and needs bead registration to align with the other
channels — relevant to cross-channel analysis, not to detecting Pol2 foci themselves.

**Common artifacts / detection pitfalls.** The high diffuse background makes thresholding
**cliff-like**: too low → the whole nucleoplasm lights up (over-detect, hundreds of noise
calls); too high → almost nothing (under-detect). Contrast/prominence-based detectors are
more stable here than a single global fold-over-mean. See [[pol2-meanfold-cliff]].
