# ORTA agents — a multi-agent "dry lab"

A small team of LLM agents that help run ORTA: tuning foci parameters, running analyses, and
interpreting results. The **deterministic numerical core stays in `IF/` (code)**; agents work at
the **judgment layer** and only ever propose git-tracked config/code changes — they never edit
data or numbers.

## The team

| Agent | Role | Reads | Produces | Tools |
|-------|------|-------|----------|-------|
| **cell_biologist** | Judges foci-call quality by eye vs biological expectation | QC montages (vision) + count stats | `QCVerdict` (pass/fail, issues, suggested direction) | view QC image, read stats |
| **image_analyst** | Turns feedback into pipeline/param changes | verdicts, current config | `ParamProposal` (a config diff) | run foci on sample cells, render QC, propose diff |
| **computational_biologist** | Suggests & runs analyses on the AnnData | `nuclei/foci.h5ad`, condition map | `AnalysisProposal` + result summary | run analysis modules |
| **principal_investigator** | Coordinates, prioritizes, interprets; **interested in transcriptional regulation** | everything | `PIDecision` + questions for you | read all, message human |

The agnostic **autofoci search** adds two more agents: **algorithm_scout** (proposes detector
specs across families) and **foci_judge** (an agnostic visual referee — judges plausibility from
biology + image, never a target count). Both reason from the **wiki** (`core/wiki.py` + the
`knowledge/` cards).

## How they coordinate

- **Orchestrators** run the loops; the **PI** sets priorities and the human approves changes.
- **Shared state = the repo**: `IF/config/config.yaml` (the thing being tuned), `IF/data/figures/`
  (QC images), `agents/knowledge/` (the wiki cards the agents read + grow), and
  `agents/runs/` (structured run records — the audit trail).
- **Structured messages**: every agent returns a pydantic object from `core/schemas.py`.

## The loops

1. **Tuning loop** (`tuning/orchestrator.py`): `image_analyst` proposes params →
   `tools.sample_and_qc` runs foci on a few cells + renders a montage → `cell_biologist` judges →
   repeat until pass (bounded) → **human approves** the config diff. Records under `runs/tuning/`.
2. **Autofoci search** (`autofoci/orchestrator.py`): explores 6 detector families as arms, each
   round running an Optuna parameter search (deterministic, in `eporca.autofoci`) scored by an
   agnostic proxy, with `foci_judge` + `algorithm_scout` + PI pruning non-converging arms. Emits a
   **proposed spec** (never auto-applied). Records under `runs/autofoci/`.
3. **Analysis loop** (planned): `computational_biologist` proposes a hypothesis → PI prioritizes →
   runs the analysis → PI + a critic assess → PI reports.

## Guardrails
- Agents emit **diffs / proposed specs**, not data. Humans approve before a full-batch run, and
  before any change to `config.yaml`.
- Deterministic pipeline re-runs reproducibly from the approved config.
- Bounded iterations; sample a few cells/FOVs (not all 198); validity gates + a critic check for
  noise, batch effects, segmentation artifacts, chromatic confounds.

## Running it

Needs `anthropic` (+ `optuna` for the search) in the analysis venv and an API key. Run as modules
from the repo root:
```
# key in env (or use Claude Code auth); we load it from agents/.anthropic_key at launch
python -m agents.tuning.orchestrator   tune   --marker Sc35 --target "a few tens, compact"
python -m agents.autofoci.orchestrator search --marker Sc35 --rounds 3 --trials 20
```
Start with `--dry-run` (no LLM calls) to watch the loop wiring with stub agents.

## Layout
- `core/` — shared libs: `wiki.py` (knowledge store), `tools.py` (deterministic actions wrapping
  `eporca`), `schemas.py` (I/O contracts), `llm.py` (Anthropic-SDK helper).
- `tuning/orchestrator.py` — the guided tuning loop.
- `autofoci/orchestrator.py` — the agnostic multi-algorithm search (arm scheduler + pruning).
- `personas/*.md` — each agent's system prompt (edit to change behavior).
- `knowledge/*.md` — the wiki cards (biology / method / finding / reference); `INDEX.md` is generated.
- `runs/{tuning,autofoci}/` — where the agents write their records (audit trail).
