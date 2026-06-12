"""
Orchestrator for the ORTA agents — starts with the tuning loop.

Two modes:
  --dry-run : stub agents (no API key) so you can watch the loop wiring work.
  (default) : real LLM agents via the Anthropic SDK, each driven by its persona.

The loop: image_analyst proposes params -> tools.sample_and_qc runs foci on a few
cells + renders a montage -> cell_biologist looks at it and returns a verdict ->
repeat until pass or budget. The final diff is printed for HUMAN approval (never
auto-applied to the canonical config).

    python -m agents.tuning.orchestrator tune --marker Sc35 --dry-run
    python -m agents.tuning.orchestrator tune --marker Sc35   # needs ANTHROPIC_API_KEY
"""

from __future__ import annotations

import json
import argparse
from pathlib import Path
from datetime import datetime, timezone

from agents.core import tools, wiki
from agents.core.schemas import QCVerdict, ParamProposal
from agents.core.llm import _llm_json, _persona

ROOT = Path(__file__).resolve().parents[2]             # ORTA repo root
CONFIG = str(ROOT / "IF" / "config" / "config.yaml")
NOTEBOOK = Path(__file__).resolve().parents[1] / "runs" / "tuning"

# rough control-cell targets, used only by the dry-run stub biologist
DRY_TARGETS = {"Brd4": (300, 1200), "Pol2": (5, 15), "Sc35": (15, 45), "DAPI": (8, 40)}


def _log(kind: str, payload: dict) -> None:
    NOTEBOOK.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    (NOTEBOOK / f"{ts}_{kind}.json").write_text(json.dumps(payload, indent=2))


HISTORY_MD = NOTEBOOK / "HISTORY.md"
HISTORY_JSONL = NOTEBOOK / "history.jsonl"
_KEY_PARAMS = ("mode", "threshold", "min_size", "max_size", "marker_h", "blur_sigma")


def _append_history(run_ts: str, marker: str, it: int, target: str, stats: dict,
                    verdict: QCVerdict, proposal: "ParamProposal | None") -> None:
    """Append one iteration to the git-tracked tuning record: a machine-readable
    JSONL line + a human-readable HISTORY.md row. This is the "how it improved"
    trail — params, counts, the biologist's verdict, and the next proposed move."""
    NOTEBOOK.mkdir(parents=True, exist_ok=True)
    p = stats["params"]
    kp = {k: p[k] for k in _KEY_PARAMS if k in p}
    rec = {
        "run": run_ts, "iter": it, "marker": marker, "target": target,
        "params": p, "key_params": kp,
        "per_cell_median": stats["per_cell_median"],
        "per_cell_iqr": stats["per_cell_iqr"],
        "per_cell_counts": stats["per_cell_counts"],
        "verdict": verdict.verdict, "confidence": verdict.confidence,
        "issues": verdict.issues, "suggested_direction": verdict.suggested_direction,
        "next_params": proposal.params if proposal else {},
        "montage": stats["montage_path"], "notes": verdict.notes,
    }
    with HISTORY_JSONL.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")

    if not HISTORY_MD.exists():
        HISTORY_MD.write_text(
            "# ORTA foci-tuning history\n\n"
            "One row per tuning iteration (newest appended at the bottom). "
            "`run` is the UTC start of a tuning run; montages referenced here live "
            "in `IF/data/figures/` (regenerable, not git-tracked).\n\n"
            "| run | iter | marker | key params | median | IQR | verdict | conf | note |\n"
            "|-----|------|--------|------------|--------|-----|---------|------|------|\n",
            encoding="utf-8")
    note = " ".join((verdict.notes or "").split())
    if len(note) > 100:
        note = note[:99] + "…"
    note = note.replace("|", "│")
    kp_str = ", ".join(f"{k}={v}" for k, v in kp.items()).replace("|", "│")
    iqr = stats["per_cell_iqr"]
    row = (f"| {run_ts} | {it} | {marker} | {kp_str} | "
           f"{stats['per_cell_median']:.1f} | [{iqr[0]:.0f}, {iqr[1]:.0f}] | "
           f"{verdict.verdict} | {verdict.confidence:.2f} | {note} |\n")
    with HISTORY_MD.open("a", encoding="utf-8") as f:
        f.write(row)


# --------------------------------------------------------------- dry-run stubs
def _stub_biologist(marker, stats) -> QCVerdict:
    lo, hi = DRY_TARGETS.get(marker, (5, 50))
    med = stats["per_cell_median"]
    if lo <= med <= hi:
        return QCVerdict(marker=marker, verdict="pass", confidence=0.6,
                         notes=f"median {med:.0f} within target [{lo},{hi}]")
    direction = "up" if med > hi else "down"   # too many -> raise threshold
    return QCVerdict(marker=marker, verdict="fail", issues=["over_detect" if med > hi else "under_detect"],
                     suggested_direction={"threshold": direction}, confidence=0.6,
                     notes=f"median {med:.0f} outside target [{lo},{hi}]; move threshold {direction}")


def _stub_analyst(marker, verdict, params) -> ParamProposal:
    new = dict(params)
    step = {"up": 1.15, "down": 0.87}
    for k, d in verdict.suggested_direction.items():
        if k in new and isinstance(new[k], (int, float)):
            new[k] = round(new[k] * step.get(d, 1.0), 3)
    return ParamProposal(marker=marker, params={k: new[k] for k in verdict.suggested_direction
                                                if k in new}, rationale="stub nudge")


# --------------------------------------------------------------------- the loop
def run_tuning_loop(marker: str, target: str, dry_run: bool, max_iters: int = 5):
    from eporca.config import Config
    run_ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    fig_dir = Config.load(CONFIG).figures_dir()
    overrides: dict = {}
    base = Config.load(CONFIG).foci_params(marker).model_dump()
    print(f"[PI] tuning {marker} toward: {target}  (run {run_ts}; start params: "
          f"{ {k: base[k] for k in ('threshold','min_size','max_size','noise_k') if k in base} })")

    # ground the agents in accrued biology/method knowledge for this marker
    cards = wiki.relevant_for(marker)
    wiki_ctx = ("Background knowledge from the lab wiki (use it to judge what these foci "
                "should look like and which way to move params):\n"
                + wiki.render_for_prompt(cards))
    if cards:
        print(f"        wiki: grounding on {[c.name for c in cards]}")

    for it in range(1, max_iters + 1):
        # timestamped montage per iteration so the visual record is never overwritten
        montage = str(fig_dir / f"agent_tune_{marker}_{run_ts}_iter{it}.png")
        stats = tools.sample_and_qc(CONFIG, marker, overrides, out_png=montage)
        print(f"  iter {it}: median={stats['per_cell_median']:.0f} "
              f"IQR={stats['per_cell_iqr']}  montage={stats['montage_path']}")
        _log(f"iter{it}_{marker}_stats", stats)

        if dry_run:
            verdict = _stub_biologist(marker, stats)
        else:
            verdict = _llm_json(_persona("cell_biologist"),
                                f"{wiki_ctx}\n\nMarker {marker}. Target: {target}. Stats: "
                                f"median={stats['per_cell_median']}, IQR={stats['per_cell_iqr']}, "
                                f"cells={stats['cells']}. Judge the montage.",
                                QCVerdict, image_path=stats["montage_path"])
        _log(f"iter{it}_{marker}_verdict", verdict.model_dump())
        print(f"        biologist: {verdict.verdict}  {verdict.issues}  {verdict.notes}")
        if verdict.verdict == "pass":
            _append_history(run_ts, marker, it, target, stats, verdict, None)
            break

        cur = Config.load(CONFIG).foci_params(marker).model_copy(update=overrides).model_dump()
        if dry_run:
            proposal = _stub_analyst(marker, verdict, cur)
        else:
            proposal = _llm_json(_persona("image_analyst"),
                                 f"{wiki_ctx}\n\nCurrent params for {marker}: {cur}. "
                                 f"Biologist verdict: {verdict.model_dump()}. "
                                 f"Propose the next ParamProposal.",
                                 ParamProposal)
        _append_history(run_ts, marker, it, target, stats, verdict, proposal)
        overrides.update(proposal.params)
        print(f"        analyst proposes: {proposal.params}  ({proposal.rationale})")

    print("\n[PI] proposed change for HUMAN approval:")
    print(tools.propose_config_diff(CONFIG, marker, overrides) if overrides else "  (no change)")
    return overrides


def main():
    ap = argparse.ArgumentParser(prog="orta-agents")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("tune")
    sp.add_argument("--marker", required=True)
    sp.add_argument("--target", default="match the control biological expectation")
    sp.add_argument("--dry-run", action="store_true")
    sp.add_argument("--max-iters", type=int, default=5)
    args = ap.parse_args()
    if args.cmd == "tune":
        run_tuning_loop(args.marker, args.target, args.dry_run, args.max_iters)


if __name__ == "__main__":
    main()
