"""
Biology-driven readouts tailored to the imaged molecules (Brd4, Pol2, Sc35,
DAPI) and the perturbations (auxin/Rad21, JQ1, SGC-CBP30, DRB, triptolide,
EED226, TSA).

Each function writes a table + figure to the figures dir. These build on the
generic analyses (differential, dimreduction) and encode falsifiable
expectations (e.g. JQ1 should dissolve Brd4 condensates; DRB should round Sc35
speckles; TSA/EED226 should decompact DAPI chromocenters).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..config import Config


def _raw_df(adata) -> pd.DataFrame:
    df = pd.DataFrame(adata.layers["raw"], columns=list(adata.var_names))
    df["condition"] = adata.obs["condition"].to_numpy()
    return df


def response_fingerprint(adata, cfg: Config):
    """Heatmap of Cliff's delta (vs control) for headline per-marker features."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from .differential import differential_table

    tab = differential_table(adata, cfg)
    if tab.empty:
        return tab
    keys = ("_n_foci", "_density_per_um3", "_condensed_fraction",
            "_partition_coefficient", "_foci_vol_median_um3", "coloc_")
    sub = tab[tab["feature"].str.contains("|".join(keys))]
    piv = sub.pivot(index="feature", columns="condition", values="cliffs_delta")
    cfg.figures_dir().mkdir(parents=True, exist_ok=True)
    piv.to_csv(cfg.figures_dir() / "response_fingerprint.csv")

    fig, ax = plt.subplots(figsize=(1.1 * piv.shape[1] + 4, 0.32 * piv.shape[0] + 2))
    im = ax.imshow(piv.to_numpy(), aspect="auto", cmap="RdBu_r", vmin=-1, vmax=1)
    ax.set_xticks(range(piv.shape[1])); ax.set_xticklabels(piv.columns, rotation=45, ha="right")
    ax.set_yticks(range(piv.shape[0])); ax.set_yticklabels(piv.index, fontsize=7)
    ax.set_title("Perturbation response fingerprint (Cliff's delta vs control)")
    fig.colorbar(im, ax=ax, shrink=0.5)
    fig.tight_layout()
    fig.savefig(cfg.figures_dir() / "response_fingerprint.png", dpi=150)
    plt.close(fig)
    return piv


def token_composition(adata, cfg: Config):
    """Fraction of each Leiden nuclear-state 'token' per condition (stacked bar)."""
    if "leiden" not in adata.obs:
        return None
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    ct = pd.crosstab(adata.obs["condition"], adata.obs["leiden"], normalize="index")
    cfg.figures_dir().mkdir(parents=True, exist_ok=True)
    ct.to_csv(cfg.figures_dir() / "token_composition.csv")

    fig, ax = plt.subplots(figsize=(1.0 * len(ct) + 3, 4))
    bottom = np.zeros(len(ct))
    for col in ct.columns:
        ax.bar(ct.index, ct[col], bottom=bottom, label=f"state {col}")
        bottom += ct[col].to_numpy()
    ax.set_ylabel("fraction of nuclei"); ax.set_title("Nuclear-state composition per condition")
    ax.legend(bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=7)
    plt.xticks(rotation=45, ha="right")
    fig.tight_layout()
    fig.savefig(cfg.figures_dir() / "token_composition.png", dpi=150)
    plt.close(fig)
    return ct


def heterogeneity(adata, cfg: Config):
    """Per-condition cell-to-cell heterogeneity (CV) of each feature."""
    df = _raw_df(adata)
    g = df.groupby("condition")
    cv = g.std(numeric_only=True) / g.mean(numeric_only=True).abs().replace(0, np.nan)
    cfg.figures_dir().mkdir(parents=True, exist_ok=True)
    cv.to_csv(cfg.figures_dir() / "heterogeneity_cv.csv")
    return cv


def umap_plot(adata, cfg: Config):
    if "X_umap" not in adata.obsm:
        return
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    emb = adata.obsm["X_umap"]
    cfg.figures_dir().mkdir(parents=True, exist_ok=True)
    for color in ("condition", "leiden"):
        if color not in adata.obs:
            continue
        cats = adata.obs[color].astype("category")
        fig, ax = plt.subplots(figsize=(7, 6))
        for i, c in enumerate(cats.cat.categories):
            m = (cats == c).to_numpy()
            ax.scatter(emb[m, 0], emb[m, 1], s=3, label=str(c), alpha=0.6)
        ax.set_title(f"UMAP - {color}"); ax.set_xlabel("UMAP1"); ax.set_ylabel("UMAP2")
        ax.legend(markerscale=3, bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=7)
        fig.tight_layout()
        fig.savefig(cfg.figures_dir() / f"umap_{color}.png", dpi=150)
        plt.close(fig)


def run_all(adata, cfg: Config) -> None:
    response_fingerprint(adata, cfg)
    token_composition(adata, cfg)
    heterogeneity(adata, cfg)
    umap_plot(adata, cfg)
