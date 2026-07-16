# Probe / panel design — facet notebook

Computational log for the E–P ORCA probe/panel design module. Links literature decisions in
`[[wiki/decisions/panel-status]]` and coordinate sources in `[[wiki/literature]]`.
Template: `../_templates/notebook-entry.md`. Current version: `probe-design_v3`.

---

## 2026-07-16 — Panel v3 finalized (symmetric 95/95)
- **What:** Locked panel v3. Added Klf4 (E1+E2 → contiguous ~22kb `E_Klf4`) and Car2 (proximal + distal
  enhancers) with exact mm10 coordinates; simplified Cd9 to one large `E_Cd9` to free DNA readouts; gave
  `E_Cd9` an eRNA probe for symmetry. Staged Klf4 E1/E2 sub-readouts on plates 3/4 via fiducial-slot
  dual-barcode.
- **Changes:** `coordinates_v3.csv`, `readout_scheme_v3.csv`, `dual_barcode_v3.csv`, `ep_orca_v3.bed`.
- **Result:** fully symmetric panel — RNA 1–95, DNA 97–191 (95 each, ≤96/plate).
- **Why / evidence:** mm9→mm10 liftovers verified against source papers; only FUNCTIONALLY validated
  pairs qualify.
- **Links:** experiment `probe-design_v3` · `[[panel-status]]` · `[[xie-2017-klf4]]` · `[[hansen-2025-adt4221]]`.
