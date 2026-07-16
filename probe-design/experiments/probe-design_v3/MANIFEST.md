# Experiment probe-design_v3

The v3 E–P ORCA probe panel (finalized 2026-07-16): symmetric 95 RNA + 95 DNA features.

- **ID:** `probe-design_v3`
- **Module:** probe-design
- **Status:** complete
- **Visibility:** private
- **Date:** 2026-07-16   **Genome build:** mm10 (GRCm38)

## What this version is
Symmetric panel — RNA readouts 1–95, DNA readouts 97–191 (≤96/plate). Klf4 and Car2 added with
exact mm10 coordinates (mm9→mm10 liftovers verified); Cd9 simplified to one large `E_Cd9` to free DNA
readouts; `E_Cd9` given an eRNA probe for symmetry. Klf4 E1/E2 sub-readouts staged on plates 3/4 via
fiducial-slot dual-barcode. Full rationale + evidence: [[panel-status]] · `lab-notebook/probe-design.md`.

## Deliverables (this version's catalog)
| File | What it is |
|---|---|
| `coordinates_v3.csv` | 94 features — name, type (E/P), chr/strand, RNA-probe flag, RNA & DNA start/end, TSS + offset, note |
| `readout_scheme_v3.csv` | 193 rows — imaging round → block (RNA/DNA) → plate → readout number → feature |
| `dual_barcode_v3.csv` | 8 overlap zones — carrier/partner features, partner action (drop), region, primary+secondary readout/plate |
| `dna_overlaps_v3.csv` | 4 E/P DNA overlap regions (featA/featB, chr, overlap bp) that the dual-barcode scheme resolves |
| `ep_orca_v3.bed` | 190 lines — RNA+DNA targets as a UCSC track (mm10), colored by E–P hub |
| `matlab/EP_ORCA_v3_probes.m` | probe design/assembly script |
| `matlab/AssembleDualProbes.m` | dual-barcode probe assembly |
| `2026-07-15_e-p_coordinates.xlsx` | source coordinate spreadsheet (input) |

## Provenance
- Inputs: literature-derived coordinates (see `wiki/literature/`), the coordinate spreadsheet above.
- Decisions: [[panel-status]] (append-only rationale in `wiki/log.md`).

## Supersedes / superseded by
- v3 supersedes v1/v2 (not migrated). A next revision would be `probe-design_v4`.
