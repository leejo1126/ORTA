# Experiments registry

Every *run* across all modules, newest first. A run = a dated application of a module's pipeline to a
specific dataset/version, living at `<module>/experiments/<ID>/` with its own `config.snapshot.yaml`
and `MANIFEST.md`. This table is the index; the MANIFEST is the detail.

**ID format:** `<MODULE>_<acq-date>_v<analysis-version>` — e.g. `IF_2026-04-16_v1`, re-analysis
`IF_2026-04-16_v2`, new imaging `IF_2026-09-01_v1`. Probe-design versions: `probe-design_v2`.

**Status:** `planned → active → complete → superseded → archived`. **Visibility:** `public | private`.

| ID | Module | Dataset / raw source | Status | Vis | Headline result | Notebook |
|---|---|---|---|---|---|---|
| `IF_2026-04-16_v1` | IF | `Z:/EPORCA/2026-04-16_IF` (198 FOVs, 8 drug conditions) | active | private | first full run: 3D nuclei + 4-marker foci + AnnData + cross-condition analysis | [if-analysis](lab-notebook/if-analysis.md) |
| `probe-design_v2` | probe-design | E–P coordinates v2 (mm10) | active | private | 96 RNA + 96 DNA symmetric panel (plates full); +Klf4/Car2 + 5 Hansen pairs, −4 low-signal Novo | [probe-design](lab-notebook/probe-design.md) |

<!-- Add a row when you scaffold a new run: cp _templates/experiment <module>/experiments/<ID> -->
