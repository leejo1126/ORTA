# Experiment skeleton

Copy this folder to `<module>/experiments/<ID>/` to start a run, then:
1. Fill `MANIFEST.md` (dataset, provenance, visibility).
2. Put the exact config used as `config.snapshot.yaml` (for IF: copy `IF/config/config.yaml`, point its
   `paths.data_dir` at `./data`).
3. Run the pipeline pointed at that config; outputs land in `data/` (gitignored).
4. Curate keepers into `results/` and add a `results/CATALOG.md` row for each.
5. Throwaway checks go in `scratch/<date>_<topic>/` (gitignored).
6. Add a row to `../../../EXPERIMENTS.md` and a note in the relevant facet notebook.

Folders: `data/` (gitignored) · `results/` (tracked keepers + CATALOG) · `scratch/` (gitignored).
