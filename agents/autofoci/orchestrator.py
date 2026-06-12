"""
Autonomous, agnostic foci-detector search (Track B).

Explores the 6 detector families as parallel "arms"; each round every surviving arm runs a
deterministic Optuna parameter search scored by the agnostic proxy (no target count), then
an LLM **foci_judge** vision-checks the best montage and an **algorithm_scout** proposes the
next starting spec. A deterministic prune (proxy score + convergence + judge confidence),
optionally ratified by the **principal_investigator**, drops non-converging arms and
reallocates budget (successive halving) until 1–2 finalists remain.

Outputs go to a SEPARATE dir (`agents/runs/autofoci/<ts>_<marker>/`): per-round montages,
`trials.jsonl`, `leaderboard.md`, and a **proposed** winning spec — never applied to
`config.yaml`. The agents are grounded in the lab wiki (`wiki.relevant_for`). A `--dry-run`
stub exercises the whole loop with no API calls.

    python -m agents.autofoci.orchestrator search --marker Sc35 --dry-run
    python -m agents.autofoci.orchestrator search --marker Sc35 --rounds 3 --trials 20
"""

from __future__ import annotations

import json
import argparse
from pathlib import Path
from datetime import datetime, timezone

from agents.core import wiki
from agents.core.schemas import SpecProposal, ArmVerdict, AllocationDecision, WikiNote
from agents.core.llm import _llm_json, _persona

from eporca.config import Config
from eporca.autofoci.spec import Spec, FAMILIES
from eporca.autofoci.run import build_panel, run_spec
from eporca.autofoci import search as A

ROOT = Path(__file__).resolve().parents[2]
CONFIG = str(ROOT / "IF" / "config" / "config.yaml")
RUNS = Path(__file__).resolve().parents[1] / "runs" / "autofoci"
KEEP_SCHEDULE = (6, 3, 2, 1)            # arms kept after each round (successive halving)


# --------------------------------------------------------------- dry-run stubs
def _stub_judge(family: str, m: dict) -> ArmVerdict:
    issues = []
    if m["median_fill"] > 0.4:
        issues.append("fills_nucleus")
    if m["count_cv"] > 0.6:
        issues.append("unstable")
    if m["frac_tiny"] > 0.5:
        issues.append("noise_specks")
    return ArmVerdict(family=family, plausible=bool(m["valid"] and m["score"] >= 0.6),
                      confidence=min(0.9, float(m["score"])), issues=issues,
                      notes=f"stub: score {m['score']}")


def _stub_scout(family: str, best_params: dict) -> SpecProposal:
    return SpecProposal(family=family, params=best_params, rationale="stub: keep refining")


# --------------------------------------------------------------- leaderboard IO
def _write_leaderboard(path: Path, marker: str, history: list[dict], finalists: list[str]) -> None:
    lines = [f"# Autofoci search — {marker}\n",
             "Agnostic multi-algorithm search (no target count). Score is the proxy "
             "(contrast/SNR + reproducibility + fill/size sanity), higher = more foci-like.\n"]
    for rnd in history:
        lines.append(f"\n## Round {rnd['round']}  (kept: {', '.join(rnd['kept'])})\n")
        lines.append("| family | score | valid | med_count | cv | fill | contrast | judge | conf |")
        lines.append("|--------|-------|-------|-----------|----|------|----------|-------|------|")
        for f, r in sorted(rnd["arms"].items(), key=lambda kv: -kv[1]["score"]):
            m, v = r["metrics"], r["verdict"]
            lines.append(f"| {f} | {r['score']:.3f} | {m['valid']} | {m['median_count']:.0f} | "
                         f"{m['count_cv']} | {m['median_fill']} | {m['median_contrast']} | "
                         f"{'ok' if v['plausible'] else 'no'} | {v['confidence']:.2f} |")
    lines.append(f"\n## Finalist(s): {', '.join(finalists)}\n")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# --------------------------------------------------------------------- the loop
def run_autofoci(marker: str, fov: int = 0, dry_run: bool = False, rounds: int = 3,
                 trials: int = 20, n_cells: int = 5):
    run_ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    outdir = RUNS / f"{run_ts}_{marker}"
    mont_dir = outdir / "montages"
    mont_dir.mkdir(parents=True, exist_ok=True)

    cfg = Config.load(CONFIG)
    panel = build_panel(cfg, marker, fov, n_cells)
    bio_ctx = wiki.render_for_prompt(wiki.relevant_for(marker))
    print(f"[autofoci] {marker} fov{fov}: panel {panel.cells}  SNR={panel.image_snr:.1f}  "
          f"(run {run_ts}, dry_run={dry_run})")

    arms = {f: {"seed": Spec(family=f).with_defaults(), "scores": [], "best": None} for f in FAMILIES}
    alive = list(FAMILIES)
    history, trials_fh = [], (outdir / "trials.jsonl").open("w", encoding="utf-8")

    for rnd in range(1, rounds + 1):
        round_arms = {}
        for fam in alive:
            res = A.optimize_arm(panel, fam, n_trials=trials, seed=rnd, seed_params=arms[fam]["seed"])
            arms[fam]["scores"].append(res["best_score"])
            if not arms[fam]["best"] or res["best_score"] > arms[fam]["best"]["best_score"]:
                arms[fam]["best"] = res
            for h in res["history"]:
                trials_fh.write(json.dumps({"round": rnd, "family": fam, "score": h["score"],
                                            **h["metrics"]}) + "\n")

            mp = str(mont_dir / f"r{rnd}_{fam}.png")
            m = run_spec(panel, Spec(**res["best_spec"]), out_png=mp)
            method_ctx = wiki.render_for_prompt(wiki.relevant_for(marker, fam))

            if dry_run:
                verdict = _stub_judge(fam, m)
                prop = _stub_scout(fam, res["best_params"])
            else:
                verdict = _llm_json(
                    _persona("foci_judge"),
                    f"{bio_ctx}\n\nMethod knowledge:\n{method_ctx}\n\nMarker {marker}, family "
                    f"{fam}. Proxy metrics: {m}. Judge the montage — agnostic, no target count.",
                    ArmVerdict, image_path=mp)
                prop = _llm_json(
                    _persona("algorithm_scout"),
                    f"{method_ctx}\n\nFamily {fam}; current best params {res['best_params']}; "
                    f"metrics {m}; judge said {verdict.model_dump()}. Propose the next "
                    f"SpecProposal (params to seed the next round).",
                    SpecProposal)

            # seed the next round from the scout's params (validated to this family)
            merged = {**res["best_params"], **Spec(family=fam, params=prop.params).validated().params}
            arms[fam]["seed"] = merged
            round_arms[fam] = {"score": res["best_score"], "metrics": m,
                               "verdict": verdict.model_dump(), "proposal": prop.model_dump()}
            print(f"  r{rnd} {fam:14s} score={res['best_score']:.3f} "
                  f"med_count={m['median_count']:.0f} judge={'ok' if verdict.plausible else 'no'}"
                  f"({verdict.confidence:.2f})")

        # ---- deterministic prune (proxy score + convergence), then PI ratifies ----
        target = KEEP_SCHEDULE[min(rnd - 1, len(KEEP_SCHEDULE) - 1)]
        ranked = sorted(alive, key=lambda f: (round_arms[f]["score"],
                                              round_arms[f]["verdict"]["confidence"]), reverse=True)
        converging = [f for f in ranked if A.converging(arms[f]["scores"])]
        kept = (converging or ranked)[:target]

        if not dry_run and len(alive) > 1:
            board = "\n".join(
                f"{f}: score={round_arms[f]['score']:.3f}, judge="
                f"{'plausible' if round_arms[f]['verdict']['plausible'] else 'implausible'}"
                f"({round_arms[f]['verdict']['confidence']:.2f}), issues="
                f"{round_arms[f]['verdict']['issues']}" for f in alive)
            decision = _llm_json(
                _persona("principal_investigator"),
                f"Agnostic autofoci search for {marker}, round {rnd}/{rounds}. Leaderboard:\n"
                f"{board}\n\nDeterministic suggestion: keep {kept}, drop "
                f"{[f for f in alive if f not in kept]}. Return an AllocationDecision; you may "
                f"rescue an arm the metrics underrate if its montage/biology is promising, but "
                f"justify, and keep at most {target}.",
                AllocationDecision)
            picked = [f for f in (decision.keep or kept) if f in alive][:max(1, target)]
            kept = picked or kept

        dropped = [f for f in alive if f not in kept]
        history.append({"round": rnd, "arms": round_arms, "kept": kept, "dropped": dropped})
        print(f"  -> keep {kept}  drop {dropped}")
        alive = kept
        _write_leaderboard(outdir / "leaderboard.md", marker, history, alive)
        if len(alive) <= 1:
            break

    trials_fh.close()

    # ---- winner = best overall arm by proxy score (valid) ----
    scored = [(arms[f]["best"]["best_score"], f) for f in FAMILIES if arms[f]["best"]]
    best_score, winner = max(scored)
    win = arms[winner]["best"]
    proposed = {"marker": marker, "fov": fov, "run": run_ts, "winner_family": winner,
                "best_score": best_score, "spec": win["best_spec"], "params": win["best_params"],
                "metrics": win["best_metrics"], "note": "PROPOSED — not applied to config.yaml"}
    (outdir / f"proposed_spec_{marker}.json").write_text(json.dumps(proposed, indent=2),
                                                         encoding="utf-8")
    _write_leaderboard(outdir / "leaderboard.md", marker, history, [winner])

    # ---- distill a finding card back into the wiki ----
    wiki.write(WikiNote(
        name=f"autofoci-{marker.lower()}-{run_ts[:8]}",
        description=f"Agnostic autofoci search picked {winner} for {marker} "
                    f"(proxy {best_score:.3f}, median {win['best_metrics']['median_count']:.0f}/cell)",
        type="finding", tags=[marker, winner, "autofoci"],
        links=[f"{marker.lower()}-biology", f"{winner.replace('_','-')}-method"],
        body=(f"Run {run_ts} (fov {fov}, agnostic, no target count). Winner: **{winner}** "
              f"(proxy score {best_score:.3f}; median {win['best_metrics']['median_count']:.0f} "
              f"foci/cell, contrast {win['best_metrics']['median_contrast']}, fill "
              f"{win['best_metrics']['median_fill']}). Params: {win['best_params']}. "
              f"Proposed spec in agents/runs/autofoci/{run_ts}_{marker}/ — NOT applied to config.")),
        append_body=True)

    print(f"\n[autofoci] winner: {winner} (proxy {best_score:.3f}). Proposed spec + leaderboard "
          f"in {outdir}  (config.yaml untouched)")
    return proposed


def main():
    ap = argparse.ArgumentParser(prog="autofoci")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("search")
    sp.add_argument("--marker", required=True)
    sp.add_argument("--fov", type=int, default=0)
    sp.add_argument("--dry-run", action="store_true")
    sp.add_argument("--rounds", type=int, default=3)
    sp.add_argument("--trials", type=int, default=20)
    sp.add_argument("--cells", type=int, default=5)
    args = ap.parse_args()
    if args.cmd == "search":
        run_autofoci(args.marker, args.fov, args.dry_run, args.rounds, args.trials, args.cells)


if __name__ == "__main__":
    main()
