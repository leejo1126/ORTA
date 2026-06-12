# The ORTA agentic engineering workflow

ORTA is developed with an agentic workflow. The principle: **the deterministic numerical
core stays as reproducible code; agents operate only at the judgment layer** (QC, parameter
tuning, algorithm search, hypothesis generation) and only ever propose git-tracked
config/code changes — they never edit data or numbers, and never auto-apply to `config.yaml`.

## The knowledge layer (wiki)

`agents/core/wiki.py` + the `agents/knowledge/` cards are a git-tracked, keyword-retrieved
knowledge base the agents consult and grow:

- **biology** cards — per-marker expected morphology/abundance/artifacts.
- **method** cards — per detector family: assumptions, strengths, failure modes, key params.
- **reference** cards — cited literature (web-accrued at build time, with `sources:`).
- **finding** cards — distilled from our own runs (e.g. why Pol2 `mean_fold` oscillates).

Cards link to each other; `relevant_for(marker, algorithm)` retrieves a card set (with
one-hop link expansion) that the orchestrators inject into agent prompts. Web accrual is a
**build-time, human-curated** step; agent inference stays offline.

## The loops

1. **Guided tuning** (`agents/tuning`) — improves the *current* production detector against a
   biological expectation; the cell_biologist judges QC montages, the image_analyst proposes a
   config diff, bounded iterations, human approves. Records in `agents/runs/tuning/`.
2. **Agnostic autofoci search** (`agents/autofoci`) — explores detector *families* from
   scratch, **with no target count and no use of current params as a benchmark**. Each family
   is an arm; an Optuna parameter search (deterministic) is scored by agnostic image proxies;
   foci_judge (vision) + algorithm_scout + PI prune non-converging arms (successive halving);
   the winner is written as a **proposed spec**. Records in `agents/runs/autofoci/`.

## Guardrails

- Agents emit **diffs / proposed specs**, never data; constrained spec DSL (no code execution).
- Bounded budgets; validity gates; a critic/PI checks for noise, batch effects, artifacts.
- Everything reproducible: the deterministic core re-runs from the approved `config.yaml`.
