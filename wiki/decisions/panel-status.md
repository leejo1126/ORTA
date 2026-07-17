# EP-ORCA panel — evidence status of current pairs

Cross-reference of our existing panel against the functional-validation literature.

## Functionally validated (keep)
- **Moorthy 2017 (deletion-validated):** Sox2, Etl4, Cbfa2t2, Mcl1, Macf1, Med13l, mir290, Sall1, Tet1, Ranbp17, Esrrb → see [[moorthy-2017]]
- **Agrawal 2021 / Yeom 1996:** Nanog, Pou5f1 (pluripotency, well studied)

## Correlative only (kept, for now)
- **Novo 2018 (PCHi-C contacts, NOT deletion-validated):** Mtcl1/Ddx11/Ankrd12, Fn1, Tcfcp2l1, Enah, Epha2, Klf3, Srrm4os, Zfp638, Cd9, Abhd17c, Trim71, Mycn, Lncenc1, Hes1, Rrp1b (now shares its enhancer with the new Sik1), Gabbr1/Zfp57, Ccnd3/Bysl, Csnk1a1, Neat1, Klf9 → see [[novo-2018]]

## Dropped — low / no FISH signal (2026-07-17)
Novo-2018 (correlative) pairs removed to make room for validated Hansen pairs; dropped for **low / no FISH signal**
(weak/absent imaging in prior data), per the panel guidelines (measurability > gene identity):
- **Myb**, **Srxn1**, **Ski** (also carried the +4 Mb coord error), **Senp3/Sox15** (source sheet: "sox15 and fxr2 didn't get fished").

## Candidate NEW additions (functionally validated, not in panel)
| Rank | Gene | Source | Status |
|---|---|---|---|
| 1 | **Klf4** | [[xie-2017-klf4]] / [[cheng-2023-klf4]] | **ADDED** — `E_Klf4` = 22 kb contiguous over E1 (69 kb, −70 %) + E2 (55 kb, −85 %), with staged E1/E2 sub-readouts on plates 3/4; + `P_Klf4` (TSS 55,532,466 −). E3 available in GSE97304 supp if wanted. |
| 2 | **Car2** | [[hansen-2025-adt4221]] | **ADDED** — E1_Car2 (prox ~107kb) + E2_Car2 (dist ~168kb) + P_Car2 (TSS 14,886,428 +). |
| 3 | **Inhbb, Ceacam1, Zbtb10, Prdm14, Sik1** | [[hansen-2025-adt4221]] (supp) | **ADDED 2026-07-17** — see below. |
| 4 | Lifr, Jarid2, Dppa5a/Ooep, Ifitm, Six | [[moorthy-2017]] | **DECLINED** — user reviewed paper; current Moorthy pairs are the ones worth pursuing. |
| 5 | Lrrc31 (CRE111) | [[weidiao-2020-focus]] | not pursued for now. |

## Panel changes made (2026-07-16)
- **+Klf4, +Car2** (5 features: E_Klf4, P_Klf4, E1_Car2, E2_Car2, P_Car2). Enhancer windows expanded to 10kb (<10kb rule).
- **Cd9 simplified** — dropped the E1/E2/E3 individual + shared-readout scheme to free DNA readouts; now one large **E_Cd9** (chr6:125,407,000–125,437,000). `E_Cd9` later given an eRNA probe for symmetry → 95 features, RNA 1–95 / DNA 97–191.

## Panel changes made (2026-07-17)
- **+5 Hansen supp pairs (+10 features):** **Inhbb** (P + distal E1 + E2), **Ceacam1** (P + E, − strand to avoid the + lncRNA), **Zbtb10** (P + E), **Prdm14** (P + E), **Sik1** (P only — shares `E_Rrp1b`). Enhancers <10 kb expanded to 10 kb; promoter DNA re-centered on mm10 TSS.
- **Sik1 coord fix:** given coords were Zbtb10's; corrected to chr17:31,855,792 (−) (consistent with sharing `E_Rrp1b`).
- **−4 Novo pairs (−9 features):** Myb, Senp3/Sox15, Srxn1, Ski — dropped for low/no FISH signal (see Dropped section).
- **Net: 96 features** — RNA 1–96 (plate 1), DNA 97–192 (plate 2), both plates exactly full; staged Klf4 subs on plates 3/4.

## Upgrades to existing pairs (not yet applied)
- **Sox2:** could replace enhancer window with the validated SCR DHSs (~110 kb downstream) → [[sox2-scr-classics]] / [[eder-2025-sox2]]

## Cross-cutting caveats
- **eRNA gap:** none of the functional studies reported eRNA; RNA-arm suitability of new enhancers is unverified (check local mESC GRO-seq/CAGE).
- **Assembly hygiene:** confirm mm9 vs mm10 for every new coordinate before probe design.
