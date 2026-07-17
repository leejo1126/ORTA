# ORTA — project overview (master map)

**ORTA** (*Optical Reconstruction of Transcriptional Architecture*) — multi-modal imaging analysis of
how transcription is spatially organized in the nucleus. This file is the **single map** of the repo:
what every folder holds, each module's status, and what's active right now. Update it whenever the
layout or focus shifts.

> The four "spines" of the project — keep them current:
> | Spine | File | Answers |
> |---|---|---|
> | **Structure + status** | `OVERVIEW.md` (this file) | what exists, each module's state, what's active |
> | **Runs** | [`EXPERIMENTS.md`](EXPERIMENTS.md) | every experiment, its dataset, status, headline result |
> | **Knowledge** | [`wiki/index.md`](wiki/index.md) | what we know (biology, methods, protocols, findings, decisions) |
> | **Chronology** | [`lab-notebook/main.md`](lab-notebook/main.md) | what happened day to day (bench + computational) |

## How the project is organized — two axes

- **Modules** = modalities / workstreams (IF, probe-design, RNA, DNA, cross_modality). Each is a
  self-contained folder with the **same internal skeleton** (`_templates/module/`). Add one by copying
  the template.
- **Experiments** = dated *runs* of a module against a specific dataset/version, under
  `<module>/experiments/<ID>/`. Each carries its own config snapshot + `MANIFEST.md` and writes to its
  own output dir, so re-analysis never overwrites a prior run.
  **Experiment ID:** `<MODULE>_<acq-date>_v<analysis-version>` (e.g. `IF_2026-04-16_v1`).

**Lifecycle status** (used here, in `EXPERIMENTS.md`, and in module READMEs):
`planned → active → complete → superseded → archived`.

## Folder map

```
OVERVIEW.md          this file — structure + status
EXPERIMENTS.md       registry of every run across all modules
CLAUDE.md            working instructions for Claude (where things live, conventions, gotchas)
_templates/          copy-me skeletons: module/, experiment/, wiki-page, notebook-entry, decision, results-catalog, figure-sidecar
lab-notebook/        two-tier notebook (bench + computational)
  main.md            high-level dated log → links to facet notebooks
  wet-lab.md         bench work: procedures, protocol changes, reagents, imaging sessions
  if-analysis.md  probe-design.md  autofoci.md    dry-lab facets
wiki/                unified llm-wiki: literature/ biology/ methods/ protocols/ findings/ decisions/
IF/                  immunofluorescence module (ACTIVE) — src/eporca pipeline, Snakemake, config, experiments/
probe-design/        E–P probe / panel design (ACTIVE) — coordinates, readout scheme, MATLAB
agents/              agent "dry lab" (judgment layer): tuning/autofoci search, personas, runs
deploy/sherlock/     HPC (Sherlock) deployment
docs/                engineering method notes (architecture, ai-engineering)
publication/         publication view: Figure N → experiment ID → results CATALOG → script
archive/             superseded code kept for provenance, mapped to its successor
RNA/ DNA/ cross_modality/    planned sibling modules (skeleton stubs)
```

## Module status

| Module | Status | What it is |
|---|---|---|
| `IF/` | **active** | 3D nuclei + per-marker foci/condensates (Brd4, Pol2, Sc35, DAPI) across drug perturbations → features → AnnData → cross-condition analysis |
| `probe-design/` | **active** | E–P ORCA probe/panel design (v2): coordinates, readout scheme, dual-barcode, MATLAB probe assembly |
| `agents/` | **active** | LLM agents that tune foci parameters / run the agnostic autofoci search; emit git-tracked proposals only |
| `RNA/` | planned | nascent transcription / FISH readouts |
| `DNA/` | planned | genome-architecture (ORCA-style) readouts |
| `cross_modality/` | planned | registration + joint analysis across modalities |

## Currently working on

- **Repo reorganization** into this modules × experiments framework (branch `reorg/framework`). See
  the plan and `lab-notebook/main.md` for the running status.
- IF: current run is `IF_2026-04-16_v1` (see [`EXPERIMENTS.md`](EXPERIMENTS.md)).

## Data policy

Code lives in git; **raw imaging data does not** (hundreds of GB, external drives). Derived data is
gitignored and fully regenerable from raw `.dax` + a run's `config.snapshot.yaml`. Deposition targets
are tracked in [`docs/data-availability.md`](docs/data-availability.md).
