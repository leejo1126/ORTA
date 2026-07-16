# publication/

The "publication view" over the project — assembles the manuscript's figures from the experiments so
the paper cites **stable experiment IDs**, not loose PNGs. One subfolder per manuscript when there are
several.

- `figures.md` — the Figure N → experiment ID → `results/CATALOG` entry → generation script map.
- (add) panel-assembly scripts, supplementary tables, the manuscript's figure exports.

Provenance for every panel already lives in each run's `results/CATALOG.md`; this area just selects and
orders them for the paper. See `../REPRODUCE.md` and `../release-manifest.md`.
