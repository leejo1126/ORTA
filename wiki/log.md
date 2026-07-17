# Wiki log

Append-only. One line per operation: `YYYY-MM-DD  OP  detail`.

2026-07-16  INIT     Created unified ORTA wiki skeleton (schema + index + domains) on branch reorg/framework.
2026-07-16  MIGRATE  Moved 25 agent cards from agents/knowledge/ into wiki/{biology(8),methods(8),findings(9)} (git mv, history preserved); removed agents/knowledge/INDEX.md.
2026-07-16  MIGRATE  Copied 11 source papers from EP-ORCA/literature/ into wiki/literature/; panel-status into wiki/decisions/.
2026-07-16  INGEST   Authored 6 new findings/reference pages from project memory: bead-contamination, brd4-foci-are-real, anndata-foci-crash, native-crash-fixes, if-fov-condition-layout, if-data-map.
2026-07-16  REPOINT  agents/core/wiki.py now reads wiki/ recursively; machine card list -> wiki/index-cards.md (curated index.md untouched). Verified: 31 cards load, expectations(Brd4) resolves.
2026-07-17  LINT    Corrected [[panel-status]] Klf4 row: E_Klf4 is a 22 kb contiguous window over E1+E2 with staged plate-3/4 sub-readouts (was stale "Xie E2, 10 kb").
2026-07-17  DECISION probe-design_v3 reorganized to the modules x experiments framework (results/ + data/ tiers, generator + config snapshot committed, AssembleDualProbes -> probe-design/src). Design unchanged. See probe-design MANIFEST.
2026-07-17  DECISION probe-design panel: +5 Hansen supp pairs (Inhbb, Ceacam1, Zbtb10, Prdm14, Sik1) / -4 Novo pairs (Myb, Senp3/Sox15, Srxn1, Ski) dropped for low/no FISH signal. Sik1 coord fixed to chr17. Net 96 features (96/96 plates). See [[panel-status]].
2026-07-17  LINT    Renamed probe-design_v3 -> probe-design_v2 (+ all coordinates/readout/dual-barcode/bed/matlab filenames). Version numbers bump only on probe synthesis, which never happened for v2. Also split Inhbb/Tcfcp2l1 BED hub colors.
2026-07-17  INGEST   [[prdm14-enhancer-insertions-2025]] (Development 152(24):dev204886) — Prdm14 downstream enhancers mEn1/cEn1/mEn2 (2i/LIF mESC, luciferase+CRISPR). mEn1 mm10 chr1:13,084,522-13,085,902 (~42kb 3prime of TSS); our E_Prdm14 window already covers mEn1+mEn2 -> no coord change, evidence upgraded to functional mESC.
