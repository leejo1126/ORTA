# Wiki schema — ORTA unified knowledge base

Config for this llm-wiki (Karpathy pattern; skill: `llm-wiki`). Read before every ingest/query/lint.
One unified KB for the whole project — merges the former `EP-ORCA/literature/` (E–P panel literature)
and `agents/knowledge/` (foci methods + marker biology). The agents read this wiki for grounding.

## Purpose
Distil durable project knowledge — the literature behind the panel, marker biology, detection methods,
wet-lab protocols, empirical findings, and decisions — so it compounds instead of being re-derived.

## Domains (subfolders)
- **literature/** — one page per source paper. Slug = `firstauthor-year[-topic]`. Fields: cell type ·
  method · **evidence type** (FUNCTIONAL / CORRELATIVE / BENCHMARK / SYNTHETIC) · genome build · E–P
  distance · eRNA evidence · confidence · validated pairs (mm10 coords) · relevance. Only FUNCTIONAL
  counts as "validated" for panel inclusion.
- **biology/** — marker + nuclear-structure biology cards (Brd4, Pol2, Sc35, DAPI/chromocenters, speckles…).
- **methods/** — foci/spot detection algorithm cards (h-dome, wavelet, mean_fold, mad-tophat, LoG/DoG, otsu…).
- **protocols/** — versioned wet-lab protocols (IF staining, hybridization…). Bench-notebook entries cite the
  version used; a change is a version bump on the page.
- **findings/** — empirical results specific to this project (autofoci picks, the Pol2 cliff, bead artifact,
  crash fixes, data-layout maps). Link the experiment ID.
- **decisions/** — cross-source decisions and their rationale (e.g. `panel-status`).

## Conventions
- Genome build **mm10 (GRCm38)** is the reference; flag any mm9 coordinate and give the liftover.
- Link liberally with `[[slug]]`. Update `index.md` on any add/rename; append to `log.md` every operation.
- One page = one topic. Tags on a trailing backtick line. Keep pages short; put chronology in the notebook,
  not here.

## Operations: ingest / query / lint — see the `llm-wiki` skill.
