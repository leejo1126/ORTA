# Probe / panel design — facet notebook

Computational log for the E–P ORCA probe/panel design module. Links literature decisions in
`[[wiki/decisions/panel-status]]` and coordinate sources in `[[wiki/literature]]`.
Template: `../_templates/notebook-entry.md`. Current version: `probe-design_v2`.

---

## 2026-07-16 — Panel v2 finalized (symmetric 95/95)
- **What:** Locked panel v2. Added Klf4 (E1+E2 → contiguous ~22kb `E_Klf4`) and Car2 (proximal + distal
  enhancers) with exact mm10 coordinates; simplified Cd9 to one large `E_Cd9` to free DNA readouts; gave
  `E_Cd9` an eRNA probe for symmetry. Staged Klf4 E1/E2 sub-readouts on plates 3/4 via fiducial-slot
  dual-barcode.
- **Changes:** `coordinates_v2.csv`, `readout_scheme_v2.csv`, `dual_barcode_v2.csv`, `ep_orca_v2.bed`.
- **Result:** fully symmetric panel — RNA 1–95, DNA 97–191 (95 each, ≤96/plate).
- **Why / evidence:** mm9→mm10 liftovers verified against source papers; only FUNCTIONALLY validated
  pairs qualify.
- **Links:** experiment `probe-design_v2` · `[[panel-status]]` · `[[xie-2017-klf4]]` · `[[hansen-2025-adt4221]]`.

## 2026-07-17 — Swapped 5 Hansen pairs in for 4 low-signal Novo pairs (still 96/96)
- **What / added (5 pairs, +10 features):** functionally-validated E–P pairs from Hansen et al. supp
  (mm10): **Inhbb** (P + distal E1 + E2), **Ceacam1** (P + E, enhancer on − strand to avoid the + strand
  lncRNA), **Zbtb10** (P + E), **Prdm14** (P + E), **Sik1** (P only — shares the existing `E_Rrp1b`).
  Enhancers <10 kb auto-expanded to 10 kb (E1_Inhbb, E_Ceacam1, E_Zbtb10). Promoter DNA re-centered on the
  mm10 TSS (±5 kb); RNA on the gene body.
- **Coordinate fix:** Sik1 promoter had been given as Zbtb10's coords (copy-paste); corrected to the real
  Sik1 locus **chr17:31,855,792 (−)**, which is consistent with sharing `E_Rrp1b` (~40 kb away).
- **Dropped (4 pairs, −9 features):** **Myb**, **Senp3/Sox15**, **Srxn1**, **Ski** — all Novo-2018
  (correlative PCHi-C) pairs dropped for **low / no FISH signal** (weak or absent imaging in prior data;
  Senp3/Sox15 specifically flagged in the source sheet as "sox15 and fxr2 didn't get fished", and Ski also
  carried the +4 Mb coordinate error). Chosen per the panel guidelines (measurability > gene identity).
- **Net:** 95 → **96 features**; RNA 1–96 (plate 1), DNA 97–192 (plate 2) — both plates now exactly full.
  No new DNA overlaps; staged Klf4 sub-readouts unchanged (plates 3/4). Sik1 hubs with Rrp1b as intended.
- **Regenerated:** `results/{coordinates,readout_scheme,dual_barcode,dna_overlaps}_v2.csv`, `ep_orca_v2.bed`
  via `node generate/build.js`.
- **Links:** experiment `probe-design_v2` · `[[panel-status]]` · `[[hansen-2025-adt4221]]` · `[[novo-2018]]`.
