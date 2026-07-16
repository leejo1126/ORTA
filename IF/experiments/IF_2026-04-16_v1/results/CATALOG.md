# Results catalog — experiment `IF_2026-04-16_v1`

Curated keeper outputs for this run. Each row **is** the note. Curated in Phase 2a from
`IF/data/figures/`. All figures regenerate from this run's config:
`eporca analyze --config config.snapshot.yaml` (module `eporca.analysis.*`); the source dump under the
gitignored `IF/data/figures/` is transient. Numbers in "What it says" are read straight from the tables;
**biological interpretation is the analyst's to confirm** (marked ⇒).

## Figures

| File | What it is | How generated | How to read | What it says |
|---|---|---|---|---|
| `figures/umap_condition.png` | UMAP of per-nucleus feature space, colored by drug condition | `eporca analyze` → `analysis.dimreduction` (PCA n_pcs=20 → UMAP) | each dot = one nucleus; color = condition; proximity = similar multi-marker profile | ⇒ do conditions separate in feature space? (visual) |
| `figures/umap_leiden.png` | Same UMAP colored by Leiden cluster (res=1.0) | `analysis.dimreduction` (Leiden, 12 clusters 0–11) | dot = nucleus; color = cluster id | ⇒ cluster structure of nuclei; see `token_composition` for how clusters map to conditions |
| `figures/differential_heatmap.png` | Per-marker feature changes vs control, per condition | `analysis.differential` (see `differential_vs_control.csv`) | rows = features, cols = conditions; color = effect vs control | ⇒ which features move under each drug |
| `figures/colocalization_fraction.png` | Colocalized fraction for the 3 marker pairs across conditions | `analysis.colocalization` (coloc_radius 0.4µm, 50 random nulls) | bars/points per condition per pair (Brd4–Pol2, Pol2–Sc35, Brd4–Sc35) | Brd4–Pol2 enrichment ~1.7–2.0× random (control 1.74); triptolide lowest (~1.37) ⇒ pairs colocalize above chance |
| `figures/response_fingerprint.png` | Multi-feature "fingerprint" of each condition's response | `analysis.biology`/`differential` (see `response_fingerprint.csv`) | one profile per condition across summary features | ⇒ per-condition response signature |
| `figures/token_composition.png` | Stacked Leiden-cluster composition per condition | `analysis.dimreduction` (see `token_composition.csv`) | stacked bars: cluster fractions per condition | triptolide 80% cluster 0; drb 34% c0 + 44% c6; tsa 60% c7; control/jq1/eed226/sgc/auxin spread across c1–c5 ⇒ transcription inhibitors collapse nuclei into distinct clusters |
| `figures/correlation/corr_<cond>.{png,csv}` | Per-condition marker–feature correlation matrix (8 conditions) | `analysis.correlation` | heatmap of pairwise feature correlations, one per condition | ⇒ compare correlation structure across drugs |

## Tables

| File | What it is | What it says |
|---|---|---|
| `tables/differential_vs_control.csv` | Per-condition per-marker feature deltas vs control (input to the heatmap) | 8 conditions × per-marker features |
| `tables/colocalization_summary.csv` | Coloc fraction / NN-distance / enrichment, mean+median+count, per pair per condition | Brd4–Pol2 enrich ~1.74 (control) → 1.37 (triptolide); Pol2–Sc35 NN rises under drb/triptolide |
| `tables/token_composition.csv` | Leiden cluster fractions (0–11) per condition | source of the composition figure (numbers above) |
| `tables/heterogeneity_cv.csv` | Per-condition per-marker CVs of foci density/volume/condensed-fraction/partition/intensity + coloc | cell-to-cell heterogeneity per feature |
| `tables/response_fingerprint.csv` | Summary response vector per condition | source of the fingerprint figure |
| `tables/bead_quantification.csv` | Per-marker foci counts + % panchromatic/bead-like (fiducial-bead QC) | Brd4 24.2M foci (0.05% bead-like), Sc35 1.0M (0.35%), Pol2 265k (2.56% panchromatic — highest), DAPI 416k ⇒ bead bleed is a small but Pol2-weighted fraction (see `[[bead-contamination]]`) |

## Keeper-by-reference (not tracked — too large for git)

| Path | What it is | How to regenerate |
|---|---|---|
| `IF/data/figures/cluster_reps/` | Representative-cell 3D TIFF crops, one per Leiden cluster (`rep_c##_<cond>_fov###_n###.tif`, ~1.2 GB each) + `README.txt` | `eporca analyze` (cluster-representative export step) |

<!-- Scratch left in the gitignored IF/data/figures/ (transient, not curated): the 8x ~1.2GB Fiji QC
TIFFs (autofoci_fiji_*, foci_fiji_*), agent_tune_* tuning iterations, qc_foci* (incl. v2/v3),
cluster_foci_qc* (incl. _fixed), bead_check.png, overlay_labels_fov000.png. -->
