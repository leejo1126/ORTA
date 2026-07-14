"""eporca: EP-ORCA immunofluorescence analysis pipeline.

Only lightweight modules (config, dax_reader) are imported here so that
`import eporca` works in both the cellpose-gpu and analysis environments.
Heavy modules (segment, foci, analysis.*) are imported on demand.
"""

import os as _os

# Cap native thread pools BEFORE numpy/OpenBLAS/numba load. The analysis box has 28
# cores, which exceeds the precompiled OpenBLAS thread cap (it warns "set
# OPENBLAS_NUM_THREADS to 24 or lower" and takes an unstable auxiliary-array path);
# over-subscribing threads across OpenBLAS + numba (UMAP) + igraph (leiden) segfaults
# the embedding step (SIGSEGV / Windows 0xC0000409). setdefault so an explicit override wins.
for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS",
           "NUMEXPR_NUM_THREADS", "BLIS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS",
           "NUMBA_NUM_THREADS"):
    _os.environ.setdefault(_v, "8")

from .config import Config

__all__ = ["Config"]
__version__ = "0.1.0"
