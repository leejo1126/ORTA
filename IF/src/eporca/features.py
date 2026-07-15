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
from .qc.beads import flag_beads


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


def _add_local_intensities(cfg: Config, spots: pd.DataFrame, channels: dict, mask) -> pd.DataFrame:
    """Mean intensity of EVERY marker in a 3x3x3 window at each focus COM, plus a
    flat-field-robust enrichment ratio local_<M>_enr = local_<M> / (that nucleus's
    mean of channel M). Because illumination shading varies over the ~240um FOV but is
    ~constant within a ~10um nucleus, the ratio cancels it -- so local_<M>_enr measures
    'how much M sits at this focus vs its nuclear background' independent of FOV position.
    local_DAPI is chromatin context; local_Brd4 etc. let us ask e.g. is Brd4 recruited to
    a Pol2 focus (density-robust, unlike nearest-neighbour colocalization).
    (local_dapi kept as an alias for backward-compatible nucleus features.)"""
    markers = cfg.markers
    for m in markers:
        spots[f"local_{m}"] = np.nan
        spots[f"local_{m}_enr"] = np.nan
    spots["local_dapi"] = np.nan
    if spots.empty:
        return spots
    ref = channels[markers[0]]
    z = np.clip(np.rint(spots["com_z_px"]).astype(int), 0, ref.shape[0] - 1)
    y = np.clip(np.rint(spots["com_y_px"]).astype(int), 0, ref.shape[1] - 1)
    x = np.clip(np.rint(spots["com_x_px"]).astype(int), 0, ref.shape[2] - 1)
    max_lab = int(mask.max())
    cnt = np.bincount(mask.ravel(), minlength=max_lab + 1)
    nuc_of = np.clip(spots["nucleus"].fillna(0).astype(int).to_numpy(), 0, max_lab)
    for m in markers:
        ch = channels[m]
        loc = ndi.uniform_filter(ch, size=3)[z, y, x]
        spots[f"local_{m}"] = loc
        mean_by = np.zeros(max_lab + 1, np.float64)
        idx = np.arange(1, max_lab + 1)
        mean_by[idx] = ndi.sum_labels(ch, mask, index=idx) / np.maximum(cnt[idx], 1)
        denom = mean_by[nuc_of]
        spots[f"local_{m}_enr"] = np.where(denom > 0, loc / denom, np.nan)
    spots["local_dapi"] = spots.get("local_DAPI", np.nan)
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

    is_bead = spots["is_bead"] if "is_bead" in spots.columns else pd.Series(False, index=spots.index)
    for nuc, g in spots.groupby("nucleus"):
        if nuc == 0:
            continue
        greal = g[~is_bead.loc[g.index]]                       # beads are not colocalization partners
        # trees from real foci only; query ALL foci (beads get NN to real foci)
        trees = {m: cKDTree(gm[["_cz", "_cy", "_cx"]].to_numpy())
                 for m in markers if len(gm := greal[greal["marker"] == m])}
        for a in markers:
            ga = g[g["marker"] == a]
            if not len(ga):
                continue
            pa = ga[["_cz", "_cy", "_cx"]].to_numpy()
            for b in markers:
                if b == a or b not in trees:
                    continue
                d, _ = trees[b].query(pa, k=1)
                spots.loc[ga.index, f"nn_{b}_um"] = d
    return spots.drop(columns=["_cz", "_cy", "_cx"])


def _nucleus_table(cfg: Config, fov: int, spots: pd.DataFrame, channels: dict, mask) -> pd.DataFrame:
    """One row per kept nucleus: morphology + per-channel foci aggregates +
    condensed fraction / partition coefficient + colocalization summaries.
    `channels` (marker->trimmed image) and `mask` are read once by the caller."""
    metrics = pd.read_csv(cfg.mask_metrics_path(fov))
    nuc = metrics[metrics["kept"] == 1].copy()
    nuc = nuc.rename(columns={"label": "nucleus", "volume_um3": "nucleus_volume_um3"})
    nuc["fov"] = fov
    nuc["condition"] = cfg.condition_for_fov(fov) or "unassigned"

    max_lab = int(mask.max())
    nuc_vox = np.bincount(mask.ravel(), minlength=max_lab + 1)
    voxel_um3 = cfg.acquisition.pixel_size_um ** 2 * cfg.acquisition.z_um
    coloc_r = cfg.analysis.colocalization.coloc_radius_um

    for marker in cfg.markers:
        raw = channels[marker]
        idx = np.arange(1, max_lab + 1)
        tot = ndi.sum_labels(raw, mask, index=idx)             # per-nucleus total intensity
        tot_by_lab = dict(zip(idx, tot))

        bead_col = spots["is_bead"] if "is_bead" in spots.columns else pd.Series(False, index=spots.index)
        is_m = spots["marker"] == marker
        sm = spots[is_m & ~bead_col]                 # real foci only (beads excluded)
        smb = spots[is_m & bead_col]                 # bead / bright-artifact foci
        bead_int_by = smb.groupby("nucleus")["integrated_intensity"].sum().to_dict()
        n_beads_by = smb.groupby("nucleus").size().to_dict()
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
            foci_int = float(a["foci_int_total"]) if a is not None else 0.0
            # subtract bead intensity from the whole-nucleus denominator too
            total_int = max(tot_by_lab.get(lab, 0.0) - bead_int_by.get(lab, 0.0), foci_int)
            foci_vox = (float(a["foci_vol_mean"]) * n / voxel_um3) if a is not None and n else 0.0
            nucleoplasm_vox = max(nvox - foci_vox, 1.0)
            cond_frac = foci_int / total_int if total_int else 0.0
            cond_mean = foci_int / max(foci_vox, 1.0) if foci_vox else 0.0
            nucpl_mean = (total_int - foci_int) / nucleoplasm_vox
            partition = cond_mean / nucpl_mean if nucpl_mean else np.nan
            return pd.Series({
                f"{marker}_n_foci": n,
                f"{marker}_n_beads": int(n_beads_by.get(lab, 0)),
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

    # colocalization summaries per nucleus from the per-foci NN columns (beads excluded).
    # coloc_<a>_<b>_enrich = observed frac / expected-if-random: the expected fraction of
    # a-foci within coloc_r of a b-focus if a-foci were placed uniformly at random, given
    # the b-focus density (1 - (1 - Vball/Vnuc)^n_b). >1 = colocalized above chance. This is
    # spatial/density-based so it is immune to flat-field intensity variation, and it corrects
    # for the fact that a dense marker (e.g. Brd4, ~700 foci/nucleus) colocalizes ~everything
    # trivially -- raw frac then saturates near 1 and hides real enrichment.
    bead_all = spots["is_bead"] if "is_bead" in spots.columns else pd.Series(False, index=spots.index)
    ball_v = (4.0 / 3.0) * np.pi * coloc_r ** 3
    Vnuc = nuc["nucleus_volume_um3"].to_numpy()
    for a, b in cfg.analysis.colocalization.pairs:
        col = f"nn_{b}_um"
        nb = spots[(spots["marker"] == b) & ~bead_all].groupby("nucleus").size()
        nb_map = nuc["nucleus"].map(nb).fillna(0.0).to_numpy()
        exp = 1.0 - np.power(1.0 - np.minimum(ball_v / np.maximum(Vnuc, 1e-9), 1.0), nb_map)
        sub = spots[(spots["marker"] == a) & ~bead_all & spots[col].notna()]
        if sub.empty:
            nuc[f"coloc_{a}_{b}_frac"] = np.nan
            nuc[f"coloc_{a}_{b}_nn_um"] = np.nan
            nuc[f"coloc_{a}_{b}_enrich"] = np.nan
            continue
        g = sub.groupby("nucleus")[col]
        nuc[f"coloc_{a}_{b}_frac"] = nuc["nucleus"].map(g.apply(lambda s: float(np.mean(s < coloc_r))))
        nuc[f"coloc_{a}_{b}_nn_um"] = nuc["nucleus"].map(g.median())
        obs = nuc[f"coloc_{a}_{b}_frac"].to_numpy()
        nuc[f"coloc_{a}_{b}_enrich"] = np.where(exp > 0, obs / exp, np.nan)
    return nuc


def features_fov(cfg: Config, fov: int) -> dict:
    """Build and save per-nucleus and per-foci feature tables for one FOV. A FOV
    with no kept nuclei (e.g. a bad/out-of-focus FOV rejected by the QC filters) is
    written as empty tables instead of crashing, so the batch continues."""
    metrics = pd.read_csv(cfg.mask_metrics_path(fov))
    if "kept" not in metrics or int((metrics["kept"] == 1).sum()) == 0:
        pd.DataFrame({"fov": []}).to_parquet(cfg.features_nuclei_path(fov), index=False)
        pd.DataFrame({"fov": []}).to_parquet(cfg.features_foci_path(fov), index=False)
        return {"fov": fov, "n_nuclei": 0, "n_foci": 0, "status": "no_nuclei"}

    spots = _load_spots(cfg, fov)
    spots["is_bead"] = flag_beads(spots, cfg)   # fiducial-bead / bright-artifact QC flag
    # read each channel + the nucleus mask once; share across local-intensity and nucleus aggregation
    channels = {m: read_channel(cfg, fov, m, trim=True).astype(np.float32) for m in cfg.markers}
    mask = load_nuclear_labels_3d(cfg, fov, channels[cfg.markers[0]].shape)
    spots = _add_local_intensities(cfg, spots, channels, mask)
    spots = _add_coloc_nn(cfg, spots)
    nuclei = _nucleus_table(cfg, fov, spots, channels, mask)

    spots.to_parquet(cfg.features_foci_path(fov), index=False)
    nuclei.to_parquet(cfg.features_nuclei_path(fov), index=False)
    return {"fov": fov, "n_nuclei": len(nuclei), "n_foci": len(spots)}
