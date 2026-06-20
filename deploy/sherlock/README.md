# Deploying the ORTA IF pipeline on Sherlock (Boettiger `aboettig` node)

Target: the lab's dedicated node `sh-110-12` (24 CPU / 384 GB / **no GPU**), partition
`aboettig`. Self-contained **Apptainer** image (zero interference with the lab's shared
conda/modules), **cellpose on CPU**, Snakemake parallelizing across FOVs on the one node
(resumable).

## Why these choices
- **No GPU on the node** → segmentation runs on CPU (`segmentation.use_gpu=false`, set
  automatically by `make_config.py`). It's the slow step across ~191 FOVs (hours → ~a
  day) but resumable; bump to a GPU partition later if needed (see bottom).
- **Data lives on the lab NAS**, which Sherlock nodes can't mount → stage the raw `.dax`
  to Oak first (`stage_data.sh`).
- **Isolation** → one Apptainer image; nothing on the host changes.

## Steps

1. **Get the code on Sherlock**
   ```bash
   cd $GROUP_HOME && git clone git@github.com:leejo1126/ORTA.git
   ```

2. **Stage the raw data NAS → Oak** (run on a machine that sees the NAS; edit paths first)
   ```bash
   bash ORTA/deploy/sherlock/stage_data.sh
   ```

3. **Build the image** (on Sherlock; ~20–40 min, needs network)
   ```bash
   cd $GROUP_HOME/ORTA
   apptainer build --fakeroot deploy/sherlock/eporca.sif deploy/sherlock/eporca.def
   ```

4. **Edit `run_pipeline.sbatch`** — set `REPO`, `DAX_DIR` (the Oak path from step 2),
   `DATA_DIR` (Oak or `$SCRATCH`), and `SEG_CONCURRENCY` (concurrent CPU-cellpose jobs).

5. **Submit**
   ```bash
   cd $GROUP_HOME/ORTA && sbatch deploy/sherlock/run_pipeline.sbatch
   squeue -u $USER
   tail -f logs/eporca_*.out
   ```
   Snakemake is resumable: if the job hits the walltime, just `sbatch` again — it
   continues from the last completed step.

## How it works
- `make_config.py` renders a run config from `IF/config/config.yaml`, overriding only
  paths + interpreters (`/opt/envs/{analysis,cellpose}/bin/python`) + CPU segmentation —
  so the **detector params (incl. the production Sc35) stay the single source of truth**.
- `--resources gpu=$SEG_CONCURRENCY` caps concurrent segment jobs (the Snakefile tags
  `segment` with `gpu=1`; on CPU it's just a concurrency token to avoid RAM/CPU thrash).
- Outputs land under `DATA_DIR/{zarr,masks,foci,features,anndata,figures}`; pull the
  compact results (`anndata/*.h5ad`, tables, figures) back with `rsync`/Globus.

## Tuning / scaling
- **Speed vs. RAM:** raise `SEG_CONCURRENCY` (more parallel cellpose) until RAM is tight
  (384 GB); raise `-j` for the cheap CPU steps. `OMP_NUM_THREADS` (in the `.def`) bounds
  per-process threads.
- **Smoke test first:** run a few FOVs before the full panel — temporarily set
  `acquisition.n_fovs` low, or target specific outputs, e.g.
  `snakemake ... <DATA_DIR>/features/fov_000_foci.parquet`.
- **If CPU segmentation is too slow:** route just the `segment` step to a Sherlock `gpu`
  partition. That needs converting the Snakefile `run:` rules to `shell:` (calling the
  `eporca` CLI) + the Snakemake Slurm executor so per-rule jobs go to different
  partitions — a larger change; ask and I'll wire it.

## Notes
- The `agents/` autofoci/tuning layer is **not** part of the batch pipeline and needs no
  GPU or API key here; this deploy is the deterministic `eporca` pipeline only.
- Chromatic correction is off by default (`chromatic.mode: none`); to enable, also stage
  the `beads_*` / `405_only_*` calibration files and run `eporca chromatic-calibrate`.
