# Autofoci search — Pol2

Agnostic multi-algorithm search (no target count). Score is the proxy (contrast/SNR + reproducibility + fill/size sanity), higher = more foci-like.


## Round 1  (kept: h_dome, wavelet, log_dog)

| family | score | valid | med_count | cv | fill | contrast | judge | conf |
|--------|-------|-------|-----------|----|------|----------|-------|------|
| h_dome | 0.824 | True | 314 | 0.083 | 0.5618 | 4.73 | no | 0.88 |
| log_dog | 0.814 | True | 80 | 0.083 | 0.5726 | 4.53 | no | 0.85 |
| mad_tophat | 0.765 | True | 223 | 0.089 | 0.5226 | 3.5 | no | 0.85 |
| otsu_adaptive | 0.735 | True | 2051 | 0.202 | 0.3837 | 3.19 | no | 0.90 |
| wavelet | 0.697 | True | 15 | 0.144 | 0.0028 | 2.18 | ok | 0.72 |
| mean_fold | 0.687 | True | 35 | 0.197 | 0.0957 | 2.21 | no | 0.72 |

## Round 2  (kept: wavelet)

| family | score | valid | med_count | cv | fill | contrast | judge | conf |
|--------|-------|-------|-----------|----|------|----------|-------|------|
| h_dome | 0.832 | True | 281 | 0.082 | 0.5591 | 4.91 | no | 0.85 |
| log_dog | 0.808 | True | 87 | 0.103 | 0.577 | 4.52 | no | 0.85 |
| wavelet | 0.697 | True | 10 | 0.141 | 0.0027 | 2.17 | ok | 0.82 |

## Finalist(s): wavelet

