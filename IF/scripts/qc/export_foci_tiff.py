"""
Export a FOV's foci/condensate calls as an ImageJ/Fiji hyperstack TIFF, so you can
inspect calling in 3D without touching OME-Zarr. Writes one TIFF per marker with
channels = [raw (bg-subtracted), foci labels, (optional) nuclei], calibrated in
microns (xy from pixel_size_um, z spacing from z_um) so the z:xy aspect is correct.

Two label sources:
  - default: the SAVED per-channel label volume from `eporca foci` (production config).
  - --spec PATH: apply an autofoci *proposed spec* (from a search's proposed_spec_*.json)
    over every nucleus in the FOV, so you can eyeball what the agnostic search's winner
    actually produces. (Reads the marker from the spec file.)

    python IF/scripts/qc/export_foci_tiff.py --config IF/config/config.yaml --fov 0 --marker Sc35
    python IF/scripts/qc/export_foci_tiff.py --config IF/config/config.yaml --with-nuclei \
        --spec agents/runs/autofoci/<ts>_Sc35/proposed_spec_Sc35.json

In Fiji:
  - File > Open the .tif (opens as a composite hyperstack: C channels x Z slices).
  - For the labels channel, Image > Lookup Tables > glasbey (or "3-3-2 RGB") to see
    each focus in its own color; the raw channel keeps a Grays LUT.
  - 3D view: Image > Stacks > 3D Project (quick), or Plugins > 3D Viewer. Calibration
    is read from the TIFF, so proportions are right.
"""

from __future__ import annotations

import json
import argparse
from pathlib import Path

import numpy as np
import scipy.ndimage as ndi
import zarr
import tifffile

from eporca.config import Config
from eporca.io_zarr import read_channel
from eporca.foci import load_nuclear_labels_3d, subtract_background, _expand_slices


def _labels_from_spec(cfg, fov, marker, raw_float, spec) -> np.ndarray:
    """Apply an autofoci spec to every nucleus in the FOV; assemble a full label
    volume with globally-unique ids (same per-nucleus crop + renumber as eporca.foci)."""
    from eporca.autofoci.spec import detect_core
    nuc = load_nuclear_labels_3d(cfg, fov, raw_float.shape)
    slices = ndi.find_objects(nuc)
    full = np.zeros(raw_float.shape, np.uint32)
    base = 0
    for L in [i + 1 for i, s in enumerate(slices) if s is not None]:
        sl = _expand_slices(slices[L - 1], raw_float.shape, (1, 8, 8))
        subnuc = nuc[sl] == L
        if not subnuc.any():
            continue
        lab = detect_core(spec, np.ascontiguousarray(raw_float[sl]), subnuc)
        m = lab > 0
        if m.any():
            full[sl][m] = lab[m].astype(np.uint32) + base
            base += int(lab.max())
    return full


def _to_uint16(lab: np.ndarray):
    """ImageJ composite channels share a dtype (uint16). Dense markers can exceed the
    uint16 ceiling -> remap nonzero ids into [1, 65535] so none overflow to 0 (vanish).
    Returns (uint16 labels, true n_foci, remapped?)."""
    n = int(lab.max())
    if n > 65535:
        nz = lab > 0
        disp = np.zeros(lab.shape, dtype=np.uint16)
        disp[nz] = ((lab[nz].astype(np.uint64) - 1) % 65535 + 1).astype(np.uint16)
        return disp, n, True
    return lab.astype(np.uint16), n, False


def _randomize(lab: np.ndarray):
    """Display-only: shuffle label ids so spatially-adjacent foci (which get consecutive
    ids from the per-nucleus numbering) no longer map to adjacent glasbey colors. Each
    focus gets a distinct value spread across 1..65535 in random order, so neighbours get
    well-separated colours. Returns (uint16 labels, true n_foci). NOTE: shuffled ids no
    longer join the per_spot CSV. Deterministic (seeded)."""
    present = np.unique(lab)
    present = present[present > 0]
    n = int(present.size)
    out = np.zeros(lab.shape, dtype=np.uint16)
    if n:
        order = np.random.default_rng(0).permutation(n)
        spread = (order.astype(np.uint64) * 65534 // max(1, n - 1) + 1).astype(np.uint16)
        lut = np.zeros(int(lab.max()) + 1, dtype=np.uint16)
        lut[present] = spread
        out = lut[lab]
    return out, n


def _export(cfg, fov, marker, lab, with_nuclei, out_dir, tag, randomize=True) -> None:
    px, zum = cfg.acquisition.pixel_size_um, cfg.acquisition.z_um
    raw = np.clip(subtract_background(
        read_channel(cfg, fov, marker, trim=True).astype(np.float32), cfg.foci.background),
        0, 65535).astype(np.uint16)
    if randomize:
        lab16, n_foci = _randomize(lab)
        note = "  [labels shuffled for display (glasbey-friendly); not CSV-joinable]"
    else:
        lab16, n_foci, remapped = _to_uint16(lab)
        note = "  [labels remapped: ids cycle 1..65535]" if remapped else ""
    chans, names = [raw, lab16], ["raw", "foci_labels"]
    if with_nuclei:
        chans.append(load_nuclear_labels_3d(cfg, fov, raw.shape).astype(np.uint16))
        names.append("nuclei")
    stack = np.stack(chans, axis=1)                                   # (Z, C, Y, X)
    out = out_dir / f"{tag}_fiji_fov{fov:03d}_{marker}.tif"
    tifffile.imwrite(str(out), stack, imagej=True, resolution=(1.0 / px, 1.0 / px),
                     metadata={"spacing": zum, "unit": "um", "axes": "ZCYX", "Labels": names})
    print(f"wrote {out}  (Z,C,Y,X)={stack.shape}  channels={names}  foci={n_foci}" + note)


def main() -> None:
    ap = argparse.ArgumentParser(description="Export foci calls as a Fiji hyperstack TIFF")
    ap.add_argument("--config", default="IF/config/config.yaml")
    ap.add_argument("--fov", type=int, default=0)
    ap.add_argument("--marker", default="Sc35", help="comma-separated markers (saved-label mode)")
    ap.add_argument("--spec", default=None,
                    help="apply an autofoci proposed_spec_*.json over the FOV instead of "
                         "reading the saved labels (marker taken from the spec file)")
    ap.add_argument("--out", default=None, help="output dir (default: <data>/figures)")
    ap.add_argument("--with-nuclei", action="store_true", help="add a nucleus-mask channel")
    ap.add_argument("--keep-ids", action="store_true",
                    help="keep true label ids (CSV-joinable) instead of shuffling them for "
                         "glasbey display (default: shuffle, since this is a QC viewer)")
    args = ap.parse_args()

    cfg = Config.load(args.config)
    out_dir = Path(args.out) if args.out else cfg.figures_dir()
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.spec:
        from eporca.autofoci.spec import Spec
        meta = json.loads(Path(args.spec).read_text())
        marker = meta["marker"]
        spec = Spec(**meta["spec"])
        raw_float = subtract_background(
            read_channel(cfg, args.fov, marker, trim=True).astype(np.float32), cfg.foci.background)
        lab = _labels_from_spec(cfg, args.fov, marker, raw_float, spec)
        print(f"[autofoci spec] {marker}: family={spec.family} -> {int(lab.max())} foci in FOV {args.fov}")
        _export(cfg, args.fov, marker, lab, args.with_nuclei, out_dir, tag="autofoci",
                randomize=not args.keep_ids)
        return

    for marker in [m.strip() for m in args.marker.split(",") if m.strip()]:
        path = cfg.foci_label_path(args.fov, marker)
        try:
            lab = np.asarray(zarr.open_group(path, mode="r")["0"])
        except Exception as e:                                        # noqa: BLE001
            raise SystemExit(f"No saved foci labels for {marker} at {path}; run "
                             f"`eporca foci --config {args.config} --fov {args.fov}` first. [{e}]")
        _export(cfg, args.fov, marker, lab, args.with_nuclei, out_dir, tag="foci",
                randomize=not args.keep_ids)


if __name__ == "__main__":
    main()
