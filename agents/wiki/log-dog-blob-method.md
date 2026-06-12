---
name: log-dog-blob-method
description: Multiscale Laplacian/Difference-of-Gaussian blob detection (skimage blob_log/blob_dog) — principled spot finder
type: method
tags:
- LoG
- DoG
- blob
- multiscale
- algorithm
sources: []
links:
- brd4-biology
- pol2-biology
---

**Idea.** Scale-space blob detection: convolve with Laplacian-of-Gaussian (or
Difference-of-Gaussian) across a range of sigmas; local maxima in the (x,y,z,σ) response
give blob **centers and sizes**. `skimage.feature.blob_log` / `blob_dog` are available
(no new dependency). Blob centers become seeds; grow to label volumes via fixed-radius
spheres or a watershed seeded at the blobs.

**Assumptions.** Foci are approximately **round, Gaussian-like blobs** within a known scale
range.

**Strengths.** Principled, well-established for diffraction-limited puncta; **returns size**;
handles a range of spot sizes; robust to smooth background. Strong candidate for Brd4 puncta
and bright Pol2 clusters.

**Failure modes.** Irregular/large condensates (Sc35 speckles, DAPI chromocenters) are not
blob-like; closely packed blobs over-merge in the response; sensitive to the sigma range and
the response `threshold`. Gives points, not regions — needs a region-growing step for volumes.

**Key params.** `min_sigma`, `max_sigma`, `num_sigma`, `threshold` (or `threshold_rel`),
`overlap`; plus the seed→region growth radius/method.
