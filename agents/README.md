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

## How they coordinate

- **Orchestrator** (`orchestrator.py`) runs the loops; the **PI** sets priorities and the human
  approves changes.
- **Shared state = the repo**: `IF/config/config.yaml` (the thing being tuned),
  `IF/data/figures/` (QC images), and `agents/lab_notebook/` (structured reports the agents
  write — the audit trail).
- **Structured messages**: every agent returns a pydantic object from `schemas.py`.

## The two loops

1. **Tuning loop** (build this first): `image_analyst` proposes params → `tools.sample_and_qc`
   runs foci on a few cells and renders a montage → `cell_biologist` views it + the counts and
   returns a verdict → repeat until pass (bounded) → **human approves** the config diff.
2. **Analysis loop**: `computational_biologist` proposes a hypothesis → PI prioritizes →
   it runs the analysis → PI + a critic assess → PI reports to you.

## Guardrails
- Agents emit **diffs**, not data. Humans approve before a full-batch run.
- Deterministic pipeline re-runs reproducibly from the approved config.
- Bounded iterations; sample a few FOVs (not all 191); a skeptic/critic checks for batch
  effects, segmentation artifacts, chromatic confounds.
- **Eval:** the tuning loop should reproduce our hand-tuned params (Brd4 dense; Sc35 ~tens;
  DAPI ~tens; Pol2 ~10/cell).

## Running it

Needs the Claude Agent SDK and an API key:
```
pip install claude-agent-sdk anthropic       # into the analysis venv
setx ANTHROPIC_API_KEY "sk-ant-..."          # or use Claude Code's auth
python agents/orchestrator.py tune --marker Sc35 --target "a few tens, compact"
```
Start with `--dry-run` (no LLM calls) to see the loop wiring with a stub agent.

## Files
- `personas/*.md` — each agent's system prompt (edit these to change behavior).
- `schemas.py` — the structured I/O contracts.
- `tools.py` — the deterministic actions agents can call (wrap the `eporca` pipeline).
- `orchestrator.py` — the loop skeleton (SDK wiring + a dry-run stub).
- `lab_notebook/` — where agents write their reports (audit trail).
