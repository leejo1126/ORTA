# IF image analysis — facet notebook

Computational log for the immunofluorescence module. Deeper detail than `main.md`; link experiment IDs,
`results/` outputs, and `[[wiki]]` pages. Template: `../_templates/notebook-entry.md`.

Pipeline (all keyed off `IF/config/config.yaml`): raw `.dax` → OME-Zarr → 3D Cellpose nuclei →
per-marker 3D foci → features → AnnData → cross-condition analysis. Current run: `IF_2026-04-16_v1`.

---

## 2026-06-20 — Sc35 detector adopted from autofoci
- **What:** Set the Sc35 foci detector to the autofoci `mean_fold` pick (run `20260620T021146Z`), anchored
  to the literature ~20–60 speckles/nucleus (median ~43 on FOV 0).
- **Changes:** `foci.per_marker.Sc35` in config → `mean_fold`, threshold 1.789, etc.
- **Links:** `[[autofoci-sc35-20260620]]` · [autofoci](autofoci.md).

## 2026-06-12 — Bead contamination QC
- **What:** Added the fiducial-bead brightness filter — beads bleed into the Pol2 (561) channel and
  dominate intensity aggregates. Per-marker `max_intensity` thresholds sit at the biology/bead trough.
- **Changes:** `qc.beads` config block; `eporca.qc.beads`.
- **Links:** `[[bead-contamination]]`.

## (ongoing) — Detector choices per marker
- Brd4 = `mad` (top-hat + h-maxima + watershed); Pol2/DAPI = `mean_fold` (MATLAB findDensities recipe);
  Sc35 = autofoci `mean_fold`. High Brd4 counts (~700/nucleus) are real biology, not over-segmentation.
- **Links:** `[[brd4-foci-are-real]]` · `[[pol2-meanfold-cliff]]`.
