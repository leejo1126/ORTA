# ep-orca-if

Config-driven, resumable pipeline for the EP-ORCA 4-channel immunofluorescence dataset
(Brd4 / Pol2 / Sc35 / DAPI), from raw `.dax` through nuclear segmentation, per-channel
foci/condensate detection, cross-condition analysis, and `AnnData` export.

## Pipeline

| step | module | env | output |
|------|--------|-----|--------|
| 0 | `io_zarr` | analysis | `data/zarr/fov_<NNN>.zarr` (single-scale OME-Zarr, c,z,y,x) |
| 1 | `segment` | cellpose-gpu | `data/masks/fov_<NNN>_nuclei.zarr` + `_metrics.csv` |
| 2 | `foci` | analysis | `data/foci/fov_<NNN>_c<i>.zarr` + `_per_spot.csv` (per channel) |
| 3 | `features` | analysis | `data/features/fov_<NNN>_{nuclei,foci}.parquet` |
| 4 | `analysis/*` | analysis | `data/figures/`, summary tables |
| 5 | `anndata_build` | analysis | `data/anndata/{nuclei,foci}.h5ad` |

All tunable values live in [`config/config.yaml`](config/config.yaml); the FOV→condition map
is in [`config/conditions.yaml`](config/conditions.yaml).

## Environments

Two interpreters (see [`environment-cellpose.md`](environment-cellpose.md) and
[`environment-analysis.yml`](environment-analysis.yml)):
- **analysis venv** — `S:/cluade code/EP-ORCA/.venv` (py3.13): everything except segmentation.
- **cellpose-gpu** — `C:/ProgramData/Anaconda3/envs/cellpose-gpu` (py3.10): step 1 only.

Install the package editable in both:
```
<venv>/Scripts/python.exe       -m pip install -e .[analysis]
cellpose-gpu/python.exe          -m pip install -e . --no-deps   # + zarr (pinned numpy/scipy)
```

## Running

Single step on one FOV (CLI):
```
eporca to-zarr   --config config/config.yaml --fov 0
eporca segment   --config config/config.yaml --fov 0     # cellpose-gpu python
eporca foci      --config config/config.yaml --fov 0
eporca features  --config config/config.yaml --fov 0
```

Whole dataset (Snakemake, resumable, parallel):
```
snakemake -s workflow/Snakefile --configfile config/config.yaml -j 8 --resources gpu=3
```

## Conditions

control · auxin (Rad21 depletion) · JQ1 · SGC-CBP30 · DRB · triptolide · EED226 · TSA.
See `config/conditions.yaml` for FOV ranges.
