"""Cross-channel colocalization summaries per condition.

Per-nucleus colocalization features (coloc_<A>_<B>_frac / _nn_um) are built in
features.py from chromatic-corrected within-nucleus nearest-neighbour distances.
Here we aggregate them per condition and compare each perturbation to control.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..config import Config


def coloc_summary(adata, cfg: Config) -> pd.DataFrame:
    cols = [v for v in adata.var_names if v.startswith("coloc_")]
    if not cols:
        return pd.DataFrame()
    raw = pd.DataFrame(adata.layers["raw"], columns=list(adata.var_names))[cols]
    raw["condition"] = adata.obs["condition"].to_numpy()
    return raw.groupby("condition").agg(["mean", "median", "count"])


def run(adata, cfg: Config) -> pd.DataFrame:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    cfg.figures_dir().mkdir(parents=True, exist_ok=True)
    summ = coloc_summary(adata, cfg)
    if summ.empty:
        return summ
    summ.to_csv(cfg.figures_dir() / "colocalization_summary.csv")

    frac_cols = [v for v in adata.var_names if v.startswith("coloc_") and v.endswith("_frac")]
    raw = pd.DataFrame(adata.layers["raw"], columns=list(adata.var_names))[frac_cols]
    raw["condition"] = adata.obs["condition"].to_numpy()
    means = raw.groupby("condition").mean()
    fig, ax = plt.subplots(figsize=(1.0 * len(means) + 3, 0.5 * len(frac_cols) + 2))
    im = ax.imshow(means.T.to_numpy(), aspect="auto", cmap="viridis")
    ax.set_xticks(range(len(means))); ax.set_xticklabels(means.index, rotation=45, ha="right")
    ax.set_yticks(range(len(frac_cols))); ax.set_yticklabels(frac_cols, fontsize=7)
    ax.set_title("Colocalized fraction (mean per nucleus)")
    fig.colorbar(im, ax=ax, shrink=0.6)
    fig.tight_layout()
    fig.savefig(cfg.figures_dir() / "colocalization_fraction.png", dpi=150)
    plt.close(fig)
    return summ
