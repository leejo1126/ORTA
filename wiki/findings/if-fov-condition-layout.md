---
name: if-fov-condition-layout
description: IF FOV→condition layout — 198 total FOVs, 184 assigned, 2-frame gaps between 8 drug conditions
type: reference
tags: [IF, FOV, conditions, layout, acquisition, dataset]
sources: []
links: [if-data-map]
---

IF acquisition (experiment `IF_2026-04-16_v1`): `n_fovs: 198` (FOVs 000..197). `IF/config/conditions.yaml`
maps inclusive FOV ranges to 8 drug conditions; `assigned_fovs()` (`IF/src/eporca/config.py`) keeps only
FOVs inside a defined range — "gap"/boundary FOVs between blocks are excluded.

Gaps are **2 frames** between each pair of conditions: 42–43, 64–65, 86–87, 108–109, 130–131, 152–153,
174–175. 7 gaps × 2 = 14 excluded → **184 assigned FOVs** (matches feature files on disk).

Blocks: control 0–41 (42), auxin 44–63, jq1 66–85, sgc_cbp30 88–107, drb 110–129, triptolide 132–151,
eed226 154–173 (20 each), tsa 176–197 (22). control & tsa are larger than the uniform 20 — confirm
intended if it matters.

**Gotcha:** don't trust ad-hoc `grep -c` / `ls | wc` counts over the JudeData01 network share — they can
return partial listings (once miscounted 184 as 177, falsely implying 3-frame gaps). Enumerate
explicitly. See [[if-data-map]].
