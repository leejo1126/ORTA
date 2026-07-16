# archive/

Superseded code kept for provenance only — **do not import or run**. Each prototype here was an early
standalone script (from the pre-reorg `EP-ORCA/` workspace) that has since been reworked into the
maintained `IF/src/eporca/` package. Listed with its successor.

## prototypes/ → successor in `IF/src/eporca/`

| Archived prototype | Superseded by | What it did |
|---|---|---|
| `dax_reader.py` | `IF/src/eporca/dax_reader.py` | read `.dax` + `.inf` acquisition files |
| `cellpose_3d_nuclei.py` | `IF/src/eporca/segment.py` | 3D Cellpose nuclei segmentation |
| `cellpose_dapi_masks_2d_prototype.py` | `IF/src/eporca/segment.py` | earlier **2D** Cellpose DAPI-mask prototype (was `EP-ORCA/sample script/`) |
| `brd4_condensate_features.py` | `IF/src/eporca/features.py` (+ `foci.py`) | per-condensate/foci feature extraction |
| `make_max_projection.py` | `IF/src/eporca/io_zarr.py` + `scripts/qc/` | max-intensity projections for QC |

The maintained code is config-driven and run via the Snakemake pipeline (`IF/workflow/Snakefile`);
these scripts predate that and hardcode paths. Retained so the lineage of the current pipeline is
traceable for the methods write-up.
