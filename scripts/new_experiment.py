#!/usr/bin/env python3
"""Scaffold a new experiment run from the template.

Usage:
    python scripts/new_experiment.py <module> <ID>
    python scripts/new_experiment.py IF IF_2026-09-01_v1

Copies _templates/experiment/ -> <module>/experiments/<ID>/, stamps the ID into the
skeleton files, and (for IF) drops a config.snapshot.yaml from IF/config/config.yaml with
paths.data_dir pointed at this run's own ./data so it is fully self-contained.

Then: fill MANIFEST.md, add a row to EXPERIMENTS.md, run the pipeline pointed at the snapshot:
    snakemake -s IF/workflow/Snakefile --config cfg=<module>/experiments/<ID>/config.snapshot.yaml -j 8
No pipeline code changes are needed — the run is selected purely by which config it points at.
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TEMPLATE = REPO / "_templates" / "experiment"


def main() -> int:
    ap = argparse.ArgumentParser(description="Scaffold a new experiment run.")
    ap.add_argument("module", help="module name, e.g. IF, probe-design")
    ap.add_argument("id", help="experiment ID, e.g. IF_2026-09-01_v1")
    args = ap.parse_args()

    dest = REPO / args.module / "experiments" / args.id
    if dest.exists():
        print(f"ERROR: {dest} already exists — refusing to overwrite.", file=sys.stderr)
        return 1
    if not (REPO / args.module).exists():
        print(f"ERROR: module '{args.module}' not found at {REPO / args.module}.", file=sys.stderr)
        return 1

    shutil.copytree(TEMPLATE, dest)

    # stamp the ID placeholder into the text skeletons
    for name in ("MANIFEST.md", "NOTES.md", "README.md", "results/CATALOG.md"):
        f = dest / name
        if f.exists():
            f.write_text(f.read_text(encoding="utf-8").replace("<ID>", args.id), encoding="utf-8")

    # IF: freeze the current config with data_dir -> this run's own ./data, and snapshot
    # conditions.yaml alongside it (the loader auto-reads conditions.yaml next to the config).
    if args.module == "IF":
        cfg = (REPO / "IF" / "config" / "config.yaml").read_text(encoding="utf-8")
        cfg = re.sub(r'(\n\s*data_dir:\s*)"[^"]*"', r'\1"./data"', cfg, count=1)
        (dest / "config.snapshot.yaml").write_text(cfg, encoding="utf-8")
        conditions = REPO / "IF" / "config" / "conditions.yaml"
        if conditions.exists():
            shutil.copy(conditions, dest / "conditions.yaml")

    print(f"Scaffolded {dest.relative_to(REPO)}")
    print("Next: fill MANIFEST.md, add an EXPERIMENTS.md row, then run the pipeline against config.snapshot.yaml.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
