# ORTA agent wiki — index

Knowledge cards the agents consult and grow. One line per card: **title** (type) — description — `tags`.


## biology

- [brd4-biology](brd4-biology.md) — Brd4 — BET bromodomain reader at active enhancers; dense small nuclear puncta, can phase-separate `Brd4, marker, condensate, morphology`
- [dapi-biology](dapi-biology.md) — DAPI — total DNA stain; "foci" are dense chromocenters/heterochromatin, not isolated spots `DAPI, marker, heterochromatin, chromocenter, morphology`
- [pol2-biology](pol2-biology.md) — Pol2 (RNA Pol II) — transcription clusters/factories; sparse discrete foci on a high diffuse background `Pol2, marker, transcription, morphology`
- [sc35-biology](sc35-biology.md) — Sc35 (SRSF2) — canonical nuclear speckle marker; ~tens of compact irregular bright bodies `Sc35, SRSF2, marker, speckle, morphology`

## method

- [h-dome-localmax-method](h-dome-localmax-method.md) — Contrast-based extended maxima / h-domes + local-maxima seeds, grown by threshold or watershed `h-dome, h-maxima, local-maxima, prominence, algorithm`
- [log-dog-blob-method](log-dog-blob-method.md) — Multiscale Laplacian/Difference-of-Gaussian blob detection (skimage blob_log/blob_dog) — principled spot finder `LoG, DoG, blob, multiscale, algorithm`
- [mad-tophat-method](mad-tophat-method.md) — Per-slice white top-hat + MAD-relative threshold + h-maxima seeds + watershed (dense puncta) `mad, tophat, watershed, algorithm`
- [mean-fold-method](mean-fold-method.md) — Threshold at k×(in-nucleus mean) + size gating + optional intensity watershed (MATLAB findDensities port) `mean_fold, threshold, watershed, algorithm`
- [otsu-adaptive-method](otsu-adaptive-method.md) — Global Otsu or local/adaptive thresholding → connected components / watershed → size gate `otsu, adaptive, threshold, algorithm`
- [wavelet-spot-method](wavelet-spot-method.md) — À-trous wavelet multiscale-product spot detection — robust at low SNR, threshold on detail coefficients (Olivo-Marin 2002) `wavelet, a-trous, multiscale, SNR, algorithm`

## finding

- [autofoci-brd4-20260612](autofoci-brd4-20260612.md) — Agnostic autofoci search picked h_dome for Brd4 (proxy 0.902, median 324/cell) `Brd4, h_dome, autofoci`
- [autofoci-brd4-20260620](autofoci-brd4-20260620.md) — Agnostic autofoci search picked otsu_adaptive for Brd4 (proxy 0.983, median 383/cell) `Brd4, otsu_adaptive, autofoci`
- [autofoci-dapi-20260612](autofoci-dapi-20260612.md) — Agnostic autofoci search picked wavelet for DAPI (proxy 0.825, median 21/cell) `DAPI, wavelet, autofoci`
- [autofoci-dapi-20260620](autofoci-dapi-20260620.md) — Agnostic autofoci search picked wavelet for DAPI (proxy 0.971, median 11/cell) `DAPI, wavelet, autofoci`
- [autofoci-pol2-20260612](autofoci-pol2-20260612.md) — Agnostic autofoci search picked wavelet for Pol2 (proxy 0.719, median 338/cell) `Pol2, wavelet, autofoci`
- [autofoci-pol2-20260620](autofoci-pol2-20260620.md) — Agnostic autofoci search picked wavelet for Pol2 (proxy 0.910, median 25/cell) `Pol2, wavelet, autofoci`
- [autofoci-sc35-20260612](autofoci-sc35-20260612.md) — Agnostic autofoci search picked mean_fold for Sc35 (proxy 0.962, median 19/cell) `Sc35, mean_fold, autofoci`
- [autofoci-sc35-20260620](autofoci-sc35-20260620.md) — Agnostic autofoci search picked mean_fold for Sc35 (proxy 0.984, median 43/cell) `Sc35, mean_fold, autofoci`
- [pol2-meanfold-cliff](pol2-meanfold-cliff.md) — FINDING — mean_fold thresholding is cliff-like on Pol2; our tuning loop oscillated 6→75→2→56→0.5 and never converged `Pol2, mean_fold, threshold, convergence, finding`

## reference

- [lit-chromocenters](lit-chromocenters.md) — Chromocenters — DAPI-dense pericentromeric heterochromatin, cell-type-specific count (~7–18 in mouse), ~6× brighter than surroundings `DAPI, heterochromatin, chromocenter, reference`
- [lit-condensate-transcription](lit-condensate-transcription.md) — Brd4/Mediator/Pol II form liquid-like condensates at super-enhancers (Sabari 2018; Cho 2018) `Brd4, Pol2, condensate, phase-separation, reference`
- [lit-nuclear-speckles](lit-nuclear-speckles.md) — Nuclear speckles — 20–50 per nucleus, irregular µm-scale IGCs; SC35 = SRSF2 (Spector & Lamond 2011) `Sc35, SRSF2, speckle, reference`
- [lit-pol2-clusters](lit-pol2-clusters.md) — Pol II clusters are ~100 nm, transient (~8 s), often single molecules — the per-nucleus "count" is intrinsically fuzzy (Cho 2016; Cisse 2013) `Pol2, transcription, cluster, SNR, reference`
- [lit-spot-detection-benchmark](lit-spot-detection-benchmark.md) — Spot-detector performance is strongly SNR-dependent; wavelet-multiscale & supervised methods best at low SNR (Smal 2010) `spot-detection, benchmark, SNR, wavelet, method, reference`
- [lit-spot-detection-tools](lit-spot-detection-tools.md) — Modern spot tools — big-fish/TrackMate use LoG+threshold; deepBlink/Piscis/Spotiflow are DL but 2D-only (relevant to our 3D data) `spot-detection, software, LoG, deepBlink, reference`
