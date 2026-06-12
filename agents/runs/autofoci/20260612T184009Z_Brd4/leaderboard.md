# Autofoci search — Brd4

Agnostic multi-algorithm search (no target count). Score is the proxy (contrast/SNR + reproducibility + fill/size sanity), higher = more foci-like.


## Round 1  (kept: h_dome, log_dog, mad_tophat, wavelet)

| family | score | valid | med_count | cv | fill | contrast | judge | conf |
|--------|-------|-------|-----------|----|------|----------|-------|------|
| mean_fold | 0.944 | True | 81 | 0.131 | 0.009 | 9.36 | no | 0.78 |
| otsu_adaptive | 0.904 | True | 7 | 0.285 | 0.0021 | 8.5 | no | 0.85 |
| h_dome | 0.902 | True | 324 | 0.089 | 0.2618 | 6.14 | ok | 0.72 |
| log_dog | 0.881 | True | 251 | 0.14 | 0.5511 | 7.21 | ok | 0.72 |
| wavelet | 0.878 | True | 154 | 0.15 | 0.029 | 5.73 | ok | 0.72 |
| mad_tophat | 0.873 | True | 272 | 0.07 | 0.531 | 6.02 | ok | 0.72 |

## Round 2  (kept: h_dome, log_dog, wavelet)

| family | score | valid | med_count | cv | fill | contrast | judge | conf |
|--------|-------|-------|-----------|----|------|----------|-------|------|
| h_dome | 0.902 | True | 324 | 0.089 | 0.2618 | 6.14 | ok | 0.72 |
| log_dog | 0.886 | True | 229 | 0.111 | 0.5759 | 7.21 | ok | 0.72 |
| wavelet | 0.882 | True | 332 | 0.132 | 0.0359 | 5.71 | ok | 0.72 |
| mad_tophat | 0.877 | True | 335 | 0.061 | 0.562 | 6.16 | ok | 0.78 |

## Round 3  (kept: h_dome, wavelet)

| family | score | valid | med_count | cv | fill | contrast | judge | conf |
|--------|-------|-------|-----------|----|------|----------|-------|------|
| h_dome | 0.886 | True | 467 | 0.078 | 0.5495 | 6.67 | ok | 0.72 |
| wavelet | 0.885 | True | 161 | 0.143 | 0.0254 | 5.9 | ok | 0.72 |
| log_dog | 0.883 | True | 23 | 0.137 | 0.0179 | 5.79 | no | 0.82 |

## Round 4  (kept: h_dome)

| family | score | valid | med_count | cv | fill | contrast | judge | conf |
|--------|-------|-------|-----------|----|------|----------|-------|------|
| h_dome | 0.902 | True | 54 | 0.146 | 0.0329 | 6.59 | ok | 0.72 |
| wavelet | 0.884 | True | 370 | 0.111 | 0.0463 | 5.61 | ok | 0.72 |

## Finalist(s): h_dome

