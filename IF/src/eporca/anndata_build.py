"""
Step 5: aggregate per-FOV feature tables into AnnData objects.

  nuclei.h5ad  (primary)  obs = nuclei (fov, condition, drug_target, volume, ...)
                          X   = z-scored per-nucleus feature matrix (layers['raw'])
                          obsm['spatial'] = nucleus COM (z,y,x um)
                          + X_pca / X_umap / leiden added by analysis.dimreduction
  foci.h5ad    (secondary) obs = individual foci (channel, nucleus, condition, COM,
                          volume, intensities, local DAPI, NN distances)

Run after step 3 for all desired FOVs.
"""

from __future__ import annotations

import glob
import numpy as np
import pandas as pd

from .config import Config

# Per-nucleus columns that are metadata (obs) rather than model features (X).
_NUC_META = ["fov", "condition", "drug_target", "nucleus", "nucleus_volume_um3",
             "circularity", "com_z_um", "com_y_um", "com_x_um", "volume_vox", "kept"]


def _gather(paths) -> pd.DataFrame:
    frames = [pd.read_parquet(p) for p in paths]
    frames = [f for f in frames if len(f)]
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def build_nuclei_anndata(cfg: Config) -> str:
    import anndata as ad

    paths = sorted(glob.glob(str(cfg.data_dir / "features" / "fov_*_nuclei.parquet")))
    df = _gather(paths)
    if df.empty:
        raise RuntimeError("no per-nucleus feature parquet files found")

    # drug_target from condition map
    tmap = {k: v.drug_target for k, v in cfg.conditions.items()}
    df["drug_target"] = df["condition"].map(tmap).fillna("none")

    feat_cols = [c for c in df.columns
                 if c not in _NUC_META and pd.api.types.is_numeric_dtype(df[c])]
    raw = df[feat_cols].to_numpy(dtype=np.float32)
    raw = np.nan_to_num(raw, nan=0.0, posinf=0.0, neginf=0.0)
    mu, sd = raw.mean(0), raw.std(0)
    sd[sd == 0] = 1.0
    X = (raw - mu) / sd

    obs = df[[c for c in _NUC_META if c in df.columns]].copy()
    obs.index = [f"fov{int(r.fov):03d}_n{int(r.nucleus)}" for r in df.itertuples()]
    for c in ("condition", "drug_target"):
        obs[c] = obs[c].astype("category")

    adata = ad.AnnData(X=X, obs=obs)
    adata.var_names = feat_cols
    adata.layers["raw"] = raw
    adata.obsm["spatial"] = df[["com_z_um", "com_y_um", "com_x_um"]].to_numpy(np.float32)
    adata.uns["eporca"] = {
        "markers": cfg.markers,
        "conditions": {k: v.model_dump() for k, v in cfg.conditions.items()},
        "control_condition": cfg.analysis.control_condition,
        "feature_zscore": {"mean": mu.tolist(), "std": sd.tolist()},
    }
    out = cfg.anndata_path("nuclei")
    adata.write_h5ad(out)
    return out


def build_foci_anndata(cfg: Config) -> str:
    import anndata as ad

    paths = sorted(glob.glob(str(cfg.data_dir / "features" / "fov_*_foci.parquet")))
    df = _gather(paths)
    if df.empty:
        raise RuntimeError("no per-foci feature parquet files found")

    meta = ["fov", "marker", "condition", "spot_label", "nucleus",
            "com_z_um", "com_y_um", "com_x_um", "com_z_px", "com_y_px", "com_x_px"]
    feat_cols = [c for c in df.columns
                 if c not in meta and pd.api.types.is_numeric_dtype(df[c])]
    raw = np.nan_to_num(df[feat_cols].to_numpy(np.float32))

    obs = df[[c for c in meta if c in df.columns]].copy()
    obs.index = [f"fov{int(r.fov):03d}_{r.marker}_{int(r.spot_label)}" for r in df.itertuples()]
    for c in ("marker", "condition"):
        obs[c] = obs[c].astype("category")

    adata = ad.AnnData(X=raw, obs=obs)
    adata.var_names = feat_cols
    adata.obsm["spatial"] = df[["com_z_um", "com_y_um", "com_x_um"]].to_numpy(np.float32)
    out = cfg.anndata_path("foci")
    adata.write_h5ad(out)
    return out


def build_all(cfg: Config, embed: bool = True) -> dict:
    cfg.ensure_dirs()
    nuc = build_nuclei_anndata(cfg)
    foci = build_foci_anndata(cfg)
    if embed:
        from .analysis.dimreduction import compute_embedding
        import anndata as ad
        adata = ad.read_h5ad(nuc)
        compute_embedding(adata, cfg)
        adata.write_h5ad(nuc)
    return {"nuclei": nuc, "foci": foci}
