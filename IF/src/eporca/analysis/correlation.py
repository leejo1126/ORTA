"""Within/between-channel feature correlation matrices, per condition.

Shows how feature couplings (e.g. Brd4 vs Pol2 foci counts/partition) change
under each perturbation relative to control.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..config import Config


def _matrix(adata, condition: str) -> pd.DataFrame:
    raw = pd.DataFrame(adata.layers["raw"], columns=list(adata.var_names))
    raw = raw.loc[adata.obs["condition"].to_numpy() == condition]
    raw = raw.loc[:, raw.std() > 0]
    return raw.corr()


def run(adata, cfg: Config) -> dict:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    outdir = cfg.figures_dir() / "correlation"
    outdir.mkdir(parents=True, exist_ok=True)
    out = {}
    for cond in adata.obs["condition"].cat.categories:
        m = _matrix(adata, cond)
        if m.empty:
            continue
        m.to_csv(outdir / f"corr_{cond}.csv")
        out[cond] = m
        fig, ax = plt.subplots(figsize=(0.25 * m.shape[1] + 3, 0.25 * m.shape[0] + 3))
        im = ax.imshow(m.to_numpy(), cmap="RdBu_r", vmin=-1, vmax=1)
        ax.set_xticks(range(m.shape[1])); ax.set_xticklabels(m.columns, rotation=90, fontsize=5)
        ax.set_yticks(range(m.shape[0])); ax.set_yticklabels(m.index, fontsize=5)
        ax.set_title(f"feature correlation - {cond}")
        fig.colorbar(im, ax=ax, shrink=0.6)
        fig.tight_layout()
        fig.savefig(outdir / f"corr_{cond}.png", dpi=150)
        plt.close(fig)
    return out
