---
name: lit-chromocenters
description: Chromocenters — DAPI-dense pericentromeric heterochromatin, cell-type-specific count (~7–18 in mouse), ~6× brighter than surroundings
type: reference
tags:
- DAPI
- heterochromatin
- chromocenter
- reference
sources:
- "Organisation of complex nuclear domains in somatic mouse cells, https://www.sciencedirect.com/science/article/abs/pii/S0248490099800318"
- "Pericentromeric heterochromatin organization / chromocenters (mouse somatic cells)"
---

Pericentromeric heterochromatin (clustered major-satellite repeats) condenses into
**chromocenters** — large DAPI-dense foci. Number is **cell-type specific**: ~18 per
nucleus in mouse 3T3 fibroblasts, ~7 in kidney/bone-marrow cells; differentiation tends
toward **fewer, larger** chromocenters relocating to the periphery. DAPI signal in
chromocenters is roughly **6× brighter** than surrounding nucleoplasm. Human/other cell
types differ.

**Implication for detection.** DAPI stains the whole nucleus, so chromocenters are the
**densest peaks (several-fold contrast over the nuclear bulk)**, not isolated spots — use
relative/local contrast, expect a few tens or fewer, and **do not hardcode a count** (it
varies by cell type). The cardinal failure is calling the whole nucleus as one body.
