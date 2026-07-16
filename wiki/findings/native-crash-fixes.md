---
name: native-crash-fixes
description: Two native (non-Python) crashes in the IF anndata step — SMB write handle + OpenBLAS thread over-subscription — and their fixes
type: finding
tags: [crash, SMB, OpenBLAS, threads, segfault, windows, pipeline, environment]
sources: []
links: [anndata-foci-crash, if-data-map]
---

The IF `anndata` aggregation step (`IF/src/eporca/anndata_build.py`) suffered **native** crashes (no
Python traceback; Windows exit codes 0xC0000374 heap-corruption / 0xC0000005 access-violation /
0xC0000409 stack-overrun / POSIX 139 SIGSEGV). Diagnosed 2026-07-13 as two independent faults:

1. **Foci write to the SMB share.** Holding a `ParquetWriter`/h5py handle open on
   `//171.65.20.231/JudeData01/...` for the minutes it takes to append ~184 row groups crashes on any
   transient SMB hiccup. **Fix:** `build_foci_parquet` streams to **local disk**, then
   `shutil.copyfile` to the share in one shot (a retryable `OSError`, not a segfault). Proven: 25.8M
   rows / 1.7 GB, copy ~30 s.

2. **Embedding-step segfault.** The analysis box (`BLabServer2`) has **28 cores**, exceeding the
   precompiled OpenBLAS thread cap. Over-subscribing threads across OpenBLAS + numba (UMAP) + igraph
   (leiden) segfaults `compute_embedding`. **Fix:** cap native thread pools to 8 via
   `os.environ.setdefault` at the **top of `eporca/__init__.py`** (before numpy/OpenBLAS import):
   `OPENBLAS/OMP/MKL/NUMEXPR/BLIS/VECLIB/NUMBA _NUM_THREADS`. Proven: embedding then completes.

**Apply on this machine:** any heavy numeric step (scanpy/UMAP/BLAS) needs the thread cap set before
numpy loads; any large file written to the JudeData01 share should be built locally then copied. Don't
diagnose these as Python/memory bugs — check the **Windows native exit code first**.
See [[anndata-foci-crash]].
