# Legacy prototypes & the analysis venv (the `EP-ORCA/` sibling)

The `EP-ORCA/` folder that sits **next to** this repo (`S:/cluade code/EP-ORCA/`, not under
git) predates the `eporca` package. It holds:

- `scripts/` — the original prototype scripts (`cellpose_3d_nuclei.py`,
  `brd4_condensate_features.py`, `dax_reader.py`, `make_max_projection.py`) and
  `sample script/` — the MATLAB-era recipe these were ported from.
- `output/` — early one-off outputs (condensate TIFFs, max projections, masks).
- `.venv/` — **the analysis virtual environment** the pipeline currently runs on
  (`config.yaml` → `interpreters.analysis`).

## Provenance / status

Those prototypes are **superseded** by the packaged pipeline:

| legacy script | superseded by |
|---|---|
| `cellpose_3d_nuclei.py` | `eporca.segment` |
| `brd4_condensate_features.py` | `eporca.foci` + `eporca.features` |
| `dax_reader.py` | `eporca.dax_reader` |
| `make_max_projection.py` | QC helpers in `IF/scripts/qc/` |

They are kept only for provenance/reference; new work goes in `IF/src/eporca`.

## The venv

The analysis venv lives in `EP-ORCA/.venv` for historical reasons; its location is a
**config value** (`interpreters.analysis`), so the pipeline doesn't depend on the folder
layout — only on that path being correct. If the venv is ever recreated inside the repo
(`ep-orca-if/.venv`), update `interpreters.analysis` to match. The cellpose-gpu env is
separate (`C:/ProgramData/Anaconda3/envs/cellpose-gpu`) and unaffected.
