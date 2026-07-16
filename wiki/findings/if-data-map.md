---
name: if-data-map
description: Map of the IF pipeline's generated data artifacts — what each data/ subdir holds, its grain, scale, and format
type: reference
tags: [IF, data, artifacts, parquet, zarr, anndata, pipeline]
sources: []
links: [if-fov-condition-layout, anndata-foci-crash, native-crash-fixes]
---

All IF derived data lives under `IF/data/` on the JudeData01 share
(`//171.65.20.231/JudeData01/cluade code/ep-orca-if/IF/data/`). Code is git-tracked; data is not
(regenerable from raw `.dax` + the run's config via `IF/workflow/Snakefile`).

**Flow:** `.dax` → **zarr** (OME-Zarr image) → **masks** (nuclei) + **foci** (per-marker spots) →
**features** (tidy Parquet) → **anndata** (`nuclei.h5ad`) → **figures**.

**Per-FOV** (184 assigned FOVs — see [[if-fov-condition-layout]]):
- `zarr/fov_NNN.zarr` — multi-channel 3D image (Brd4/647, Sc35/488, DAPI/405, Pol2/561). Input to all.
- `masks/fov_NNN_nuclei.zarr` — 3D nucleus label mask (Cellpose); `..._nuclei_metrics.csv` — per-nucleus QC.
- `foci/fov_NNN_c{i}_{marker}.zarr` — 3D foci label mask per marker; `..._per_spot.csv` — one row/focus.
- `features/fov_NNN_nuclei.parquet` — tidy per-nucleus features (~200/FOV → ~37k total).
- `features/fov_NNN_foci.parquet` — tidy per-focus table (~155k/FOV → ~28M total; ~90% Brd4).

**Aggregate / derived:**
- `anndata/nuclei.h5ad` — **primary** analysis object (~37k nuclei × features, z-scored X, obsm['spatial'],
  PCA/UMAP/leiden). The only h5ad downstream reads.
- `anndata/foci.parquet` — ~28M-row streamed foci table (replaces the write-only foci.h5ad, see
  [[anndata-foci-crash]]).
- `figures/` — QC/analysis PNGs (incl. `agent_tune_*` montages); `_analysis.done` sentinel. Curated
  keepers for a run live in that run's `results/` instead.

**Calibration/support:** `chromatic/calibration.npz`; `registration/fov_NNN.json` (+ `_qc.png`);
`packaged/fov_NNN.ome.zarr` (single OME-NGFF store bundling image + labels, for napari/Fiji + deposition).

**Grain:** FOV → zarr, masks, packaged. Nucleus → metrics.csv, nuclei.parquet, nuclei.h5ad.
Focus → per_spot.csv, foci/*.zarr, foci.parquet.
