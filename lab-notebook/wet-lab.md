# Wet-lab notebook

Bench work: procedures performed, protocol changes/deviations, reagents & lots, cell lines/conditions,
imaging sessions. Each entry ideally links to the resulting raw dataset + the experiment ID that will
consume it, and to the versioned protocol in `[[wiki/protocols]]`. Template: `../_templates/notebook-entry.md`.

> Tell Claude the day's bench work and it will file it here + summarize in `main.md` + version any changed
> protocol page. The fields below are placeholders where the record wasn't captured digitally — fill them in.

---

## 2026-04-16 — IF staining + imaging, drug-perturbation panel
- **What:** Immunofluorescence staining and 3D imaging of the E–P drug-perturbation panel.
- **Samples / conditions:** mESC (line: _TBD_); 8 drug conditions across 198 FOVs (see
  `IF/config/conditions.yaml` for FOV↔condition ranges).
- **Markers / channels:** Brd4 (647), Sc35 (488), DAPI (405), Pol2 (561, imaged post-bleach to avoid
  647/Brd4 bleed-through). Fiducial beads for registration.
- **Protocol:** `[[if-staining]]` v_TBD — _fixation, permeabilization, antibodies + lots, dilutions,
  mounting, microscope/objective, exposure/z-step to be filled_.
- **Changes / deviations:** _none recorded_.
- **Result / raw data:** `.dax` at `Z:/EPORCA/2026-04-16_IF` → experiment `IF_2026-04-16_v1`.
- **Links:** [main](main.md) · [if-analysis](if-analysis.md).

<!-- New bench day → copy the template block; if a protocol changed, bump the wiki/protocols page version. -->
