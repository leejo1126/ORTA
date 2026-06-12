"""
Structured I/O contracts for the ORTA agents. Each agent returns one of these
(as JSON), so the orchestrator can route results and everything is inspectable.
"""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel


class QCVerdict(BaseModel):
    """Cell biologist's judgement of a marker's foci calls."""
    marker: str
    verdict: str                      # "pass" | "fail"
    issues: list[str] = []            # over_split, under_detect, fills_nucleus, merged, ...
    suggested_direction: dict[str, str] = {}   # e.g. {"threshold": "up", "min_size": "up"}
    confidence: float = 0.5
    notes: str = ""


class ParamProposal(BaseModel):
    """Image analyst's proposed parameter change for one marker."""
    marker: str
    params: dict                      # new FociParams fields (merged onto current)
    rationale: str = ""
    test_fov: int = 0
    test_cells: Optional[list[int]] = None     # None -> auto-pick
    montage_path: Optional[str] = None         # filled after sample_and_qc
    per_cell_median: Optional[float] = None
    per_cell_iqr: Optional[list[float]] = None


class AnalysisProposal(BaseModel):
    """Computational biologist's analysis plan."""
    question: str
    method: str                       # which eporca.analysis module / approach
    markers: list[str] = []
    multiple_testing: str = "BH-FDR"
    expected_direction: str = ""      # falsifiable prediction
    result_summary: Optional[str] = None


class PIDecision(BaseModel):
    """PI's synthesis and next steps for the human."""
    summary: str
    priorities: list[str] = []
    open_questions: list[str] = []
    risks: list[str] = []


class WikiNote(BaseModel):
    """A knowledge card an agent contributes to the wiki (see agents/core/wiki.py).
    `type` is biology | method | finding | reference; findings are appended over time."""
    name: str                          # short kebab-case slug / title
    description: str                   # one-line summary (used for retrieval + index)
    type: str = "finding"
    tags: list[str] = []               # e.g. ["Sc35", "mean_fold", "threshold"]
    sources: list[str] = []            # citations / URLs for literature-derived notes
    links: list[str] = []              # related card names ([[name]] style)
    body: str = ""                     # the note itself (markdown)


# --- autofoci (agnostic algorithm search) contracts ---------------------------
class SpecProposal(BaseModel):
    """Algorithm scout's next detector spec to try for one arm (seeds the next
    Optuna round). Params are validated/clipped against autofoci PARAM_SPACE."""
    family: str                        # one of the autofoci FAMILIES
    params: dict = {}                  # starting params for the next round
    rationale: str = ""
    structural_change: bool = False    # true if switching family / qualitative approach


class ArmVerdict(BaseModel):
    """Foci judge's agnostic verdict on an arm's current best result (from montage+metrics)."""
    family: str
    plausible: bool
    confidence: float = 0.5
    issues: list[str] = []             # fires_on_background, fills_nucleus, over_split, ...
    suggested_direction: dict[str, str] = {}   # e.g. {"sensitivity":"lower"}
    notes: str = ""


class AllocationDecision(BaseModel):
    """PI's per-round budget decision over the arms (which to keep / drop / promote)."""
    keep: list[str] = []
    drop: list[str] = []
    finalists: list[str] = []
    rationale: str = ""
