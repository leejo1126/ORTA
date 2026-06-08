"""PCA -> UMAP -> Leiden on the per-nucleus matrix, written back into AnnData."""

from __future__ import annotations

import numpy as np

from ..config import Config


def compute_embedding(adata, cfg: Config) -> None:
    """Add obsm['X_pca'], obsm['X_umap'] and obs['leiden'] to `adata` in place."""
    from sklearn.decomposition import PCA

    n_pcs = min(cfg.analysis.clustering.n_pcs, adata.n_vars, max(adata.n_obs - 1, 1))
    seed = cfg.analysis.random_seed
    X = np.nan_to_num(np.asarray(adata.X, dtype=np.float32))

    pcs = PCA(n_components=n_pcs, random_state=seed).fit_transform(X)
    adata.obsm["X_pca"] = pcs

    try:
        import umap
        adata.obsm["X_umap"] = umap.UMAP(
            n_neighbors=cfg.analysis.clustering.n_neighbors, random_state=seed,
        ).fit_transform(pcs)
    except Exception as e:  # umap optional / may fail on tiny data
        adata.uns["umap_error"] = str(e)

    adata.obs["leiden"] = _leiden(pcs, cfg).astype(str)
    adata.obs["leiden"] = adata.obs["leiden"].astype("category")


def _leiden(pcs, cfg: Config):
    """Leiden clustering on a kNN graph of the PCA space; fallback to KMeans."""
    n = pcs.shape[0]
    k = min(cfg.analysis.clustering.n_neighbors, max(n - 1, 1))
    try:
        import igraph as ig
        import leidenalg
        from sklearn.neighbors import NearestNeighbors

        nn = NearestNeighbors(n_neighbors=k + 1).fit(pcs)
        _, idx = nn.kneighbors(pcs)
        edges = {(min(i, j), max(i, j)) for i, row in enumerate(idx) for j in row[1:]}
        g = ig.Graph(n=n, edges=list(edges))
        part = leidenalg.find_partition(
            g, leidenalg.RBConfigurationVertexPartition,
            resolution_parameter=cfg.analysis.clustering.leiden_resolution,
            seed=cfg.analysis.random_seed,
        )
        return np.asarray(part.membership)
    except Exception:
        from sklearn.cluster import KMeans
        kk = min(8, max(2, n // 50))
        return KMeans(n_clusters=kk, random_state=cfg.analysis.random_seed,
                      n_init=10).fit_predict(pcs)
