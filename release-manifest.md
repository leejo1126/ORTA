# Release manifest — what goes public

The repo is a monorepo; a publication may open only the paper-relevant subset. This file enumerates the
intended `visibility` of each module/experiment so a curated public release (or a public mirror) can be
built from `public`-flagged content + the `publication/` area. Each experiment's MANIFEST also carries a
`visibility` field; this is the roll-up.

**Decisions still needed:** choose a **code license** (see below) before any public release.

## Modules
| Module | Visibility (intended) | Notes |
|---|---|---|
| `IF/` | public at publication | the analysis pipeline + the paper's IF results |
| `probe-design/` | public at publication | panel design accompanying the DNA/ORCA readouts |
| `agents/` | public (supplementary) | the agentic tuning layer — a methods contribution; can be released as supplementary |
| `wiki/` | selective | methods/biology/literature/decisions support the paper; keep any unpublished-collaborator notes private |
| `RNA/`, `DNA/`, `cross_modality/` | private until their own results publish | planned modules |

## Experiments
| Experiment | Visibility | Gate |
|---|---|---|
| `IF_2026-04-16_v1` | private → public at IF paper submission | data deposited + accessions filled |
| `probe-design_v3` | public with the DNA/design paper | — |

## Code license — MIT
Chosen: **MIT** (`LICENSE` + `CITATION.cff`). **Action:** set the copyright holder name in `LICENSE`
(currently a placeholder). Data gets a separate license at deposition (e.g. CC-BY-4.0).

## Release steps (at publication)
1. Fill accessions in `docs/data-availability.md`; deposit raw + `nuclei.h5ad` + tables.
2. Set `LICENSE` + `CITATION.cff`; finalize `publication/figures.md`.
3. Tag a version; mint a Zenodo DOI for the code.
4. Build the public release: include `public`-flagged modules/experiments + `publication/`; exclude
   `private` content.
