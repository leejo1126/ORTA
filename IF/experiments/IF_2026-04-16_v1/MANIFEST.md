# Experiment IF_2026-04-16_v1

The first full analysis run of the IF drug-perturbation dataset.

- **ID:** `IF_2026-04-16_v1`
- **Module:** IF
- **Status:** active
- **Visibility:** private
- **Date started:** 2026-04-16 (acquisition)   **Operator:** _TBD_

## Dataset
- **Raw data location:** `Z:/EPORCA/2026-04-16_IF` — interleaved `.dax` (647/561/488/405) + separate
  post-bleach `zscan_561_*` for Pol2. **NOT in git.**
- **Samples / conditions:** mESC; 198 FOVs (000–197), 8 drug conditions (see `config.snapshot.yaml`
  `conditions` / `IF/config/conditions.yaml`); ~184 FOVs assigned, 2-frame gaps between conditions.
- **Markers / channels:** Brd4 (647), Sc35 (488), DAPI (405), Pol2 (561, post-bleach). Fiducial beads
  for registration; bead brightness filter applied (`qc.beads`).
- **Acquisition:** see `../../../lab-notebook/wet-lab.md` (2026-04-16).

## Provenance
- **Config:** `config.snapshot.yaml` (this folder). Detectors: Brd4 `mad`; Pol2/DAPI `mean_fold`
  (MATLAB findDensities recipe); Sc35 `mean_fold` from autofoci run `20260620T021146Z`.
- **Derived data:** currently at the legacy `IF/data/` (referenced via `data_dir: ../../data`), gitignored
  and regenerable. Future runs write to their own `experiments/<ID>/data/`.
- **Pipeline git commit:** produced across the pre-reorg history; baseline `reorg/framework` @ HEAD.
- **Environment:** analysis venv (see `IF/env/` after the Phase 5 relocation) + cellpose-gpu for segment.

## Result
- **Headline:** first end-to-end run — 3D nuclei + 4-marker 3D foci + per-nucleus features + AnnData +
  cross-condition analysis (colocalization, differential vs control, Leiden clustering, UMAPs).
- **Keeper outputs:** see `results/CATALOG.md` (curated from `IF/data/figures/` in Phase 2a).
- **Notes / log:** `../../../lab-notebook/if-analysis.md`.

## Supersedes / superseded by
- First run; no predecessor. A re-analysis would be `IF_2026-04-16_v2`.
