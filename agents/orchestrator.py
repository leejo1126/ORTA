"""
Orchestrator for the ORTA agents — starts with the tuning loop.

Two modes:
  --dry-run : stub agents (no API key) so you can watch the loop wiring work.
  (default) : real LLM agents via the Anthropic SDK, each driven by its persona.

The loop: image_analyst proposes params -> tools.sample_and_qc runs foci on a few
cells + renders a montage -> cell_biologist looks at it and returns a verdict ->
repeat until pass or budget. The final diff is printed for HUMAN approval (never
auto-applied to the canonical config).

    python agents/orchestrator.py tune --marker Sc35 --dry-run
    python agents/orchestrator.py tune --marker Sc35     # needs ANTHROPIC_API_KEY
"""

from __future__ import annotations

import os
import sys
import json
import base64
import argparse
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tools  # noqa: E402
from schemas import QCVerdict, ParamProposal  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent          # ORTA repo root
CONFIG = str(ROOT / "IF" / "config" / "config.yaml")
PERSONAS = Path(__file__).resolve().parent / "personas"
NOTEBOOK = Path(__file__).resolve().parent / "lab_notebook"
MODEL = os.environ.get("ORTA_AGENT_MODEL", "claude-sonnet-4-6")

# rough control-cell targets, used only by the dry-run stub biologist
DRY_TARGETS = {"Brd4": (300, 1200), "Pol2": (5, 15), "Sc35": (15, 45), "DAPI": (8, 40)}


def _persona(name: str) -> str:
    return (PERSONAS / f"{name}.md").read_text()


def _log(kind: str, payload: dict) -> None:
    NOTEBOOK.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    (NOTEBOOK / f"{ts}_{kind}.json").write_text(json.dumps(payload, indent=2))


# --------------------------------------------------------------------- LLM call
def _llm_json(system: str, user_text: str, schema, image_path: str | None = None):
    """One structured agent turn via the Anthropic SDK; returns a `schema` object."""
    import anthropic
    client = anthropic.Anthropic()
    content = [{"type": "text", "text": user_text +
                f"\n\nReturn ONLY JSON matching this schema:\n{json.dumps(schema.model_json_schema())}"}]
    if image_path:
        b64 = base64.standard_b64encode(Path(image_path).read_bytes()).decode()
        content.append({"type": "image",
                        "source": {"type": "base64", "media_type": "image/png", "data": b64}})
    msg = client.messages.create(model=MODEL, max_tokens=1024, system=system,
                                 messages=[{"role": "user", "content": content}])
    text = "".join(b.text for b in msg.content if b.type == "text")
    start, end = text.find("{"), text.rfind("}")
    return schema.model_validate_json(text[start:end + 1])


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
    overrides: dict = {}
    base = Config.load(CONFIG).foci_params(marker).model_dump()
    print(f"[PI] tuning {marker} toward: {target}  (start params: "
          f"{ {k: base[k] for k in ('threshold','min_size','max_size','noise_k') if k in base} })")

    for it in range(1, max_iters + 1):
        stats = tools.sample_and_qc(CONFIG, marker, overrides)
        print(f"  iter {it}: median={stats['per_cell_median']:.0f} "
              f"IQR={stats['per_cell_iqr']}  montage={stats['montage_path']}")
        _log(f"iter{it}_{marker}_stats", stats)

        if dry_run:
            verdict = _stub_biologist(marker, stats)
        else:
            verdict = _llm_json(_persona("cell_biologist"),
                                f"Marker {marker}. Target: {target}. Stats: "
                                f"median={stats['per_cell_median']}, IQR={stats['per_cell_iqr']}, "
                                f"cells={stats['cells']}. Judge the montage.",
                                QCVerdict, image_path=stats["montage_path"])
        _log(f"iter{it}_{marker}_verdict", verdict.model_dump())
        print(f"        biologist: {verdict.verdict}  {verdict.issues}  {verdict.notes}")
        if verdict.verdict == "pass":
            break

        cur = Config.load(CONFIG).foci_params(marker).model_copy(update=overrides).model_dump()
        if dry_run:
            proposal = _stub_analyst(marker, verdict, cur)
        else:
            proposal = _llm_json(_persona("image_analyst"),
                                 f"Current params for {marker}: {cur}. Biologist verdict: "
                                 f"{verdict.model_dump()}. Propose the next ParamProposal.",
                                 ParamProposal)
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
