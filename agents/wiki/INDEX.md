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
