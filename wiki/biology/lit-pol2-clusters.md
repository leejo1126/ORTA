---
name: lit-pol2-clusters
description: Pol II clusters are ~100 nm, transient (~8 s), often single molecules — the per-nucleus "count" is intrinsically fuzzy (Cho 2016; Cisse 2013)
type: reference
tags:
- Pol2
- transcription
- cluster
- SNR
- reference
sources:
- Cho et al. 2016, eLife 5:e13617, https://elifesciences.org/articles/13617
- Cisse et al. 2013, Science 341:664-667 (super-resolution Pol II clustering)
links:
- pol2-biology
- pol2-meanfold-cliff
---

RNA Pol II forms **clusters ~100 nm wide that are short-lived (lifetime ~8 s)**; cluster
dynamics predict mRNA output (Cho 2016). Super-resolution work shows many "transcription
foci" comprise only a single Pol II molecule, on a high diffuse background.

**Implication for detection (important).** The per-nucleus **count of Pol II foci is not a
hard biological constant** — it depends on SNR, threshold, and what counts as a "cluster."
This is *why* a fixed target band (e.g. "~10/nucleus") is the wrong yardstick for Pol II,
and why fold-over-mean thresholding is cliff-like here (see [[pol2-meanfold-cliff]]). An
agnostic detector should be judged on **stable, well-contrasted clusters** and reproducible
behavior, not on hitting a preset number.
