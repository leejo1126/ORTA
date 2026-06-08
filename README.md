# ORTA — Optical Reconstruction of Transcriptional Architecture

Multi-modal imaging analysis of how transcription is spatially organized in the nucleus.
ORTA brings together complementary readouts of nuclear/transcriptional architecture and the
cross-analysis between them.

## Modules

| dir | modality | status |
|-----|----------|--------|
| [`IF/`](IF/) | Immunofluorescence — 3D nuclei + per-marker foci/condensates (Brd4, Pol2, Sc35, DAPI/chromocenters) across drug perturbations, with cross-condition analysis and AnnData export | **active** |
| `RNA/` | RNA (e.g. nascent transcription / FISH) readouts | planned |
| `DNA/` | DNA / genome-architecture (ORCA-style) readouts | planned |
| `cross_modality/` | registration + joint analysis across modalities | planned |
| `agents/` | multi-agent "lab" (cell-biologist / image-analyst / computational-biologist / PI) that tunes parameters, runs analyses, and interprets results | planned |
| `docs/` | method notes, AI-engineering workflow | planned |

## IF pipeline (current)

A config-driven, resumable Snakemake pipeline: raw `.dax` → OME-Zarr → 3D Cellpose nuclei →
per-nucleus 3D foci detection → feature assembly → cross-condition analysis → `AnnData`.
See [`IF/README.md`](IF/README.md) for details and how to run it.

## Data

Code lives here; **data does not** (raw imaging ~hundreds of GB). Derived data is fully
regenerable from raw `.dax` + `config.yaml` via the pipeline. Deposition plan: compact results
(`AnnData`, tables, figures) → Zenodo/Figshare with a DOI; large imaging (raw + OME-Zarr) →
BioImage Archive / object storage at publication.

## How this is built

ORTA is developed with an agentic engineering workflow (the Claude Code harness for
implementation, and a planned in-repo multi-agent layer for parameter tuning, analysis, and
interpretation). The deterministic numerical core stays as reproducible code; agents operate at
the judgment layer (QC, tuning, hypothesis generation) and only ever propose git-tracked
config/code changes.
