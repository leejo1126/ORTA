# <MODULE NAME> module

> Copy this whole `_templates/module/` folder to `<module>/` to add a new modality. Then fill in below,
> add a row to `../OVERVIEW.md` (module status table), and create `../lab-notebook/<module>.md`.

**Status:** planned | active | complete | superseded | archived
**One-liner:** <what this modality measures and why>

## Layout
```
<module>/
  README.md            this file
  src/  or  scripts/   the deterministic code for this modality
  config/              config template(s) — the single source of tunables
  workflow/            pipeline / driver (Snakemake or scripts)
  env/                 environment spec + pinned lockfile
  experiments/         one subdir per run: <MODULE>_<acq-date>_v<version>/
  notebooks/           exploratory notebooks (scratch analysis lives under experiments/<ID>/scratch/)
```

## How to run
<command(s) to run the pipeline for one experiment, pointing at that run's config snapshot>

## Data
Raw data location(s) (external): <path/accession>. Derived data is gitignored + regenerable.

## Related
- Wiki: `[[...]]`
- Experiments: see `../EXPERIMENTS.md`
