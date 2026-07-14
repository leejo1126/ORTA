"""
Step 5: aggregate per-FOV feature tables.

  nuclei.h5ad  (primary)   AnnData. obs = nuclei (fov, condition, drug_target, volume, ...)
                           X   = z-scored per-nucleus feature matrix (layers['raw'])
                           obsm['spatial'] = nucleus COM (z,y,x um)
                           + X_pca / X_umap / leiden added by analysis.dimreduction
  foci.parquet (secondary) A single columnar Parquet table (one row per focus: marker,
                           nucleus, condition, COM, volume, intensities, ...). Foci are
                           ~28M point detections with no variable-space to embed, so this
                           is a tidy table you query lazily (DuckDB/Polars), NOT an AnnData.
                           Built by streaming per-FOV parquet -> one writer, so the whole
                           set is never held in RAM (the old whole-dataset concat + 28M
                           itertuples index crashed h5py with a native heap corruption).

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

    # Re-derive condition from the CURRENT config (robust to parquet written under
    # an older mapping) and drop unassigned/gap FOVs.
    df["condition"] = df["fov"].map(lambda f: cfg.condition_for_fov(int(f)))
    df = df[df["condition"].notna()].reset_index(drop=True)
    if df.empty:
        raise RuntimeError("no nuclei in assigned-condition FOVs")
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


def _normalize_foci_df(df: pd.DataFrame, cfg: Config, tmap: dict) -> pd.DataFrame:
    """Re-derive condition from the CURRENT config, drop gap FOVs, add a stable
    focus_id, and pin per-column dtypes so every FOV yields an identical schema
    (streaming ParquetWriter requires it; per-FOV NaN patterns would otherwise
    flip int<->float and break the write)."""
    df = df.copy()
    df["condition"] = df["fov"].map(lambda f: cfg.condition_for_fov(int(f)))
    df = df[df["condition"].notna()]
    if df.empty:
        return df
    df["drug_target"] = df["condition"].map(tmap).fillna("none")
    df.insert(0, "focus_id",
              "fov" + df["fov"].astype(int).map("{:03d}".format)
              + "_" + df["marker"].astype(str)
              + "_" + df["spot_label"].astype(int).astype(str))
    for c in df.columns:
        if c in ("focus_id", "marker", "condition", "drug_target"):
            df[c] = df[c].astype("string")
        elif c in ("fov", "spot_label"):
            df[c] = df[c].astype("int64")
        else:  # nucleus (nullable), COMs, volumes, intensities, ... -> float32
            df[c] = pd.to_numeric(df[c], errors="coerce").astype("float32")
    return df


def build_foci_parquet(cfg: Config) -> str:
    """Stream all per-FOV foci parquet into ONE columnar table without ever
    holding the whole ~28M-row set in RAM. Foci are point detections, not an
    AnnData matrix -- query the result lazily (DuckDB/Polars).

    The table is built on LOCAL disk and copied to the (often SMB) destination in
    a single shot: holding a ParquetWriter open on a network share for the minutes
    it takes to append ~184 row groups crashes natively (Windows access violation)
    on any transient SMB hiccup. A plain sequential copy fails cleanly (retryable
    OSError) instead."""
    import os
    import shutil
    import tempfile
    import time
    import pyarrow as pa
    import pyarrow.parquet as pq

    paths = sorted(glob.glob(str(cfg.data_dir / "features" / "fov_*_foci.parquet")))
    if not paths:
        raise RuntimeError("no per-foci feature parquet files found")

    tmap = {k: v.drug_target for k, v in cfg.conditions.items()}
    out = cfg.foci_table_path()
    fd, tmp_path = tempfile.mkstemp(prefix="eporca_foci_", suffix=".parquet")
    os.close(fd)

    writer = None
    schema = None
    cols = None
    n_total = 0
    try:
        for p in paths:
            df = _normalize_foci_df(pd.read_parquet(p), cfg, tmap)
            if df.empty:
                continue
            if cols is None:
                cols = list(df.columns)
            df = df.reindex(columns=cols)  # identical column order every FOV
            table = pa.Table.from_pandas(df, preserve_index=False)
            if writer is None:
                schema = table.schema
                writer = pq.ParquetWriter(tmp_path, schema, compression="zstd")
            else:
                table = table.cast(schema)  # guard against per-FOV schema drift
            writer.write_table(table)
            n_total += table.num_rows
        if writer is not None:
            writer.close()
            writer = None
        if n_total == 0:
            raise RuntimeError("no foci in assigned-condition FOVs")
        # single-shot copy to the (possibly network) destination; retry transient SMB errors
        err = None
        for attempt in range(3):
            try:
                shutil.copyfile(tmp_path, out)
                err = None
                break
            except OSError as e:
                err = e
                time.sleep(2 * (attempt + 1))
        if err is not None:
            raise err
    finally:
        if writer is not None:
            writer.close()
        try:
            os.remove(tmp_path)
        except OSError:
            pass
    print({"foci_table": out, "n_foci": n_total})
    return out


def build_all(cfg: Config, embed: bool = True) -> dict:
    cfg.ensure_dirs()
    nuc = build_nuclei_anndata(cfg)
    foci = build_foci_parquet(cfg)
    if embed:
        from .analysis.dimreduction import compute_embedding
        import anndata as ad
        adata = ad.read_h5ad(nuc)
        compute_embedding(adata, cfg)
        adata.write_h5ad(nuc)
    return {"nuclei": nuc, "foci": foci}
