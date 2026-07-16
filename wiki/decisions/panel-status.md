# EP-ORCA panel — evidence status of current pairs

Cross-reference of our existing panel against the functional-validation literature.

## Functionally validated (keep)
- **Moorthy 2017 (deletion-validated):** Sox2, Etl4, Cbfa2t2, Mcl1, Macf1, Med13l, mir290, Sall1, Tet1, Ranbp17, Esrrb → see [[moorthy-2017]]
- **Agrawal 2021 / Yeom 1996:** Nanog, Pou5f1 (pluripotency, well studied)

## Correlative only (candidates to reconsider/replace)
- **Novo 2018 (PCHi-C contacts, NOT deletion-validated):** Mtcl1/Ddx11/Ankrd12, Fn1, Tcfcp2l1, Smg7/Lamc1, Enah, Epha2, Ski, Klf3, Srrm4os, Zfp638, Cd9, Abhd17c, Trim71, Senp3/Sox15, Mycn, Lncenc1, Hes1, Rrp1b, Gabbr1/Zfp57, Ccnd3/Bysl, Csnk1a1, Neat1, Klf9 → see [[novo-2018]]

## Candidate NEW additions (functionally validated, not in panel)
| Rank | Gene | Source | Status |
|---|---|---|---|
| 1 | **Klf4** | [[xie-2017-klf4]] / [[cheng-2023-klf4]] | **ADDED to coordinates_v3** — E_Klf4 (=Xie E2, 10kb) + P_Klf4 (TSS 55,532,466 −). E1/E3 still available in GSE97304 supp if wanted. |
| 2 | **Car2** | [[hansen-2025-adt4221]] | **ADDED to coordinates_v3** — E1_Car2 (prox ~107kb) + E2_Car2 (dist ~168kb) + P_Car2 (TSS 14,886,428 +). |
| 3 | Lifr, Jarid2, Dppa5a/Ooep, Ifitm, Six | [[moorthy-2017]] | **DECLINED** — user reviewed paper; current Moorthy pairs are the ones worth pursuing. |
| 4 | Lrrc31 (CRE111) | [[weidiao-2020-focus]] | not pursued for now. |

## Panel changes made (2026-07-16)
- **+Klf4, +Car2** (5 features: E_Klf4, P_Klf4, E1_Car2, E2_Car2, P_Car2). Enhancer windows expanded to 10kb (<10kb rule).
- **Cd9 simplified** — dropped the E1/E2/E3 individual + shared-readout scheme (a [[novo-2018]] pair) to free DNA readouts; now one large **E_Cd9** (chr6:125,407,000–125,437,000, DNA-only). Net: 95 features, RNA 1–94, DNA 97–191 (both ≤96/plate).

## Upgrades to existing pairs (not yet applied)
- **Sox2:** could replace enhancer window with the validated SCR DHSs (~110 kb downstream) → [[sox2-scr-classics]] / [[eder-2025-sox2]]

## Cross-cutting caveats
- **eRNA gap:** none of the functional studies reported eRNA; RNA-arm suitability of new enhancers is unverified (check local mESC GRO-seq/CAGE).
- **Assembly hygiene:** confirm mm9 vs mm10 for every new coordinate before probe design.
