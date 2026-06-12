# Autofoci search — DAPI

Agnostic multi-algorithm search (no target count). Score is the proxy (contrast/SNR + reproducibility + fill/size sanity), higher = more foci-like.


## Round 1  (kept: wavelet, log_dog, mad_tophat)

| family | score | valid | med_count | cv | fill | contrast | judge | conf |
|--------|-------|-------|-----------|----|------|----------|-------|------|
| mean_fold | 0.801 | True | 11 | 0.459 | 0.0044 | 5.08 | no | 0.72 |
| otsu_adaptive | 0.800 | True | 1 | 0.632 | 0.002 | 5.69 | no | 0.75 |
| wavelet | 0.794 | True | 17 | 0.119 | 0.0168 | 3.57 | ok | 0.82 |
| h_dome | 0.781 | True | 302 | 0.2 | 0.2108 | 3.67 | no | 0.75 |
| log_dog | 0.773 | True | 14 | 0.239 | 0.0275 | 3.65 | ok | 0.78 |
| mad_tophat | 0.688 | True | 54 | 0.456 | 0.0238 | 2.85 | ok | 0.62 |

## Round 2  (kept: log_dog, wavelet, mad_tophat)

| family | score | valid | med_count | cv | fill | contrast | judge | conf |
|--------|-------|-------|-----------|----|------|----------|-------|------|
| log_dog | 0.785 | True | 12 | 0.188 | 0.0237 | 3.7 | ok | 0.72 |
| wavelet | 0.781 | True | 6 | 0.344 | 0.0066 | 4.19 | ok | 0.72 |
| mad_tophat | 0.719 | True | 57 | 0.289 | 0.0405 | 2.91 | ok | 0.78 |

## Round 3  (kept: wavelet, log_dog)

| family | score | valid | med_count | cv | fill | contrast | judge | conf |
|--------|-------|-------|-----------|----|------|----------|-------|------|
| wavelet | 0.821 | True | 9 | 0.144 | 0.0073 | 4.2 | ok | 0.75 |
| log_dog | 0.786 | True | 12 | 0.166 | 0.0281 | 3.62 | ok | 0.72 |
| mad_tophat | 0.707 | True | 26 | 0.358 | 0.034 | 2.92 | ok | 0.78 |

## Round 4  (kept: wavelet)

| family | score | valid | med_count | cv | fill | contrast | judge | conf |
|--------|-------|-------|-----------|----|------|----------|-------|------|
| wavelet | 0.820 | True | 25 | 0.104 | 0.0094 | 3.98 | ok | 0.82 |
| log_dog | 0.761 | True | 15 | 0.288 | 0.0291 | 3.6 | ok | 0.78 |

## Finalist(s): wavelet

