# Experiment <ID>

> One run of a module against a specific dataset/version. Fill every field — this is the provenance
> record that makes the run reproducible and citable.

- **ID:** `<MODULE>_<acq-date>_v<analysis-version>`
- **Module:** <IF | probe-design | ...>
- **Status:** planned | active | complete | superseded | archived
- **Visibility:** public | private
- **Date started:** YYYY-MM-DD   **Operator:** <name>

## Dataset
- **Raw data location:** `<external path or archive accession>` (NOT in git)
- **Samples / conditions:** <cell line, drug conditions, FOVs, etc.>
- **Acquisition:** <imaging session — link to `../../lab-notebook/wet-lab.md` entry>

## Provenance
- **Config:** `config.snapshot.yaml` (in this folder — the exact tunables used)
- **Pipeline git commit:** `<sha>` (the code that produced `data/`)
- **Environment:** `<env/lockfile ref>`

## Result
- **Headline:** <one-line takeaway; also add/echo the `EXPERIMENTS.md` row>
- **Keeper outputs:** see `results/CATALOG.md`
- **Notes / log:** `NOTES.md` (or link to the facet notebook)

## Supersedes / superseded by
<links to prior/next run IDs, if any>
