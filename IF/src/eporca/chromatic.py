"""
Chromatic-aberration correction via a multi-channel bead calibration.

Estimates ALL-TO-ALL 3D polynomial (degree 3) transforms between channels
(647/561/488/405) from a bead image, so any channel's coordinates can be mapped
into any other channel's frame (e.g. to push DNA loci between frames and ask
whether a locus sits inside a focus / how far from its surface).

Bead sources (config.chromatic.beads): 647/561/488 from the 4-channel
`beads_*.dax` (idx 0/1/2); 405 from a separate `405_only_*.dax` (tetraspecks
image poorly at 405). Beads are 3D-Gaussian localized per channel, matched across
channels per FOV (coarse phase-correlation seeds the match; the separate 405
acquisition's stage offset is removed so its transform is chromatic-only), pooled
across bead FOVs, then a per-ordered-pair 3D cubic is least-squares fit. 405 is
coarse (micron-scale) by design.

Build/run: `eporca chromatic-calibrate`. Applied to data only when
config.chromatic.mode == "polynomial" (off by default).

Also keeps a constant-offset fallback (offset_um / correct_coms_um) used by
features when no polynomial calibration is active.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from .config import Config


# ----------------------------------------------------- constant-offset fallback
def offset_um(cfg: Config, marker: str) -> np.ndarray:
    dz, dy, dx = cfg.chromatic.offsets_vox.get(marker, [0.0, 0.0, 0.0])
    return np.array([dz * cfg.acquisition.z_um, dy * cfg.acquisition.pixel_size_um,
                     dx * cfg.acquisition.pixel_size_um], dtype=float)


def correct_coms_um(coms_zyx_um: np.ndarray, cfg: Config, marker: str) -> np.ndarray:
    if coms_zyx_um.size == 0:
        return coms_zyx_um
    return coms_zyx_um - offset_um(cfg, marker)


# --------------------------------------------------------- 3D polynomial model
def _exps(degree: int):
    return [(a, b, c) for d in range(degree + 1) for a in range(d + 1)
            for b in range(d + 1 - a) for c in [d - a - b]]


def _features(P, exps):
    F = np.empty((P.shape[0], len(exps)), dtype=float)
    for i, (a, b, c) in enumerate(exps):
        F[:, i] = P[:, 0] ** a * P[:, 1] ** b * P[:, 2] ** c   # (z, y, x)
    return F


class Poly3D:
    """3D polynomial map (z,y,x) -> (z,y,x), one polynomial per output coordinate."""
    def __init__(self, exps, coeffs):
        self.exps = exps
        self.coeffs = np.asarray(coeffs)

    @classmethod
    def fit(cls, src_zyx, dst_zyx, degree):
        exps = _exps(degree)
        F = _features(src_zyx, exps)
        coeffs, *_ = np.linalg.lstsq(F, dst_zyx, rcond=None)
        return cls(exps, coeffs)

    def __call__(self, P):
        return _features(np.asarray(P, float), self.exps) @ self.coeffs


# ----------------------------------------------------------- bead localization
def _read_bead_channels(cfg: Config, fov: int) -> dict:
    """{wavelength: (z,y,x) volume}; 647/561/488 from beads dax, 405 from 405-only."""
    from .dax_reader import read_dax, read_dax_multichannel
    bc = cfg.chromatic.beads
    inter = str(Path(bc.dir) / bc.interleaved_pattern.format(i=fov))
    vol, _ = read_dax_multichannel(inter, bc.n_channels_interleaved)   # (z, C, y, x)
    base = {"647": np.asarray(vol[:, 0]), "561": np.asarray(vol[:, 1]),
            "488": np.asarray(vol[:, 2])}
    base["405"] = np.asarray(read_dax(str(Path(bc.dir) / bc.dapi_pattern.format(i=fov)))[0])
    return {wl: base[wl] for wl in bc.wavelengths}


def _localize_3d(vol, n=400, min_distance=7, thresh_pct=99.0, saturation=64000, win=5, zwin=3):
    from skimage.feature import peak_local_max
    from .registration import _fit_gaussian_3d
    mip = vol.max(axis=0)
    cand = peak_local_max(mip, min_distance=min_distance,
                          threshold_abs=np.percentile(mip, thresh_pct), num_peaks=2000)
    cand = sorted(cand, key=lambda p: -mip[p[0], p[1]])
    Z, H, W = vol.shape
    pts = []
    for y, x in cand:
        if mip[y, x] >= saturation:
            continue
        z = int(np.argmax(vol[:, y, x]))
        z0, y0, x0 = max(0, z - zwin), max(0, y - win), max(0, x - win)
        fz, fy, fx, amp, sxy, ok = _fit_gaussian_3d(
            vol[z0:min(Z, z + zwin + 1), y0:min(H, y + win + 1), x0:min(W, x + win + 1)])
        if not ok:
            continue
        pts.append((z0 + fz, y0 + fy, x0 + fx))
        if len(pts) >= n:
            break
    return np.array(pts, dtype=float) if pts else np.empty((0, 3))


def _pairwise_match(a_pts, a_mip, b_pts, b_mip, match_xy=5.0, match_z=3.0):
    """Correspondences between two channels' beads (coarse phase-corr seeds the NN
    match; fit uses ORIGINAL coords so the transform captures the real chromatic
    shift). Returns (a_matched, b_matched) in (z,y,x)."""
    from scipy.spatial import cKDTree
    from skimage.registration import phase_cross_correlation
    if len(a_pts) < 3 or len(b_pts) < 3:
        return np.empty((0, 3)), np.empty((0, 3))
    sh, _, _ = phase_cross_correlation(a_mip, b_mip, upsample_factor=10)
    b_sh = b_pts.copy(); b_sh[:, 1] += sh[0]; b_sh[:, 2] += sh[1]
    d, idx = cKDTree(a_pts[:, 1:3]).query(b_sh[:, 1:3])
    keep = (d <= match_xy) & (np.abs(a_pts[idx, 0] - b_sh[:, 0]) <= match_z)
    return a_pts[idx[keep]], b_pts[keep]


# --------------------------------------------------------------- calibration
def calibrate(cfg: Config) -> dict:
    """Estimate all-to-all 3D polynomial transforms from the bead calibration.
    Beads are matched PER PAIR (not requiring all 4 channels), so the well-imaged
    647/561/488 get many beads; 405 is coarse (separate acquisition, see notes)."""
    bc = cfg.chromatic.beads
    if bc is None:
        raise RuntimeError("config.chromatic.beads not set")
    wls = bc.wavelengths
    loc, mips = {}, {}
    for fov in bc.fovs:
        vols = _read_bead_channels(cfg, fov)
        for wl in wls:
            loc[(fov, wl)] = _localize_3d(vols[wl])
            mips[(fov, wl)] = vols[wl].max(axis=0)
        print("  bead fov %d beads/channel: %s" % (
            fov, {wl: len(loc[(fov, wl)]) for wl in wls}))

    n_terms = len(_exps(cfg.chromatic.degree))
    transforms, resid = {}, {}
    for A in wls:
        for B in wls:
            if A == B:
                continue
            srcs, dsts = [], []
            for fov in bc.fovs:
                am, bm = _pairwise_match(loc[(fov, A)], mips[(fov, A)],
                                         loc[(fov, B)], mips[(fov, B)])
                if len(am):
                    srcs.append(am); dsts.append(bm)
            if not srcs:
                resid[f"{A}->{B}"] = {"status": "no_matches", "n": 0}
                continue
            src, dst = np.concatenate(srcs), np.concatenate(dsts)
            poly = Poly3D.fit(src, dst, cfg.chromatic.degree)
            r = np.sqrt(((poly(src) - dst) ** 2).sum(1))
            transforms[(A, B)] = poly
            resid[f"{A}->{B}"] = {
                "rmse_px": float(r.mean()), "p90_px": float(np.percentile(r, 90)),
                "n": int(len(src)),
                "status": "ok" if len(src) >= 2 * n_terms else "underdetermined",
            }
    _save_calibration(cfg, transforms, wls, resid,
                      max((v.get("n", 0) for v in resid.values()), default=0))
    return resid


def _save_calibration(cfg, transforms, wavelengths, resid, n_beads):
    path = Path(cfg.chromatic.calibration_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    arrays = {"wavelengths": np.array(wavelengths),
              "exps": np.array(transforms[next(iter(transforms))].exps)}
    for (A, B), poly in transforms.items():
        arrays[f"{A}__{B}"] = poly.coeffs
    np.savez(path, **arrays)
    Path(str(path) + ".residuals.json").write_text(
        json.dumps({"n_beads": int(n_beads), "degree": cfg.chromatic.degree,
                    "residuals": resid}, indent=2))


def load_calibration(cfg: Config) -> dict:
    """Return {(A, B): Poly3D} from the saved calibration."""
    d = np.load(cfg.chromatic.calibration_path, allow_pickle=False)
    exps = [tuple(int(v) for v in e) for e in d["exps"]]
    wls = [str(w) for w in d["wavelengths"]]
    out = {}
    for A in wls:
        for B in wls:
            if f"{A}__{B}" in d:
                out[(A, B)] = Poly3D(exps, d[f"{A}__{B}"])
    return out


def apply_chromatic(coords_zyx, from_wl: str, to_wl: str, calib: dict) -> np.ndarray:
    """Map (N,3) (z,y,x) pixel coords from one channel's frame into another's."""
    if from_wl == to_wl or (from_wl, to_wl) not in calib:
        return np.asarray(coords_zyx, float)
    return calib[(from_wl, to_wl)](coords_zyx)
