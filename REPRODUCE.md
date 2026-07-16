# Reproducing the results

Every curated figure traces to a run: `figure → results/CATALOG → experiment ID → config.snapshot.yaml
→ git commit → raw data`. To regenerate one, reproduce its run.

## 1. Environment
```
# analysis env (everything except cellpose segmentation)
python -m venv .venv
.venv/Scripts/python -m pip install -r IF/env/requirements.lock
.venv/Scripts/python -m pip install -e IF
# segmentation env (GPU): see IF/env/environment-cellpose.md
```
Point `interpreters.analysis` (and `.cellpose`) in the run's `config.snapshot.yaml` at these interpreters.

## 2. Data
Raw imaging is deposited separately (see [docs/data-availability.md](docs/data-availability.md)); set the
run's `paths.dax_dir` to your local copy. Derived data is regenerable — you do not need to download it.

## 3. Run a pipeline (regenerates that run's data/ + figures)
```
snakemake -s IF/workflow/Snakefile \
  --config cfg=IF/experiments/<ID>/config.snapshot.yaml \
  -j 8 --resources gpu=1
```
Outputs land in `IF/experiments/<ID>/data/`. Curated keepers are in `IF/experiments/<ID>/results/`
(each documented in `results/CATALOG.md`).

## Figure → command
See [publication/figures.md](publication/figures.md) for the Figure N → experiment ID → generation
command mapping (populated at manuscript time).

## Determinism
Detector params, seeds (`analysis.random_seed`), and thread caps are fixed in the config; on this host,
native thread pools are capped in `eporca/__init__.py` (see the `native-crash-fixes` wiki finding).
