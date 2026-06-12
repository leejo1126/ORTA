# ORTA architecture

ORTA is an umbrella for multi-modal imaging analysis of nuclear/transcriptional
architecture. The repo separates a **deterministic numerical core** from an **agent
judgment layer**, and keeps code in git while data stays out.

## Repo map

```
ep-orca-if/
  IF/                      # the immunofluorescence modality (active module)
    src/eporca/            # the pipeline package (installed editable)
      io_zarr, segment, foci, features, anndata_build, chromatic, registration,
      analysis/, autofoci/ # autofoci/ = deterministic core of the agnostic search
    config/                # config.yaml (single source of tunables) + conditions.yaml
    workflow/              # Snakemake DAG
    scripts/qc/            # QC + 3D viewers (napari, Fiji TIFF export, overlays)
    scripts/pipeline/      # whole-dataset driver
    env/                   # environment specs (analysis venv + cellpose-gpu)
    data/                  # gitignored; regenerable from raw .dax + config
  agents/                  # the agent "dry lab" (judgment layer)
    core/                  # wiki (knowledge), tools, schemas, llm helper
    tuning/                # guided foci-tuning loop
    autofoci/              # agnostic multi-algorithm search (arm scheduler)
    personas/  knowledge/  runs/
  docs/                    # this folder
  RNA/  DNA/  cross_modality/   # planned sibling modules under the umbrella
```

## Two layers

- **Deterministic core (`IF/src/eporca`)** — all numbers: OME-Zarr conversion, 3D nuclei
  (Cellpose), per-channel foci/condensate detection, features, AnnData, cross-condition
  analysis. Reproducible from `config.yaml`. `eporca.autofoci` adds the spec DSL + detector
  primitives + proxy metrics the search optimizes — still deterministic, no LLM.
- **Agent judgment layer (`agents/`)** — LLM agents that tune parameters, search algorithms,
  and interpret results. They read the **wiki** for grounding and only ever emit git-tracked
  **proposals** (config diffs / proposed specs); humans approve before anything touches
  `config.yaml` or a full-batch run. See [ai-engineering.md](ai-engineering.md).

## Data flow

raw `.dax` → OME-Zarr (`io_zarr`) → 3D nuclei (`segment`) → per-channel foci (`foci`) →
features (`features`) → `AnnData` (`anndata_build`) → analysis. Foci detection is the step
the agents help tune/search; everything is keyed off `config.yaml`.
