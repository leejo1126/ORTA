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
class ChannelCfg(BaseModel):
    index: int
    wavelength: str
    marker: str


class PathsCfg(BaseModel):
    dax_dir: str
    data_dir: str


class InterpretersCfg(BaseModel):
    analysis: str
    cellpose: str


class AcquisitionCfg(BaseModel):
    fov_pattern: str
    n_fovs: int
    pixel_size_um: float
    z_um: float
    trim_z: int
    channels: list[ChannelCfg]


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
    tophat_radius: int
    noise_k: float
    seed_h_k: float
    min_size: int
    blur_sigma: float


class FociCfg(BaseModel):
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
        for c in self.acquisition.channels:
            if c.marker == marker:
                return c.index
        raise KeyError(f"no channel with marker {marker!r}")

    def marker_of(self, index: int) -> str:
        for c in self.acquisition.channels:
            if c.index == index:
                return c.marker
        raise KeyError(f"no channel with index {index}")

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

    def dax_path(self, fov: int) -> str:
        return str(Path(self.paths.dax_dir) / self.acquisition.fov_pattern.format(fov=fov))

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
