---
name: brd4-foci-are-real
description: High Brd4 foci counts (~700/nucleus) in the IF pipeline are biologically real, not over-segmentation — do not prune the detector
type: finding
tags: [Brd4, foci, detector, scale, biology, judgment]
sources: []
links: [anndata-foci-crash, brd4-biology, if-data-map]
---

For the IF pipeline, the very high Brd4 foci counts (~143k per FOV, ~700 per nucleus; ~90% of the
~28M-row foci table) are **biologically real**, per the user's scientific judgment (2026-07-13). Brd4
forms that many true puncta; the user believes the literature has been *underestimating* Brd4 foci
counts, not that the detector over-segments.

**Apply:** do NOT propose pruning/tightening the Brd4 detector to reduce counts or "shrink" the foci
table — the large count is the finding, not noise. Treat the ~28M-row foci table as the true data
scale (this is why the pipeline streams foci to Parquet rather than an in-memory h5ad).
See [[anndata-foci-crash]], [[brd4-biology]].
