# ORTA foci-tuning history

One row per tuning iteration (newest appended at the bottom). `run` is the UTC start of a tuning run; montages referenced here live in `IF/data/figures/` (regenerable, not git-tracked).

| run | iter | marker | key params | median | IQR | verdict | conf | note |
|-----|------|--------|------------|--------|-----|---------|------|------|
| 20260612T051740Z | 1 | Sc35 | mode=mean_fold, threshold=2.0, min_size=25, max_size=10000, marker_h=2.0, blur_sigma=1.0 | 36.5 | [34, 40] | pass | 0.82 | Detected foci appear as compact, discrete speckles distributed throughout the nucleoplasm, consiste… |
| 20260612T060428Z | 1 | Brd4 | mode=mad, threshold=2.0, min_size=10, max_size=None, marker_h=2.0, blur_sigma=0.3 | 1016.5 | [982, 1058] | pass | 0.72 | Median ~1017 foci/nucleus is biologically plausible for Brd4 and the montage shows dense, nucleopla… |
| 20260612T060612Z | 1 | Pol2 | mode=mean_fold, threshold=1.7, min_size=8, max_size=2000, marker_h=2.0, blur_sigma=1.0 | 6.0 | [5, 7] | fail | 0.75 | The montage shows nuclei with broadly granular Pol2 signal but virtually no colored foci overlays a… |
| 20260612T060804Z | 1 | DAPI | mode=mean_fold, threshold=1.3, min_size=100, max_size=30000, marker_h=2.0, blur_sigma=1.0 | 15.5 | [12, 18] | pass | 0.72 | Detected foci are compact, discrete bodies occupying a small fraction of the nucleoplasm, consisten… |
| 20260612T061052Z | 1 | Pol2 | mode=mean_fold, threshold=1.7, min_size=8, max_size=2000, marker_h=2.0, blur_sigma=1.0 | 6.0 | [5, 7] | fail | 0.72 | The montage shows nuclei with broadly distributed Pol2 signal and only a handful of colored overlay… |
| 20260612T061052Z | 2 | Pol2 | mode=mean_fold, threshold=1.45, min_size=5, max_size=2000, marker_h=2.0, blur_sigma=1.0 | 75.0 | [48, 102] | fail | 0.88 | The median per-cell count of 75 (IQR 48–102) is ~7–10× higher than the expected ~10 discrete Pol2 f… |
| 20260612T061052Z | 3 | Pol2 | mode=mean_fold, threshold=1.85, min_size=15, max_size=2000, marker_h=2.0, blur_sigma=1.0 | 1.5 | [0, 2] | fail | 0.82 | The per-cell foci counts are extremely low (median 1.5, IQR 0.25–2.0) relative to the expected ~10 … |
| 20260612T061052Z | 4 | Pol2 | mode=mean_fold, threshold=1.45, min_size=8, max_size=2000, marker_h=2.0, blur_sigma=1.0 | 56.5 | [33, 83] | fail | 0.85 | The reported median of 56.5 foci/cell is ~5-6x above the expected ~10 discrete Pol2 transcription f… |
| 20260612T061052Z | 5 | Pol2 | mode=mean_fold, threshold=1.85, min_size=20, max_size=2000, marker_h=2.0, blur_sigma=1.0 | 0.5 | [0, 1] | fail | 0.85 | The montage shows nuclei with clearly visible bright Pol2 puncta distributed across the nucleoplasm… |
