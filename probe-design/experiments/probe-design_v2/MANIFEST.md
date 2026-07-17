# Experiment probe-design_v2

The v2 E–P ORCA probe panel: symmetric **96 RNA + 96 DNA** features (both plates full).

- **ID:** `probe-design_v2`
- **Module:** probe-design
- **Status:** active
- **Visibility:** private
- **Date:** 2026-07-16 (rev. 2026-07-17)   **Genome build:** mm10 (GRCm38)

## What this version is
Symmetric panel — RNA readouts 1–96 (plate 1), DNA readouts 97–192 (plate 2), both plates full.
Klf4 (E1+E2 → 22 kb `E_Klf4` with staged plate-3/4 sub-readouts) and Car2 added; Cd9 simplified to one
large `E_Cd9` (+ eRNA probe for symmetry). **Rev. 2026-07-17:** added 5 Hansen-supp validated pairs
(Inhbb, Ceacam1, Zbtb10, Prdm14, Sik1; Sik1 shares `E_Rrp1b`) and dropped 4 low/no-FISH-signal Novo pairs
(Myb, Senp3/Sox15, Srxn1, Ski). Full rationale + evidence: [[panel-status]] · `lab-notebook/probe-design.md`.

## Layout (three tiers + code)
- `results/` — curated design keepers (below), each with a `results/CATALOG.md` row.
- `data/` — machine-generated probe FASTAs (gitignored; regenerate via MATLAB).
- `scratch/` — throwaway checks.
- `generate/` — the design generator `build.js` + its committed `inputs/`.
- `matlab/` — the probe-assembly driver; reusable `AssembleDualProbes.m` lives at `../../src/`.
- `config.snapshot.yaml` — frozen design + probe parameters. `NOTES.md` — run log.

## Deliverables (curated — see `results/CATALOG.md`)
| File | What it is |
|---|---|
| `results/coordinates_v2.csv` | 96 features — name, type (E/P), chr/strand, RNA-probe flag, RNA & DNA start/end, TSS + offset, note |
| `results/readout_scheme_v2.csv` | 196 rows — imaging round → block (RNA/DNA/…-sub) → plate → readout number → feature |
| `results/dual_barcode_v2.csv` | 9 zones — 5 E–P DNA overlaps + 4 staged Klf4 sub-zones; carrier/partner, partner_action, region, primary+secondary readout/plate |
| `results/dna_overlaps_v2.csv` | 5 E/P DNA overlap regions (featA/featB, chr, overlap bp) that the dual-barcode scheme resolves |
| `results/ep_orca_v2.bed` | 193 lines — RNA+DNA targets as a UCSC track (mm10), colored by E–P hub |
| `generate/build.js` | generator: inputs → the five `results/` files (`node build.js`) |
| `generate/inputs/` | committed inputs (`sheet_clean.tsv`, `promoter_tss_chosen.tsv`) |
| `matlab/EP_ORCA_v2_probes.m` | probe-assembly driver → `data/EP_ORCA_v2_{RNA,DNA}_probe.fasta` |
| `../../src/AssembleDualProbes.m` | reusable dual-barcode assembler (module-level) |
| `config.snapshot.yaml` | frozen design + probe parameters |
| `2026-07-15_e-p_coordinates.xlsx` | source coordinate spreadsheet (input) |

## Provenance
- **Config:** `config.snapshot.yaml` (design windows, primer indices, filter thresholds, plate layout).
- **How generated:** `node generate/build.js` (design) → `matlab/EP_ORCA_v2_probes.m` (probes).
- **Inputs:** literature-derived coordinates (`wiki/literature/`) + the coordinate spreadsheet above.
- **Decisions:** [[panel-status]] (append-only rationale in `wiki/log.md`).
- **Reproducibility check:** `node generate/build.js` regenerates `results/` byte-identically (2026-07-17).

## Supersedes / superseded by
- **v2 is the current design** (v1 was the prior, synthesized panel; not migrated). This was briefly
  mislabeled `probe-design_v3` — corrected to v2 because version numbers bump only on actual probe
  **synthesis**, which never happened for v2. The next revision *after v2 is synthesized* → `probe-design_v3`.
