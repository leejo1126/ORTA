# ORTA wiki — index

Unified knowledge base. Schema: [[schema]] · History: [[log]] · Machine card list (agent-generated):
[index-cards.md](index-cards.md). Link with `[[slug]]`. Update this index on any add/rename.

## literature/ — source papers behind the E–P panel
| Page | Cell type | Evidence type |
|---|---|---|
| [[moorthy-2017]] | mESC (F1 129×cast) | FUNCTIONAL (deletion) |
| [[novo-2018]] | mESC | CORRELATIVE (contacts) |
| [[xie-2017-klf4]] | naive mESC | FUNCTIONAL (deletion + CRISPRi) |
| [[cheng-2023-klf4]] | mESC (KMG line) | imaging + deletion |
| [[hansen-2025-adt4221]] | mESC | FUNCTIONAL (deletion + cohesin) |
| [[eder-2025-sox2]] | mESC (F1 129/CAST) | FUNCTIONAL (synthetic relocation) |
| [[sox2-scr-classics]] | mESC | FUNCTIONAL (deletion, multi-source) |
| [[weidiao-2020-focus]] | mESC (E14) | FUNCTIONAL (deletion + 4C) |
| [[gabriele-2022-fbn2]] | mESC | BENCHMARK (looping) |
| [[tunnermann-2026-synthetic]] | mESC (synthetic) | SYNTHETIC |
| [[li-2020-imaging]] | mESC | imaging |
| [[prdm14-enhancer-insertions-2025]] | mESC (2i/LIF) | FUNCTIONAL (deletion + reporter) |

## biology/ — marker & nuclear-structure biology
- [[brd4-biology]] — BET reader at active enhancers; dense small puncta, can phase-separate `Brd4, condensate`
- [[pol2-biology]] — RNA Pol II clusters/factories; sparse foci on high diffuse background `Pol2, transcription`
- [[sc35-biology]] — SRSF2 nuclear speckles; ~tens of compact bright bodies `Sc35, speckle`
- [[dapi-biology]] — total DNA; "foci" are chromocenters/heterochromatin `DAPI, heterochromatin`
- [[lit-chromocenters]] — DAPI-dense pericentromeric heterochromatin `DAPI, reference`
- [[lit-nuclear-speckles]] — 20–50/nucleus IGCs; SC35 = SRSF2 `Sc35, reference`
- [[lit-pol2-clusters]] — Pol II clusters ~100nm, transient; count intrinsically fuzzy `Pol2, reference`
- [[lit-condensate-transcription]] — Brd4/Mediator/Pol II condensates at super-enhancers `condensate, reference`

## methods/ — foci / spot detection algorithms
- [[mean-fold-method]] — k×(in-nucleus mean) threshold + size gate + watershed (MATLAB findDensities) `mean_fold`
- [[mad-tophat-method]] — top-hat + MAD threshold + h-maxima + watershed (dense puncta) `mad, tophat`
- [[h-dome-localmax-method]] — h-domes + local-maxima seeds `h-dome, prominence`
- [[wavelet-spot-method]] — à-trous wavelet multiscale product; robust at low SNR `wavelet, SNR`
- [[log-dog-blob-method]] — Laplacian/DoG multiscale blob detection `LoG, DoG`
- [[otsu-adaptive-method]] — Otsu / adaptive threshold → CC/watershed → size gate `otsu`
- [[lit-spot-detection-benchmark]] — detector performance is SNR-dependent; wavelet best at low SNR `benchmark`
- [[lit-spot-detection-tools]] — big-fish/TrackMate (LoG); deepBlink/Piscis/Spotiflow (DL, 2D) `software`

## protocols/ — versioned wet-lab protocols
_(to author from `lab-notebook/wet-lab.md` — e.g. `if-staining`)_

## findings/ — empirical results (this project)
- [[bead-contamination]] — fiducial beads bleed into Pol2/561; Leiden cluster 10 is an artifact `Pol2, bead`
- [[brd4-foci-are-real]] — ~700 Brd4 foci/nucleus are real, not over-segmentation `Brd4`
- [[anndata-foci-crash]] — ~28M-row foci.h5ad crashes on Windows; keep foci as Parquet `anndata, parquet`
- [[native-crash-fixes]] — SMB write handle + OpenBLAS thread over-subscription fixes `crash, environment`
- [[pol2-meanfold-cliff]] — mean_fold thresholding is cliff-like on Pol2; tuning never converged `Pol2, convergence`
- [[if-fov-condition-layout]] — 198 FOVs, 184 assigned, 2-frame gaps, 8 conditions `FOV, dataset`
- [[if-data-map]] — map of every `IF/data/` artifact (grain, scale, format) `data`
- autofoci picks: [[autofoci-brd4-20260620]] · [[autofoci-pol2-20260620]] · [[autofoci-dapi-20260620]] · [[autofoci-sc35-20260620]] (and the 20260612 first pass)

## decisions/ — cross-source decisions + rationale
- [[panel-status]] — keep/drop/add/upgrade decisions vs the current E–P panel
