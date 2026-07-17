# Prdm14 lineage-specific enhancer insertions (Development 2025)

**Journal:** Development 152(24):dev204886 (2025)
**ID:** DOI 10.1242/dev.204886
**URL:** https://journals.biologists.com/dev/article/152/24/dev204886/370114/

| Field | Value |
|---|---|
| Cell type | **mESC, 2i/LIF (naïve)** |
| Method | luciferase reporter in mESCs (Fig. 1G) + CRISPR/Cas9 biallelic deletion |
| Evidence type | **FUNCTIONAL (deletion + reporter)** |
| Genome build | mm10 (coords derived from Supp. Fig. S1 gRNA seqs → UCSC; also mm39) |
| E–P distance | mEn1 ~42 kb, cEn1 ~52 kb, mEn2 ~32 kb downstream of Prdm14 TSS |
| eRNA evidence | not reported |
| Confidence | **high** (mEn1 / cEn1 / mEn2) |

## Validated elements / pairs
Thesis: rodent-specific **enhancer insertions** downstream of **Prdm14** (mm10 chr1:13,113,427–13,127,163, **− strand**; TSS **chr1:13,127,163**) drive the rapid naïve→formative pluripotency transition in rodents. The paper classifies a cluster of downstream enhancers by conservation and tests them in 2i/LIF mESCs (luciferase, Fig. 1G) with CRISPR deletion:

- **mEn1** — Muridae-specific Enhancer 1. **mm10 chr1:13,084,522–13,085,902** (~1.4 kb), ~42 kb downstream of TSS. OCT4/SOX2 motif (mouse, absent in rat). **Best-defined for mESC 2i/LIF.**
- **cEn1** — conserved Enhancer 1. mm10 chr1:13,074,159–13,075,407, ~52 kb downstream. Conserved OCT4/SOX2 motif across amniotes.
- **mEn2** — Muridae-specific Enhancer 2. mm10 chr1:13,094,606–13,095,049, ~32 kb downstream. ERV-derived; OCT4/SOX2 + TFCP2L1 motifs.
- **mEn3** — Muroidea-specific. Not precisely mapped (no gRNA in accessible supp); ~15–25 kb downstream, between mEn2 and the gene 3′ end. PRDM14-binding / autorepression site.
- **cEn2** — conserved Enhancer 2. Mouse coords not extractable from accessible materials.

Coordinates are the CRISPR **deletion** intervals (edge-to-edge of the two gRNA cut sites) mapped to UCSC by exact sequence match; the authors do not print a coordinate table. mEn3/cEn2 gRNAs would be in Table S1 (not parsed).

## Relevance to EP-ORCA panel
**Upgrades the evidence for `E_Prdm14`; no coordinate change.** Our current `E_Prdm14` = chr1:13,082,457–13,097,137 (Hansen-supp interval, 14.7 kb) **already contains both mEn1 (13,084,522–13,085,902) and mEn2 (13,094,606–13,095,049)** — confirmed by eye. This paper promotes Prdm14's evidence from "Hansen supp" to **functional mESC 2i/LIF (luciferase + CRISPR deletion)**, and documents the finer enhancer structure should we ever want to sub-resolve mEn1 vs mEn2 (à la the staged Klf4 scheme).

**Notes:** coords are gRNA-to-gRNA deletion spans (±tens of bp vs the luciferase fragment / peak core). mm10→mm39 offset ≈ +70,224 bp in this region.

**Related:** [[hansen-2025-adt4221]] · [[panel-status]]
