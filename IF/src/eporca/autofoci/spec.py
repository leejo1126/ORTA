"""
Detector *spec* DSL for the autonomous search.

A spec is a small, constrained description of a detector: a ``family`` (one of six
spot/condensate detection algorithms) plus bounded, named parameters. It carries **no
free-form code**, so an LLM can propose new detectors safely -- everything a spec can do
is implemented by the registered primitives in ``primitives.py``.

``detect_core(spec, img, nuc) -> labels`` interprets a spec into a 3D label volume on a
single cropped nucleus (``img`` background-subtracted, ``nuc`` the boolean mask), mirroring
the call shape of ``eporca.foci.detect_foci``. The ``mean_fold`` and ``mad_tophat`` families
delegate to the production detectors so they reproduce ``eporca.foci`` exactly.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

FAMILIES = ("mean_fold", "mad_tophat", "log_dog", "h_dome", "otsu_adaptive", "wavelet")

# Bounded search space per family: name -> ("float"|"int", lo, hi) | ("cat", [choices]) |
# ("bool",). Drives Optuna sampling, validates LLM proposals, and seeds defaults.
PARAM_SPACE: dict[str, dict[str, tuple]] = {
    "mean_fold": {
        "threshold": ("float", 1.05, 3.0), "abs_floor": ("float", 0.0, 50.0),
        "blur_sigma": ("float", 0.0, 2.0), "marker_h": ("float", 0.5, 10.0),
        "watershed": ("bool",), "min_size": ("int", 3, 300), "max_size": ("int", 400, 40000),
    },
    "mad_tophat": {
        "tophat_radius": ("int", 2, 12), "noise_k": ("float", 1.0, 6.0),
        "seed_h_k": ("float", 0.1, 2.0), "blur_sigma": ("float", 0.0, 2.0),
        "min_size": ("int", 3, 300),
    },
    "log_dog": {
        "variant": ("cat", ["log", "dog"]), "min_sigma": ("float", 0.8, 3.0),
        "max_sigma": ("float", 2.0, 8.0), "num_sigma": ("int", 3, 8),
        "threshold": ("float", 0.002, 0.2), "fg_floor_pct": ("float", 40.0, 95.0),
        "min_size": ("int", 3, 300),
    },
    "h_dome": {
        "h": ("float", 0.02, 0.6), "min_distance": ("int", 1, 8),
        "fg_floor_pct": ("float", 40.0, 95.0), "watershed": ("bool",),
        "min_size": ("int", 3, 300),
    },
    "otsu_adaptive": {
        "method": ("cat", ["otsu", "local"]), "block_size": ("int", 15, 151),
        "offset_k": ("float", -1.0, 3.0), "watershed": ("bool",),
        "marker_h": ("float", 0.5, 10.0), "min_size": ("int", 3, 400),
    },
    "wavelet": {
        "levels": ("cat", ["1-2", "2-3", "1-3", "2-4"]), "k": ("float", 0.5, 5.0),
        "watershed": ("bool",), "min_size": ("int", 3, 300),
    },
}


class Spec(BaseModel):
    """A detector proposal: family + bounded params. Validated against PARAM_SPACE."""
    family: str = Field(..., description="one of FAMILIES")
    params: dict = Field(default_factory=dict)

    def validated(self) -> "Spec":
        if self.family not in FAMILIES:
            raise ValueError(f"unknown family {self.family!r}; choose from {FAMILIES}")
        space = PARAM_SPACE[self.family]
        clean = {}
        for k, v in self.params.items():
            if k not in space:
                continue                                  # silently drop unknown keys
            kind = space[k][0]
            if kind == "float":
                clean[k] = float(min(max(v, space[k][1]), space[k][2]))
            elif kind == "int":
                clean[k] = int(min(max(int(v), space[k][1]), space[k][2]))
            elif kind == "cat":
                clean[k] = v if v in space[k][1] else space[k][1][0]
            elif kind == "bool":
                clean[k] = bool(v)
        return Spec(family=self.family, params=clean)

    def with_defaults(self) -> dict:
        """Fill any unset params with the midpoint / first choice of their range."""
        out = dict(self.validated().params)
        for k, dom in PARAM_SPACE[self.family].items():
            if k in out:
                continue
            if dom[0] in ("float", "int"):
                mid = (dom[1] + dom[2]) / 2
                out[k] = int(round(mid)) if dom[0] == "int" else round(mid, 3)
            elif dom[0] == "cat":
                out[k] = dom[1][0]
            elif dom[0] == "bool":
                out[k] = True
        return out


def detect_core(spec: Spec, img, nuc):
    """Interpret a spec into a 3D int label volume on one cropped nucleus.
    ``img`` is background-subtracted float (z,y,x); ``nuc`` is the boolean nucleus mask."""
    from . import primitives as P
    p = spec.validated().with_defaults()
    fam = spec.family
    if fam == "mean_fold":
        return P.detect_mean_fold(img, nuc, p)
    if fam == "mad_tophat":
        return P.detect_mad_tophat(img, nuc, p)
    if fam == "log_dog":
        return P.detect_log_dog(img, nuc, p)
    if fam == "h_dome":
        return P.detect_h_dome(img, nuc, p)
    if fam == "otsu_adaptive":
        return P.detect_otsu_adaptive(img, nuc, p)
    if fam == "wavelet":
        return P.detect_wavelet(img, nuc, p)
    raise ValueError(f"unhandled family {fam!r}")
