---
name: anndata-foci-crash
description: Building the ~28M-row foci.h5ad crashes on Windows (heap corruption); foci.h5ad is write-only — keep foci as Parquet
type: finding
tags: [anndata, foci, parquet, crash, windows, scale, pipeline]
sources: []
links: [native-crash-fixes, brd4-foci-are-real, if-data-map]
---

The IF pipeline's final `anndata` rule (`IF/src/eporca/anndata_build.py`) crashed on the full 184-FOV
run (2026-07-13) with exit `0xC0000374` (Windows STATUS_HEAP_CORRUPTION) — a native crash, no Python
traceback. Snakemake then deleted both output h5ads as possibly-corrupted.

**Why:** `build_foci_anndata` concatenates all per-FOV foci parquet (~28M rows) into one DataFrame,
builds a ~28M-element Python-string index via `df.itertuples()`, then h5py-writes it; on Windows the
OOM/native path surfaces as heap corruption. The nuclei build (~37k rows) is fine.

**Key fact:** `anndata/foci.h5ad` is **written but never read** by any code — only `nuclei.h5ad` is
consumed (dimreduction). So foci.h5ad can be dropped with zero downstream breakage.

**Fix (recommended):** stop building foci.h5ad; keep foci as the per-FOV Parquet already produced
(optionally a partitioned dataset), queried lazily with DuckDB/Polars. Foci are point detections (like
spatial-omics transcripts.parquet), not a cells×features matrix — Parquet, not AnnData. Keep
`nuclei.h5ad` as AnnData. If an h5ad is ever needed at scale, use
`anndata.experimental.concat_on_disk` / `write_zarr`, not the h5py path.

The ~28M-row scale is **real** (~700 Brd4 foci/nucleus), not over-segmentation — do not prune the
detector to shrink the table. See [[brd4-foci-are-real]], [[native-crash-fixes]].
