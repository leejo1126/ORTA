# ORTA — Optical Reconstruction of Transcriptional Architecture

Multi-modal imaging analysis of how transcription is spatially organized in the nucleus.
ORTA brings together complementary readouts of nuclear/transcriptional architecture and the
cross-analysis between them.

## Start here

| Read | For |
|---|---|
| [`OVERVIEW.md`](OVERVIEW.md) | the master map — folder structure, module status, what's active |
| [`EXPERIMENTS.md`](EXPERIMENTS.md) | every run across all modules |
| [`lab-notebook/`](lab-notebook/) | day-to-day log (bench + computational) |
| [`wiki/`](wiki/) | the knowledge base (literature, biology, methods, protocols, findings, decisions) |
| [`CLAUDE.md`](CLAUDE.md) | conventions for working in this repo |

The project is organized on two axes — **modules** (modalities) × **experiments** (dated runs under
`<module>/experiments/<ID>/`). Add either by copying a skeleton from [`_templates/`](_templates/).

## Modules

| dir | modality | status |
|-----|----------|--------|
| [`IF/`](IF/) | Immunofluorescence — 3D nuclei + per-marker foci/condensates (Brd4, Pol2, Sc35, DAPI/chromocenters) across drug perturbations, with cross-condition analysis and AnnData export | **active** |
| [`probe-design/`](probe-design/) | E–P ORCA probe / panel design (coordinates, readout scheme, dual-barcode, MATLAB probe assembly) | **active** |
| [`agents/`](agents/) | agent "dry lab" that tunes foci parameters and runs the agnostic autofoci search; emits git-tracked proposals only | **active** |
| `RNA/` | RNA (e.g. nascent transcription / FISH) readouts | planned |
| `DNA/` | DNA / genome-architecture (ORCA-style) readouts | planned |
| `cross_modality/` | registration + joint analysis across modalities | planned |
| [`docs/`](docs/) | method notes, AI-engineering workflow | active |

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
