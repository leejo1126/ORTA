# Generator — probe-design_v2

`build.js` produces this experiment's coordinate + readout design (everything in `../results/`) from the
committed inputs in `inputs/`. Pure Node.js, no network. Parameters are documented in `../config.snapshot.yaml`.

## Run
```
node build.js      # writes ../results/{coordinates,readout_scheme,dual_barcode,dna_overlaps}_v2.csv + ep_orca_v2.bed
```
Location-independent (paths derived from the script dir). Regeneration is byte-stable for identical inputs.

## Inputs (`inputs/`, committed)
- **`sheet_clean.tsv`** — the source spreadsheet `../2026-07-15_e-p_coordinates.xlsx` exported to TSV via
  Excel COM: `name, chr, start, end, strand` for the 92 base E/P features.
- **`promoter_tss_chosen.tsv`** — chosen TSS per promoter: the closest `basic`-tagged transcript TSS to each
  sheet coordinate from **Ensembl GRCm38.87 (mm10)** GTF. Offsets >1 kb were flagged and resolved
  (Sall1 −9.8 kb, Ddx11 strand fix, Ski +4 Mb typo, mir290 provisional). See `../../../lab-notebook/probe-design.md`.

## What it encodes
Promoter DNA re-centered on TSS (±5 kb, RNA left on the gene body); enhancer windows expanded to ≥10 kb;
Klf4 + Car2 added (Klf4 E1+E2 as one 22 kb window with staged plate-3/4 sub-readouts); Cd9 simplified to one
large `E_Cd9`; readout order (enhancers first → chr round-robin → bad toeholds last); the dual-barcode overlap
zones and the staged Klf4 zones. Full rationale: [[panel-status]].

## Regenerating the inputs from scratch (rarely needed)
Re-export the xlsx to TSV (Excel COM), then re-run the GTF TSS-selection pipeline (awk over the GRCm38.87
transcripts, picking the closest basic protein-coding TSS per promoter). Both steps are logged in the
probe-design notebook facet.
