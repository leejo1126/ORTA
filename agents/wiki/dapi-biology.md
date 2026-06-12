---
name: dapi-biology
description: DAPI — total DNA stain; "foci" are dense chromocenters/heterochromatin, not isolated spots
type: biology
tags:
- DAPI
- marker
- heterochromatin
- chromocenter
- morphology
sources: []
links:
- otsu-adaptive-method
- mean-fold-method
---

**What it is.** DAPI binds dsDNA and stains the **entire nucleus**. The biologically
meaningful "foci" are the **densest sub-regions** — chromocenters / pericentromeric
constitutive heterochromatin — not isolated diffraction-limited spots. DAPI is also the
channel used for nuclear segmentation.

**Expected appearance (control).** **A few tens of compact, bright bodies per nucleus**
(chromocenter number is cell-type dependent), occupying a small fraction of the nuclear
volume. Nucleoli appear as **dim holes** within the bright nucleus.

**Perturbation behavior.** Chromatin-state perturbations (e.g. EED226, TSA) can alter
heterochromatin compaction → changes in chromocenter number/size.

**Common artifacts / detection pitfalls.** Because the whole nucleus is bright, the cardinal
failure is **the detector calling the whole nucleus** as one body or filling it — the
threshold must isolate the *densest* peaks above the bright bulk. Relative/local contrast
matters more than an absolute floor. Watershed usually off (chromocenters are already
separated); strict size gating helps.
