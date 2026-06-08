"""
Step 3: assemble per-nucleus and per-foci feature tables for one FOV.

Inputs (from steps 1-2): the scaled nucleus mask + metrics CSV, and the
per-channel foci per-spot CSVs. Plus the raw OME-Zarr for per-nucleus channel
intensities (condensed fraction / partition coefficient) and a chromatin-context
feature (local DAPI intensity at each focus). Cross-channel colocalization
(within-nucleus nearest-neighbour distances) uses chromatic-corrected COMs.

Outputs:
  data/features/fov_<NNN>_nuclei.parquet   (one row per kept nucleus)
  data/features/fov_<NNN>_foci.parquet     (one row per focus, all channels)
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import scipy.ndimage as ndi
from scipy.spatial import cKDTree

from .config import Config
from .io_zarr import read_channel
from .foci import load_nuclear_labels_3d
from .chromatic import correct_coms_um


def _load_spots(cfg: Config, fov: int) -> pd.DataFrame:
    frames = []
    for marker in cfg.markers:
        path = cfg.foci_spot_csv(fov, marker)
        df = pd.read_csv(path)
        if len(df):
            frames.append(df)
    if not frames:
        return pd.DataFrame(columns=["fov", "marker", "condition", "nucleus"])
    return pd.concat(frames, ignore_index=True)


def _add_local_dapi(cfg: Config, fov: int, spots: pd.DataFrame) -> pd.DataFrame:
    """Mean DAPI intensity in a 3x3x3 window at each focus COM (chromatin context)."""
    if "DAPI" not in cfg.markers or spots.empty:
        spots["local_dapi"] = np.nan
        return spots
    dapi = read_channel(cfg, fov, "DAPI", trim=True).astype(np.float32)
    sm = ndi.uniform_filter(dapi, size=3)
    z = np.clip(np.rint(spots["com_z_px"]).astype(int), 0, sm.shape[0] - 1)
    y = np.clip(np.rint(spots["com_y_px"]).astype(int), 0, sm.shape[1] - 1)
    x = np.clip(np.rint(spots["com_x_px"]).astype(int), 0, sm.shape[2] - 1)
    spots["local_dapi"] = sm[z, y, x]
    return spots


def _add_coloc_nn(cfg: Config, spots: pd.DataFrame) -> pd.DataFrame:
    """For each focus, distance to the nearest focus of every other marker in the
    same nucleus (chromatic-corrected COMs). Adds nn_<marker>_um columns."""
    markers = cfg.markers
    for m in markers:
        spots[f"nn_{m}_um"] = np.nan
    if spots.empty:
        return spots

    # corrected coords per row
    coords = spots[["com_z_um", "com_y_um", "com_x_um"]].to_numpy(float)
    corr = coords.copy()
    for m in markers:
        sel = (spots["marker"] == m).to_numpy()
        if sel.any():
            corr[sel] = correct_coms_um(coords[sel], cfg, m)
    spots = spots.copy()
    spots[["_cz", "_cy", "_cx"]] = corr

    for nuc, g in spots.groupby("nucleus"):
        if nuc == 0:
            continue
        by_marker = {m: g[g["marker"] == m] for m in markers}
        trees = {m: cKDTree(by_marker[m][["_cz", "_cy", "_cx"]].to_numpy())
                 for m in markers if len(by_marker[m])}
        for a in markers:
            ga = by_marker[a]
            if not len(ga):
                continue
            pa = ga[["_cz", "_cy", "_cx"]].to_numpy()
            for b in markers:
                if b == a or b not in trees:
                    continue
                d, _ = trees[b].query(pa, k=1)
                spots.loc[ga.index, f"nn_{b}_um"] = d
    return spots.drop(columns=["_cz", "_cy", "_cx"])


def _nucleus_table(cfg: Config, fov: int, spots: pd.DataFrame) -> pd.DataFrame:
    """One row per kept nucleus: morphology + per-channel foci aggregates +
    condensed fraction / partition coefficient + colocalization summaries."""
    metrics = pd.read_csv(cfg.mask_metrics_path(fov))
    nuc = metrics[metrics["kept"] == 1].copy()
    nuc = nuc.rename(columns={"label": "nucleus", "volume_um3": "nucleus_volume_um3"})
    nuc["fov"] = fov
    nuc["condition"] = cfg.condition_for_fov(fov) or "unassigned"

    # full-res nucleus mask for per-channel intensity sums
    ref = read_channel(cfg, fov, cfg.markers[0], trim=True)
    mask = load_nuclear_labels_3d(cfg, fov, ref.shape)
    max_lab = int(mask.max())
    nuc_vox = np.bincount(mask.ravel(), minlength=max_lab + 1)
    voxel_um3 = cfg.acquisition.pixel_size_um ** 2 * cfg.acquisition.z_um
    coloc_r = cfg.analysis.colocalization.coloc_radius_um

    for marker in cfg.markers:
        raw = read_channel(cfg, fov, marker, trim=True).astype(np.float32)
        idx = np.arange(1, max_lab + 1)
        tot = ndi.sum_labels(raw, mask, index=idx)             # per-nucleus total intensity
        tot_by_lab = dict(zip(idx, tot))

        sm = spots[spots["marker"] == marker]
        grp = sm.groupby("nucleus")
        agg = grp.agg(
            n_foci=("spot_label", "size"),
            foci_vol_mean=("volume_um3", "mean"),
            foci_vol_median=("volume_um3", "median"),
            foci_vol_std=("volume_um3", "std"),
            foci_int_total=("integrated_intensity", "sum"),
            foci_mean_int=("mean_intensity", "mean"),
            local_dapi_mean=("local_dapi", "mean"),
        )

        def per_nuc(row):
            lab = int(row["nucleus"])
            a = agg.loc[lab] if lab in agg.index else None
            n = int(a["n_foci"]) if a is not None else 0
            vol_um3 = row["nucleus_volume_um3"]
            nvox = nuc_vox[lab] if lab <= max_lab else 0
            total_int = tot_by_lab.get(lab, 0.0)
            foci_int = float(a["foci_int_total"]) if a is not None else 0.0
            foci_vox = (float(a["foci_vol_mean"]) * n / voxel_um3) if a is not None and n else 0.0
            nucleoplasm_vox = max(nvox - foci_vox, 1.0)
            cond_frac = foci_int / total_int if total_int else 0.0
            cond_mean = foci_int / max(foci_vox, 1.0) if foci_vox else 0.0
            nucpl_mean = (total_int - foci_int) / nucleoplasm_vox
            partition = cond_mean / nucpl_mean if nucpl_mean else np.nan
            return pd.Series({
                f"{marker}_n_foci": n,
                f"{marker}_density_per_um3": n / vol_um3 if vol_um3 else 0.0,
                f"{marker}_foci_vol_mean_um3": float(a["foci_vol_mean"]) if a is not None else 0.0,
                f"{marker}_foci_vol_median_um3": float(a["foci_vol_median"]) if a is not None else 0.0,
                f"{marker}_foci_vol_cv": (float(a["foci_vol_std"]) / float(a["foci_vol_mean"])
                                          if a is not None and a["foci_vol_mean"] else 0.0),
                f"{marker}_condensed_fraction": cond_frac,
                f"{marker}_partition_coefficient": partition,
                f"{marker}_mean_foci_intensity": float(a["foci_mean_int"]) if a is not None else 0.0,
                f"{marker}_foci_local_dapi": float(a["local_dapi_mean"]) if a is not None else np.nan,
            })

        nuc = pd.concat([nuc, nuc.apply(per_nuc, axis=1)], axis=1)

    # colocalization summaries per nucleus from the per-foci NN columns
    for a, b in cfg.analysis.colocalization.pairs:
        col = f"nn_{b}_um"
        sub = spots[(spots["marker"] == a) & spots[col].notna()]
        if sub.empty:
            nuc[f"coloc_{a}_{b}_frac"] = np.nan
            nuc[f"coloc_{a}_{b}_nn_um"] = np.nan
            continue
        g = sub.groupby("nucleus")[col]
        frac = g.apply(lambda s: float(np.mean(s < coloc_r)))
        med = g.median()
        nuc[f"coloc_{a}_{b}_frac"] = nuc["nucleus"].map(frac)
        nuc[f"coloc_{a}_{b}_nn_um"] = nuc["nucleus"].map(med)
    return nuc


def features_fov(cfg: Config, fov: int) -> dict:
    """Build and save per-nucleus and per-foci feature tables for one FOV."""
    spots = _load_spots(cfg, fov)
    spots = _add_local_dapi(cfg, fov, spots)
    spots = _add_coloc_nn(cfg, spots)
    nuclei = _nucleus_table(cfg, fov, spots)

    spots.to_parquet(cfg.features_foci_path(fov), index=False)
    nuclei.to_parquet(cfg.features_nuclei_path(fov), index=False)
    return {"fov": fov, "n_nuclei": len(nuclei), "n_foci": len(spots)}
