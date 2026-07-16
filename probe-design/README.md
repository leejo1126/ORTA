# probe-design module

**Status:** active
**One-liner:** E–P ORCA probe / panel design — which enhancer–promoter pairs are imaged (RNA + DNA
readouts), their mm10 coordinates, readout/plate assignment, and dual-barcode scheme.

Design decisions are grounded in the literature wiki ([[panel-status]] + the `wiki/literature/` source
pages). This module's **experiments are panel versions** (`experiments/probe-design_v3/`, …); a new
version is a new experiment folder, not an overwrite.

## Layout
```
probe-design/
  README.md
  experiments/
    probe-design_v3/     current panel — coordinates, readout scheme, dual-barcode, .bed, MATLAB, MANIFEST
```

## Provenance
- Coordinates are **mm10 (GRCm38)**; every pair is labelled by evidence type and only FUNCTIONALLY
  validated pairs qualify as "validated" (see `wiki/schema.md`).
- The design rationale, adds/drops, and coordinate liftovers are recorded in
  `[[panel-status]]` and `lab-notebook/probe-design.md`.

## Related
- Wiki: [[panel-status]], `wiki/literature/`
- The DNA readouts this panel defines are imaged by the planned `DNA/` module.
