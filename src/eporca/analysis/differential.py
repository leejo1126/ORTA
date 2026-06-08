"""Per-condition differential feature analysis vs the control condition.

For every feature, compares each perturbation to control with a Mann-Whitney U
test (p-value) and Cliff's delta (effect size in [-1, 1]); p-values are
BH-FDR corrected per condition. Produces a tidy table and an effect-size heatmap.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from ..config import Config


def _cliffs_delta(a, b) -> float:
    a, b = np.asarray(a), np.asarray(b)
    if a.size == 0 or b.size == 0:
        return np.nan
    # P(a>b) - P(a<b) via rank comparison (O(n log n))
    from scipy.stats import rankdata
    all_v = np.concatenate([a, b])
    r = rankdata(all_v)
    ra = r[: a.size].sum()
    u = ra - a.size * (a.size + 1) / 2.0          # Mann-Whitney U for a
    return float(2.0 * u / (a.size * b.size) - 1.0)


def _bh(pvals) -> np.ndarray:
    p = np.asarray(pvals, float)
    ok = ~np.isnan(p)
    q = np.full_like(p, np.nan)
    if ok.sum() == 0:
        return q
    pv = p[ok]
    order = np.argsort(pv)
    m = pv.size
    adj = pv[order] * m / (np.arange(m) + 1)
    adj = np.minimum.accumulate(adj[::-1])[::-1]
    out = np.empty(m)
    out[order] = np.clip(adj, 0, 1)
    q[ok] = out
    return q


def differential_table(adata, cfg: Config) -> pd.DataFrame:
    from scipy.stats import mannwhitneyu

    raw = pd.DataFrame(adata.layers["raw"], columns=list(adata.var_names))
    raw["condition"] = adata.obs["condition"].to_numpy()
    ctrl = cfg.analysis.control_condition

    rows = []
    ctrl_df = raw[raw["condition"] == ctrl]
    for cond in [c for c in raw["condition"].unique() if c != ctrl]:
        cond_df = raw[raw["condition"] == cond]
        pvals, recs = [], []
        for feat in adata.var_names:
            a, b = cond_df[feat].dropna().to_numpy(), ctrl_df[feat].dropna().to_numpy()
            if a.size < 3 or b.size < 3:
                p, d = np.nan, np.nan
            else:
                try:
                    p = mannwhitneyu(a, b, alternative="two-sided").pvalue
                except ValueError:
                    p = np.nan
                d = _cliffs_delta(a, b)
            pvals.append(p)
            recs.append({"condition": cond, "feature": feat, "cliffs_delta": d,
                         "p": p, "median_cond": np.median(a) if a.size else np.nan,
                         "median_ctrl": np.median(b) if b.size else np.nan})
        q = _bh(pvals)
        for r, qq in zip(recs, q):
            r["padj"] = qq
        rows.extend(recs)
    return pd.DataFrame(rows)


def run(adata, cfg: Config) -> pd.DataFrame:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    tab = differential_table(adata, cfg)
    cfg.figures_dir().mkdir(parents=True, exist_ok=True)
    tab.to_csv(cfg.figures_dir() / "differential_vs_control.csv", index=False)

    if not tab.empty:
        piv = tab.pivot(index="feature", columns="condition", values="cliffs_delta")
        fig, ax = plt.subplots(figsize=(1.2 * piv.shape[1] + 3, 0.3 * piv.shape[0] + 2))
        im = ax.imshow(piv.to_numpy(), aspect="auto", cmap="RdBu_r", vmin=-1, vmax=1)
        ax.set_xticks(range(piv.shape[1])); ax.set_xticklabels(piv.columns, rotation=45, ha="right")
        ax.set_yticks(range(piv.shape[0])); ax.set_yticklabels(piv.index, fontsize=6)
        ax.set_title("Cliff's delta vs control")
        fig.colorbar(im, ax=ax, shrink=0.5, label="effect size")
        fig.tight_layout()
        fig.savefig(cfg.figures_dir() / "differential_heatmap.png", dpi=150)
        plt.close(fig)
    return tab
