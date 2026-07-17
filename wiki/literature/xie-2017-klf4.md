# Xie, Zhang, et al. (2017)

**Journal:** Genes & Development 31(17):1795
**ID:** PMID 28982762 · GEO GSE97304
**URL:** https://genesdev.cshlp.org/content/31/17/1795.full.html

| Field | Value |
|---|---|
| Cell type | naive mESC (JM8.N4) |
| Method | CRISPR deletion (E1/E2/E3) + dCas9-CRISPRi + luciferase + 3C |
| Evidence type | **FUNCTIONAL (deletion + CRISPRi)** |
| Genome build | mm9/mm10 (coords in GEO supp.) |
| E–P distance | ~50–70 kb (E2 ≈ 56 kb) |
| eRNA evidence | not reported |
| Deep-research verification | 3-0 confirmed |
| Confidence | **high** |

## Validated elements / pairs
Klf4 three downstream DHS enhancers E1/E2/E3, ~50–70 kb downstream of Klf4 TSS (chr4, − strand). E1 del −70%, E2 −85%, ΔE123 −90%.
- **E2 (55 kb enh, −85%)** exact mm10 core = chr4:55,475,372–55,476,162 (Waite 2024, PMC11441684); Cheng window mm10 ≈ 55,475,303–55,478,803 (from mm9 55,488,180–55,491,680).
- **E1 (69 kb enh, −70%)** mm10 ≈ chr4:55,463,623–55,466,723 (lifted from Cheng mm9 55,476,500–55,479,600, offset −12,877; = the "69 kb" enhancer Cheng imaged alongside E2). Inference that Cheng's 69 kb element = Xie E1.
- E3 (3C-interaction hub, minimal effect alone) exact coords still in GSE97304 supp; not used.

## Relevance to EP-ORCA panel
**ADDED.** In `coordinates_v2` as **E_Klf4** = one contiguous ~22 kb window (chr4:55,460,173–55,482,053) covering both E1 (69 kb) and E2 (55 kb) 10 kb sub-windows. Main panel: E_Klf4 = RNA readout 6 (plate 1) / DNA 102 (plate 2). **Staged E1/E2 resolution** parked on plates 3–4 (E1_Klf4 sub RNA 193 / DNA 289; E2_Klf4 sub RNA 194 / DNA 290) via the fiducial-slot dual-barcode — no extra main-panel probes.

**Notes:** Klf4 TSS chr4:55,532,466 (−); downstream = lower coords. E1↔E2 centers ~11.9 kb apart (~8.6 kb spacer). See [[panel-status]] for plate layout.

**Related:** [[cheng-2023-klf4]] · [[panel-status]]

