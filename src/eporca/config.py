"""
Typed configuration for the eporca pipeline.

Loads ``config/config.yaml`` (and ``config/conditions.yaml``) into validated
pydantic models and exposes helpers for channel lookups, FOV<->condition
mapping, per-marker foci parameters, and all output paths. Kept dependency-light
(pydantic + pyyaml only) so it imports in both the cellpose-gpu and analysis
environments.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel


# --- section models -----------------------------------------------------------
class SourceCfg(BaseModel):
    # where a marker's image comes from:
    #   kind="interleaved": de-interleave the multi-channel .dax, take `index`
    #   kind="file":        read a separate single-channel .dax (`pattern`)
    kind: str = "interleaved"
    index: int = 0
    pattern: Optional[str] = None


class ChannelCfg(BaseModel):
    marker: str
    wavelength: str
    source: SourceCfg = SourceCfg()


class PathsCfg(BaseModel):
    dax_dir: str
    data_dir: str


class InterpretersCfg(BaseModel):
    analysis: str
    cellpose: str


class AcquisitionCfg(BaseModel):
    interleaved_pattern: str          # the multi-channel .dax filename pattern
    n_interleaved_channels: int       # physical channels in the interleaved .dax
    n_fovs: int
    pixel_size_um: float
    z_um: float
    trim_z: int
    channels: list[ChannelCfg]        # analysis markers, in OME-Zarr channel order


class ZarrCfg(BaseModel):
    chunk_zyx: list[int]
    compressor: str = "zstd"
    clevel: int = 5


class SegmentationCfg(BaseModel):
    channel_marker: str
    diam_um: float
    cellpose_diam_px: int
    flow_threshold: float
    cellprob_threshold: float
    blur_factor: float
    batch_size: int
    use_bf16: bool
    gpu_index: int
    exclude_edge: bool
    min_volume_um3: Optional[float] = None
    max_volume_um3: Optional[float] = None
    min_circularity: Optional[float] = None
    max_circularity: Optional[float] = None


class FociParams(BaseModel):
    # detection mode: "mad" = top-hat + h-maxima + watershed (good for dense,
    # space-filling markers like Brd4); "mean_fold" = threshold at k x in-nucleus
    # mean + size gating + optional intensity-watershed (ports the MATLAB
    # findDensities recipe; good for sparse markers like Pol2/Sc35/DAPI).
    mode: str = "mad"
    # shared
    min_size: int = 10
    max_size: Optional[int] = None      # drop regions larger than this (voxels)
    blur_sigma: float = 0.0             # xy gaussian sigma applied before detection
    # --- mad mode ---
    tophat_radius: int = 5
    noise_k: float = 3.0
    seed_h_k: float = 0.5
    # --- mean_fold mode ---
    threshold: float = 2.0             # foreground = signal > threshold * mean(in-nucleus MIP)
    abs_floor: float = 0.0             # plus an absolute floor (post background subtraction)
    watershed: bool = True             # split touching bodies (intensity watershed)
    marker_h: float = 2.0             # h-maxima prominence for watershed seeds


class BackgroundCfg(BaseModel):
    # background subtracted from each channel before foci detection
    mode: str = "percentile"           # "percentile" | "constant" | "none"
    value: float = 109.0               # for "constant"
    percentile: float = 5.0            # for "percentile" (per FOV, per channel)


class FociCfg(BaseModel):
    background: BackgroundCfg = BackgroundCfg()
    defaults: FociParams
    per_marker: dict[str, FociParams] = {}
    workers: int = 1   # nucleus-level parallelism within a FOV (1 = serial)


class ChromaticCfg(BaseModel):
    reference_marker: str
    offsets_vox: dict[str, list[float]]


class ColocCfg(BaseModel):
    pairs: list[list[str]]
    coloc_radius_um: float
    n_random: int


class ClusteringCfg(BaseModel):
    n_pcs: int
    n_neighbors: int
    leiden_resolution: float


class AnalysisCfg(BaseModel):
    control_condition: str
    colocalization: ColocCfg
    clustering: ClusteringCfg
    random_seed: int


class ConditionCfg(BaseModel):
    fov_start: int
    fov_end: int
    label: str
    drug_target: str = ""


# --- top-level config ---------------------------------------------------------
class Config(BaseModel):
    paths: PathsCfg
    interpreters: InterpretersCfg
    acquisition: AcquisitionCfg
    zarr: ZarrCfg
    segmentation: SegmentationCfg
    foci: FociCfg
    chromatic: ChromaticCfg
    analysis: AnalysisCfg
    conditions: dict[str, ConditionCfg] = {}

    # ------------------------------------------------------------------ loaders
    @classmethod
    def load(cls, config_path, conditions_path: Optional[str] = None) -> "Config":
        config_path = Path(config_path)
        data = yaml.safe_load(config_path.read_text())
        cp = Path(conditions_path) if conditions_path else config_path.parent / "conditions.yaml"
        if cp.exists():
            data["conditions"] = (yaml.safe_load(cp.read_text()) or {}).get("conditions", {})
        return cls(**data)

    # ------------------------------------------------------------ channel helpers
    @property
    def markers(self) -> list[str]:
        return [c.marker for c in self.acquisition.channels]

    @property
    def n_channels(self) -> int:
        return len(self.acquisition.channels)

    def index_of(self, marker: str) -> int:
        """OME-Zarr channel index = position of the marker in the channels list."""
        for i, c in enumerate(self.acquisition.channels):
            if c.marker == marker:
                return i
        raise KeyError(f"no channel with marker {marker!r}")

    def marker_of(self, index: int) -> str:
        return self.acquisition.channels[index].marker

    def channel_of(self, marker: str) -> "ChannelCfg":
        return self.acquisition.channels[self.index_of(marker)]

    # ---------------------------------------------------------------- fov helpers
    @property
    def fovs(self) -> list[int]:
        return list(range(self.acquisition.n_fovs))

    def condition_for_fov(self, fov: int) -> Optional[str]:
        for name, c in self.conditions.items():
            if c.fov_start <= fov <= c.fov_end:
                return name
        return None

    def assigned_fovs(self) -> list[int]:
        """FOVs that fall in a defined condition range (gap FOVs excluded)."""
        return [f for f in self.fovs if self.condition_for_fov(f) is not None]

    # --------------------------------------------------------------- foci helpers
    def foci_params(self, marker: str) -> FociParams:
        return self.foci.per_marker.get(marker, self.foci.defaults)

    # --------------------------------------------------------------- path helpers
    @property
    def data_dir(self) -> Path:
        return Path(self.paths.data_dir)

    def interleaved_path(self, fov: int) -> str:
        return str(Path(self.paths.dax_dir)
                   / self.acquisition.interleaved_pattern.format(fov=fov))

    def source_path(self, fov: int, channel: "ChannelCfg") -> str:
        """The .dax file backing a channel for this FOV (interleaved or separate)."""
        if channel.source.kind == "file":
            return str(Path(self.paths.dax_dir) / channel.source.pattern.format(fov=fov))
        return self.interleaved_path(fov)

    def source_files(self, fov: int) -> list[str]:
        """Unique source .dax files needed to build this FOV's OME-Zarr."""
        seen = []
        for c in self.acquisition.channels:
            p = self.source_path(fov, c)
            if p not in seen:
                seen.append(p)
        return seen

    def zarr_path(self, fov: int) -> str:
        return str(self.data_dir / "zarr" / f"fov_{fov:03d}.zarr")

    def mask_path(self, fov: int) -> str:
        return str(self.data_dir / "masks" / f"fov_{fov:03d}_nuclei.zarr")

    def mask_metrics_path(self, fov: int) -> str:
        return str(self.data_dir / "masks" / f"fov_{fov:03d}_nuclei_metrics.csv")

    def foci_label_path(self, fov: int, marker: str) -> str:
        i = self.index_of(marker)
        return str(self.data_dir / "foci" / f"fov_{fov:03d}_c{i}_{marker}.zarr")

    def foci_spot_csv(self, fov: int, marker: str) -> str:
        i = self.index_of(marker)
        return str(self.data_dir / "foci" / f"fov_{fov:03d}_c{i}_{marker}_per_spot.csv")

    def features_nuclei_path(self, fov: int) -> str:
        return str(self.data_dir / "features" / f"fov_{fov:03d}_nuclei.parquet")

    def features_foci_path(self, fov: int) -> str:
        return str(self.data_dir / "features" / f"fov_{fov:03d}_foci.parquet")

    def anndata_path(self, kind: str) -> str:
        return str(self.data_dir / "anndata" / f"{kind}.h5ad")

    def figures_dir(self) -> Path:
        return self.data_dir / "figures"

    def ensure_dirs(self) -> None:
        for sub in ("zarr", "masks", "foci", "features", "anndata", "figures"):
            (self.data_dir / sub).mkdir(parents=True, exist_ok=True)
