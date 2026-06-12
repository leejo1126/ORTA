# Autofoci search — Sc35

Agnostic multi-algorithm search (no target count). Score is the proxy (contrast/SNR + reproducibility + fill/size sanity), higher = more foci-like.


## Round 1  (kept: mean_fold, mad_tophat, otsu_adaptive, log_dog, h_dome)

| family | score | valid | med_count | cv | fill | contrast | judge | conf |
|--------|-------|-------|-----------|----|------|----------|-------|------|
| mean_fold | 0.962 | True | 19 | 0.128 | 0.0028 | 13.7 | ok | 0.82 |
| wavelet | 0.916 | True | 4 | 0.178 | 0.0038 | 7.74 | no | 0.82 |
| otsu_adaptive | 0.907 | True | 11 | 0.163 | 0.0162 | 7.02 | ok | 0.82 |
| log_dog | 0.866 | True | 27 | 0.196 | 0.0369 | 5.67 | ok | 0.82 |
| h_dome | 0.866 | True | 39 | 0.195 | 0.0462 | 5.64 | ok | 0.82 |
| mad_tophat | 0.864 | True | 24 | 0.153 | 0.0266 | 5.3 | ok | 0.82 |

## Round 2  (kept: mean_fold, mad_tophat, h_dome)

| family | score | valid | med_count | cv | fill | contrast | judge | conf |
|--------|-------|-------|-----------|----|------|----------|-------|------|
| mean_fold | 0.958 | True | 13 | 0.147 | 0.002 | 14.2 | ok | 0.82 |
| otsu_adaptive | 0.941 | True | 11 | 0.194 | 0.0043 | 11.15 | no | 0.78 |
| log_dog | 0.884 | True | 15 | 0.163 | 0.0217 | 6.03 | ok | 0.72 |
| h_dome | 0.880 | True | 31 | 0.131 | 0.0436 | 5.65 | ok | 0.88 |
| mad_tophat | 0.859 | True | 50 | 0.092 | 0.0463 | 4.77 | ok | 0.85 |

## Round 3  (kept: mean_fold, h_dome)

| family | score | valid | med_count | cv | fill | contrast | judge | conf |
|--------|-------|-------|-----------|----|------|----------|-------|------|
| mean_fold | 0.955 | True | 14 | 0.136 | 0.004 | 11.45 | ok | 0.82 |
| h_dome | 0.880 | True | 31 | 0.11 | 0.0495 | 5.48 | ok | 0.88 |
| mad_tophat | 0.858 | True | 55 | 0.145 | 0.0427 | 5.1 | ok | 0.82 |

## Finalist(s): mean_fold

