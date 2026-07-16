# CLAUDE.md — working instructions for this repo (ORTA)

Read this first. It encodes how the project is organized so work stays consistent across sessions.

## Orientation — the four spines
Keep these current; they are the project's index:
- `OVERVIEW.md` — structure + module status + what's active. Update when layout/focus changes.
- `EXPERIMENTS.md` — one row per run. Add a row whenever a new experiment is scaffolded.
- `wiki/index.md` — the knowledge base (llm-wiki). Use the `llm-wiki` skill to ingest/query/lint.
- `lab-notebook/main.md` — dated log (bench + computational); links out to facet notebooks.

## Two axes: modules × experiments
- A **module** = a modality/workstream (`IF/`, `probe-design/`, planned `RNA/` `DNA/` `cross_modality/`).
  Same internal skeleton (`_templates/module/`). Add one by copying the template, not by inventing layout.
- An **experiment** = a dated run at `<module>/experiments/<ID>/` with `ID = <MODULE>_<acq-date>_v<version>`.
  Never overwrite a prior run's outputs — scaffold a new run (`cp _templates/experiment ...`), snapshot the
  config, and point the pipeline at it.

## Running / re-running the IF pipeline
- The pipeline is run-scoped through **one knob**: `paths.data_dir` in the config. Every output path derives
  from it (`IF/src/eporca/config.py`), and `IF/workflow/Snakefile` takes `--config cfg=<path>`.
- Re-run = new experiment dir + its own `config.snapshot.yaml` whose `data_dir` points inside that dir, then
  `snakemake --config cfg=IF/experiments/<ID>/config.snapshot.yaml`. Old runs stay intact. **Do not** edit the
  pipeline to add run-ids — the mechanism already exists.

## Outputs: three tiers (never mix them)
Inside every `experiments/<ID>/`:
- `data/` — machine-generated pipeline artifacts. Gitignored, regenerable, **no** per-file note.
- `results/` — curated keepers you reference in notebook/wiki/paper. **Every file needs a `results/CATALOG.md`
  row**: what it is · how generated (cmd + experiment ID + git commit) · how to read · what it says · links.
  Small files git-tracked; large binaries stay gitignored and the CATALOG row records path + how to regenerate.
- `scratch/<date>_<topic>/` — throwaway vibe-checks. Gitignored, disposable, no note. If one matters, **promote**
  it to `results/` (+ a CATALOG row). Nothing in `scratch/` is ever referenced from notebook/wiki.

## Lab notebook workflow
- When the user reports **bench work**: append a concise line to `lab-notebook/main.md`, write the detailed entry
  in `lab-notebook/wet-lab.md`; if a protocol changed, **version** the `wiki/protocols/<protocol>` page and note
  the change; if it produced raw imaging, record the raw-data pointer for the experiment that will consume it.
- When you do **computational work**: log it in the relevant facet (`if-analysis.md` / `probe-design.md` /
  `autofoci.md`) and, if noteworthy, in `main.md`. Link experiment IDs and `[[wiki]]` pages.

## Knowledge base
- One unified `wiki/` (llm-wiki). Domains: `literature/ biology/ methods/ protocols/ findings/ decisions/`.
- Agents read this wiki for grounding (`agents/core/wiki.py` → `wiki/`). New durable knowledge → a wiki page +
  `wiki/index.md` row + `wiki/log.md` line. Use `[[slug]]` links.

## Provenance & reproducibility (this is the point)
Every keeper traces `figure → results/CATALOG → experiment ID → config.snapshot.yaml → git commit → raw-data
pointer`. Keep that chain intact — it *is* the publication's reproducibility story.

## Conventions
- Dates ISO `YYYY-MM-DD`. Genome build mm10 (GRCm38); flag any mm9 with a liftover.
- Code in git, data out of git and regenerable. Absolute in-repo paths → make relative where possible.
- Commit per logical phase with a clear message; this reorg lives on branch `reorg/framework`.
- Windows host; repo path contains a space (`s:\cluade code\...`). Prefer `subprocess([...])` over shell strings.
