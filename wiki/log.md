# Wiki log

Append-only. One line per operation: `YYYY-MM-DD  OP  detail`.

2026-07-16  INIT     Created unified ORTA wiki skeleton (schema + index + domains) on branch reorg/framework.
2026-07-16  MIGRATE  Moved 25 agent cards from agents/knowledge/ into wiki/{biology(8),methods(8),findings(9)} (git mv, history preserved); removed agents/knowledge/INDEX.md.
2026-07-16  MIGRATE  Copied 11 source papers from EP-ORCA/literature/ into wiki/literature/; panel-status into wiki/decisions/.
2026-07-16  INGEST   Authored 6 new findings/reference pages from project memory: bead-contamination, brd4-foci-are-real, anndata-foci-crash, native-crash-fixes, if-fov-condition-layout, if-data-map.
2026-07-16  REPOINT  agents/core/wiki.py now reads wiki/ recursively; machine card list -> wiki/index-cards.md (curated index.md untouched). Verified: 31 cards load, expectations(Brd4) resolves.
