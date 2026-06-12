"""ORTA agents: the knowledge wiki + the tuning and autofoci orchestrators.

Run the orchestrators as modules from the repo root, e.g.:
    python -m agents.tuning.orchestrator   tune   --marker Sc35 --dry-run
    python -m agents.autofoci.orchestrator search --marker Sc35 --dry-run
"""

import sys

# Windows consoles default to cp1252; LLM text routinely contains characters it
# can't encode (arrows, en-dashes). Make stdout/stderr lossy-UTF-8 once at import
# so logging an agent's text never aborts a run.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
