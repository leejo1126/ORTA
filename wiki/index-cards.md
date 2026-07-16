# ORTA wiki — card index (machine-generated)

Auto-generated list of agent-readable cards (those with frontmatter `type`). The curated human index is [index.md](index.md). One line per card.


## biology

- [brd4-biology](biology/brd4-biology.md) — Brd4 — BET bromodomain reader at active enhancers; dense small nuclear puncta, can phase-separate `Brd4, marker, condensate, morphology`
- [dapi-biology](biology/dapi-biology.md) — DAPI — total DNA stain; "foci" are dense chromocenters/heterochromatin, not isolated spots `DAPI, marker, heterochromatin, chromocenter, morphology`
- [pol2-biology](biology/pol2-biology.md) — Pol2 (RNA Pol II) — transcription clusters/factories; sparse discrete foci on a high diffuse background `Pol2, marker, transcription, morphology`
- [sc35-biology](biology/sc35-biology.md) — Sc35 (SRSF2) — canonical nuclear speckle marker; ~tens of compact irregular bright bodies `Sc35, SRSF2, marker, speckle, morphology`

## method

- [h-dome-localmax-method](methods/h-dome-localmax-method.md) — Contrast-based extended maxima / h-domes + local-maxima seeds, grown by threshold or watershed `h-dome, h-maxima, local-maxima, prominence, algorithm`
- [log-dog-blob-method](methods/log-dog-blob-method.md) — Multiscale Laplacian/Difference-of-Gaussian blob detection (skimage blob_log/blob_dog) — principled spot finder `LoG, DoG, blob, multiscale, algorithm`
- [mad-tophat-method](methods/mad-tophat-method.md) — Per-slice white top-hat + MAD-relative threshold + h-maxima seeds + watershed (dense puncta) `mad, tophat, watershed, algorithm`
- [mean-fold-method](methods/mean-fold-method.md) — Threshold at k×(in-nucleus mean) + size gating + optional intensity watershed (MATLAB findDensities port) `mean_fold, threshold, watershed, algorithm`
- [otsu-adaptive-method](methods/otsu-adaptive-method.md) — Global Otsu or local/adaptive thresholding → connected components / watershed → size gate `otsu, adaptive, threshold, algorithm`
- [wavelet-spot-method](methods/wavelet-spot-method.md) — À-trous wavelet multiscale-product spot detection — robust at low SNR, threshold on detail coefficients (Olivo-Marin 2002) `wavelet, a-trous, multiscale, SNR, algorithm`

## finding

- [anndata-foci-crash](findings/anndata-foci-crash.md) — Building the ~28M-row foci.h5ad crashes on Windows (heap corruption); foci.h5ad is write-only — keep foci as Parquet `anndata, foci, parquet, crash, windows, scale, pipeline`
- [autofoci-brd4-20260612](findings/autofoci-brd4-20260612.md) — Agnostic autofoci search picked h_dome for Brd4 (proxy 0.902, median 324/cell) `Brd4, h_dome, autofoci`
- [autofoci-brd4-20260620](findings/autofoci-brd4-20260620.md) — Agnostic autofoci search picked otsu_adaptive for Brd4 (proxy 0.983, median 383/cell) `Brd4, otsu_adaptive, autofoci`
- [autofoci-dapi-20260612](findings/autofoci-dapi-20260612.md) — Agnostic autofoci search picked wavelet for DAPI (proxy 0.825, median 21/cell) `DAPI, wavelet, autofoci`
- [autofoci-dapi-20260620](findings/autofoci-dapi-20260620.md) — Agnostic autofoci search picked wavelet for DAPI (proxy 0.971, median 11/cell) `DAPI, wavelet, autofoci`
- [autofoci-pol2-20260612](findings/autofoci-pol2-20260612.md) — Agnostic autofoci search picked wavelet for Pol2 (proxy 0.719, median 338/cell) `Pol2, wavelet, autofoci`
- [autofoci-pol2-20260620](findings/autofoci-pol2-20260620.md) — Agnostic autofoci search picked wavelet for Pol2 (proxy 0.910, median 25/cell) `Pol2, wavelet, autofoci`
- [autofoci-sc35-20260612](findings/autofoci-sc35-20260612.md) — Agnostic autofoci search picked mean_fold for Sc35 (proxy 0.962, median 19/cell) `Sc35, mean_fold, autofoci`
- [autofoci-sc35-20260620](findings/autofoci-sc35-20260620.md) — Agnostic autofoci search picked mean_fold for Sc35 (proxy 0.984, median 43/cell) `Sc35, mean_fold, autofoci`
- [bead-contamination](findings/bead-contamination.md) — Fiducial beads bleed into the Pol2 (561) channel and are detected as spurious in-nucleus foci; Leiden cluster 10 is a bead artifact, not biology `Pol2, Sc35, bead, fiducial, artifact, QC, intensity`
- [brd4-foci-are-real](findings/brd4-foci-are-real.md) — High Brd4 foci counts (~700/nucleus) in the IF pipeline are biologically real, not over-segmentation — do not prune the detector `Brd4, foci, detector, scale, biology, judgment`
- [native-crash-fixes](findings/native-crash-fixes.md) — Two native (non-Python) crashes in the IF anndata step — SMB write handle + OpenBLAS thread over-subscription — and their fixes `crash, SMB, OpenBLAS, threads, segfault, windows, pipeline, environment`
- [pol2-meanfold-cliff](findings/pol2-meanfold-cliff.md) — FINDING — mean_fold thresholding is cliff-like on Pol2; our tuning loop oscillated 6→75→2→56→0.5 and never converged `Pol2, mean_fold, threshold, convergence, finding`

## reference

- [lit-chromocenters](biology/lit-chromocenters.md) — Chromocenters — DAPI-dense pericentromeric heterochromatin, cell-type-specific count (~7–18 in mouse), ~6× brighter than surroundings `DAPI, heterochromatin, chromocenter, reference`
- [lit-condensate-transcription](biology/lit-condensate-transcription.md) — Brd4/Mediator/Pol II form liquid-like condensates at super-enhancers (Sabari 2018; Cho 2018) `Brd4, Pol2, condensate, phase-separation, reference`
- [lit-nuclear-speckles](biology/lit-nuclear-speckles.md) — Nuclear speckles — 20–50 per nucleus, irregular µm-scale IGCs; SC35 = SRSF2 (Spector & Lamond 2011) `Sc35, SRSF2, speckle, reference`
- [lit-pol2-clusters](biology/lit-pol2-clusters.md) — Pol II clusters are ~100 nm, transient (~8 s), often single molecules — the per-nucleus "count" is intrinsically fuzzy (Cho 2016; Cisse 2013) `Pol2, transcription, cluster, SNR, reference`
- [if-data-map](findings/if-data-map.md) — Map of the IF pipeline's generated data artifacts — what each data/ subdir holds, its grain, scale, and format `IF, data, artifacts, parquet, zarr, anndata, pipeline`
- [if-fov-condition-layout](findings/if-fov-condition-layout.md) — IF FOV→condition layout — 198 total FOVs, 184 assigned, 2-frame gaps between 8 drug conditions `IF, FOV, conditions, layout, acquisition, dataset`
- [lit-spot-detection-benchmark](methods/lit-spot-detection-benchmark.md) — Spot-detector performance is strongly SNR-dependent; wavelet-multiscale & supervised methods best at low SNR (Smal 2010) `spot-detection, benchmark, SNR, wavelet, method, reference`
- [lit-spot-detection-tools](methods/lit-spot-detection-tools.md) — Modern spot tools — big-fish/TrackMate use LoG+threshold; deepBlink/Piscis/Spotiflow are DL but 2D-only (relevant to our 3D data) `spot-detection, software, LoG, deepBlink, reference`
