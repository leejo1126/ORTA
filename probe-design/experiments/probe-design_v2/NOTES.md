# Notes — experiment `probe-design_v2`

Run-specific log. Chronology → `../../lab-notebook/probe-design.md`; durable knowledge → `../../wiki/`.
Full design rationale (adds/drops, liftovers, staged Klf4, evidence): [[panel-status]].

## 2026-07-16 — design finalized
- 95 features (48 E / 47 P); symmetric **RNA 1–95 (plate 1)** / **DNA 97–191 (plate 2)**, both ≤96/plate.
- Promoter DNA re-centered on the true mm10 TSS (±5 kb); RNA left on the gene body. 41/45 promoters within
  <1 kb of the original coordinate; 4 flagged and resolved (Sall1, Ddx11 strand, Ski +4 Mb typo, mir290).
- **Added Klf4** — `E_Klf4` = 22 kb contiguous over E1 (69 kb, −70 %) + E2 (55 kb, −85 %); staged E1/E2
  sub-readouts parked on **plates 3/4** via the fiducial-slot dual-barcode (main panel unchanged).
- **Added Car2** — proximal (~107 kb) + distal (~168 kb) enhancers + promoter (Hansen 2025, mm10).
- **Cd9 simplified** to one large `E_Cd9` (dropped E1/E2/E3 + shared readout) to free DNA readouts;
  `E_Cd9` given an eRNA probe for symmetry (no DNA-only features remain).
- Enhancer windows <10 kb expanded to 10 kb (also existing `E_Trim71`, `E_Gabbr1`).
- 5 proximal E–P DNA overlaps resolved by the dual-barcode (carrier keeps overlap probes with A+B;
  partner's overlap probes dropped).

## 2026-07-17 — framework conformance
- Reorganized to the modules×experiments skeleton: design keepers → `results/` (+ `CATALOG.md`); probe
  FASTAs → `data/` (gitignored); generator committed under `generate/` (with `inputs/`); reusable
  `AssembleDualProbes.m` moved to module `probe-design/src/`; added `config.snapshot.yaml`.
- Verified `node generate/build.js` regenerates `results/` byte-identically from committed inputs.
