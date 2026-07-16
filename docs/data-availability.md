# Data availability plan

What gets deposited where at publication. Code lives in git; data does not. Accessions are filled in at
submission. Builds on the deposition intent in the top-level README.

| Artifact | Size | Target archive | Access | Accession |
|---|---|---|---|---|
| Raw imaging (`.dax` + `.inf`) | ~hundreds of GB | BioImage Archive / IDR (or EMPIAR) | public at publication | TBD |
| Packaged OME-Zarr (`IF/data/packaged/*.ome.zarr`) | large | BioImage Archive | public at publication | TBD |
| `nuclei.h5ad` (primary analysis object) | ~modest | Zenodo / Figshare | public, DOI | TBD |
| Foci table (`foci.parquet`) + per-nucleus feature tables | ~GB | Zenodo / Figshare | public, DOI | TBD |
| Curated figures + tables (`experiments/<ID>/results/`) | small | in the code repo + Zenodo snapshot | public | (in repo) |
| Probe/panel design (`probe-design/`) | small | in the code repo | public | (in repo) |
| Code (this repo) | — | GitHub + Zenodo release | public, DOI | TBD |

## Notes
- **Derived data is regenerable** from raw + a run's `config.snapshot.yaml` (see `REPRODUCE.md`), so only
  raw + primary analysis objects strictly need deposition; the rest is convenience.
- **Licenses:** code license TBD (see `release-manifest.md`); data under a permissive data license
  (e.g. CC-BY) — confirm with any data-sharing agreements.
- **What is public vs private** is enumerated in `release-manifest.md` (per-module / per-experiment
  `visibility`).
