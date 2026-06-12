"""Autonomous per-channel foci-detector search.

A detector is expressed as a JSON "spec" (a small DSL) of composable ops, so an LLM
can propose new methods without us executing free-form code. The current foci.py
algorithms (mad / mean_fold) are expressible as specs and serve as the benchmark.

  spec.py        - spec schema, detect_core(spec, img, nuc), benchmark_spec(cfg, marker)
  primitives.py  - the op registry (preprocess / foreground / seeds / split / filter)
  run.py         - executor: fixed cell panel, run a spec, overlay + proxy stats, validity gates
  search.py      - leaderboard + autonomous loop (Optuna refine + LLM propose, LLM judge)
"""
