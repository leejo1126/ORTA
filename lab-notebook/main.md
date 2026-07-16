# Main lab notebook

High-level dated log (bench + computational). One block per working day; link out to facet notebooks
and experiment IDs. Newest at the bottom of each month. See `README.md` for the entry template.

---

## 2026-07-16 — Repo reorganized into the modules × experiments framework
- **What:** Restructured the project into a single ORTA umbrella repo on two axes (modules × experiments);
  added the four spines (`OVERVIEW.md`, `EXPERIMENTS.md`, `wiki/`, this notebook), `_templates/`, and the
  three-tier output scheme (`data/` · `results/`+CATALOG · `scratch/`).
- **Why:** the project had grown across two roots with duplicated code and two knowledge bases; aim is a
  future-proof layout that supports re-runs, new modules, and reproducible journal publication.
- **Links:** branch `reorg/framework` · `OVERVIEW.md`.

## 2026-07-16 — Probe panel v3 finalized
- **What:** Locked E–P ORCA probe panel v3 — symmetric 95 RNA + 95 DNA; added Klf4 and Car2 (mm10 coords
  resolved from literature, mm9→mm10 liftovers checked); simplified Cd9.
- **Links:** experiment `probe-design_v3` · [probe-design](probe-design.md) · `[[panel-status]]`.

---

## 2026-06-20 — Autofoci search, second pass
- **What:** Re-ran the agnostic autofoci search across all four markers; adopted Sc35 mean_fold detector
  from the run; confirmed Brd4/Pol2/DAPI keep the hand-tuned (MATLAB findDensities) recipes.
- **Links:** [autofoci](autofoci.md) · `[[autofoci-sc35-20260620]]` · experiment `IF_2026-04-16_v1`.

## 2026-06-12 — Autofoci search, first pass + bead QC
- **What:** First agnostic autofoci search; identified the Pol2 mean_fold "cliff"; added the fiducial-bead
  brightness filter (beads bleed into Pol2/561).
- **Links:** [autofoci](autofoci.md) · [if-analysis](if-analysis.md) · `[[pol2-meanfold-cliff]]`.

---

## 2026-04-16 — IF imaging session (raw acquisition)
- **What:** Imaged the IF drug-perturbation panel — 198 FOVs, 4 markers (Brd4 647, Sc35 488, DAPI 405,
  Pol2 561 post-bleach), 8 drug conditions.
- **Result:** raw `.dax` at `Z:/EPORCA/2026-04-16_IF` → consumed by experiment `IF_2026-04-16_v1`.
- **Links:** [wet-lab](wet-lab.md) (bench/protocol details — to be filled) · [if-analysis](if-analysis.md).
