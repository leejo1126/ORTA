"""
Per-arm parameter search + leaderboard for the autofoci system (deterministic; no LLM).

Each "arm" is one detector family. ``optimize_arm`` runs a bounded parameter search over
that family's PARAM_SPACE, scoring every trial by the agnostic proxy (``run.run_spec``),
and returns the best spec + the full trial history. An optional ``seed_params`` (e.g. an
LLM's proposed starting point, or a literature-grounded default) warm-starts the search.

Uses Optuna's TPE sampler when available; falls back to reproducible random search.
``rank`` builds the leaderboard the orchestrator prunes against.
"""

from __future__ import annotations

import numpy as np

from .spec import Spec, PARAM_SPACE
from .run import Panel, run_spec

try:
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    HAVE_OPTUNA = True
except Exception:                                            # noqa: BLE001
    HAVE_OPTUNA = False


def _sample_random(space: dict, rng) -> dict:
    out = {}
    for k, dom in space.items():
        if dom[0] == "float":
            out[k] = float(rng.uniform(dom[1], dom[2]))
        elif dom[0] == "int":
            out[k] = int(rng.integers(dom[1], dom[2] + 1))
        elif dom[0] == "cat":
            out[k] = str(rng.choice(dom[1]))
        elif dom[0] == "bool":
            out[k] = bool(rng.integers(0, 2))
    return out


def optimize_arm(panel: Panel, family: str, n_trials: int = 25, seed: int = 0,
                 seed_params: dict | None = None, expect: dict | None = None) -> dict:
    """Search ``family``'s param space on ``panel``; maximize the proxy score (anchored
    to ``expect`` count/shape/coverage when provided). Returns best spec/score/params +
    per-trial history (for the leaderboard + pruning)."""
    space = PARAM_SPACE[family]
    history: list[dict] = []

    def evaluate(params: dict) -> float:
        spec = Spec(family=family, params=params)
        m = run_spec(panel, spec, expect=expect)
        history.append({"params": m["params"], "score": m["score"], "metrics": m})
        return m["score"]

    if HAVE_OPTUNA:
        sampler = optuna.samplers.TPESampler(seed=seed)
        study = optuna.create_study(direction="maximize", sampler=sampler)
        if seed_params:
            study.enqueue_trial({k: v for k, v in seed_params.items() if k in space})

        def objective(trial):
            params = {}
            for k, dom in space.items():
                if dom[0] == "float":
                    params[k] = trial.suggest_float(k, dom[1], dom[2])
                elif dom[0] == "int":
                    params[k] = trial.suggest_int(k, dom[1], dom[2])
                elif dom[0] == "cat":
                    params[k] = trial.suggest_categorical(k, dom[1])
                elif dom[0] == "bool":
                    params[k] = trial.suggest_categorical(k, [True, False])
            return evaluate(params)

        study.optimize(objective, n_trials=n_trials)
        best_score = float(study.best_value)
    else:
        rng = np.random.default_rng(seed)
        best_score = -1.0
        if seed_params:
            best_score = evaluate({k: v for k, v in seed_params.items() if k in space})
        for _ in range(n_trials):
            best_score = max(best_score, evaluate(_sample_random(space, rng)))

    best = max(history, key=lambda h: h["score"])
    best_spec = Spec(family=family, params=best["params"]).validated()
    return {
        "family": family, "best_score": round(best["score"], 4),
        "best_spec": best_spec.model_dump(), "best_params": best_spec.with_defaults(),
        "best_metrics": best["metrics"], "n_trials": len(history), "history": history,
    }


def rank(arms: list[dict]) -> list[dict]:
    """Leaderboard: arms sorted by best_score (desc). ``arms`` are optimize_arm results."""
    return sorted(arms, key=lambda a: a["best_score"], reverse=True)


def converging(best_scores: list[float], min_rounds: int = 2, eps: float = 0.01) -> bool:
    """Cheap convergence test for pruning: with >= min_rounds of per-round best scores,
    an arm is 'converging' if its recent best is still improving or already strong.
    Drop arms whose score has stalled low."""
    if len(best_scores) < min_rounds:
        return True                                          # too early to judge
    recent = best_scores[-min_rounds:]
    improving = recent[-1] >= recent[0] + eps
    strong = recent[-1] >= 0.5
    return improving or strong
