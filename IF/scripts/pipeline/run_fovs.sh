#!/usr/bin/env bash
# Drive the full pipeline over a list of FOVs (serial), then build AnnData + analyze.
# Usage:  bash IF/scripts/pipeline/run_fovs.sh 0 1 2 3 4 65 66 67 68 69
ANALYSIS="S:/cluade code/EP-ORCA/.venv/Scripts/python.exe"
CELLPOSE="C:/ProgramData/Anaconda3/envs/cellpose-gpu/python.exe"
CFG="IF/config/config.yaml"
cd "S:/cluade code/ep-orca-if" || exit 1

for f in "$@"; do
  echo "=== FOV $f : to-zarr ===";  "$ANALYSIS" -m eporca.cli to-zarr  --config "$CFG" --fov "$f" || echo "zarr FAIL $f"
  echo "=== FOV $f : segment ===";  "$CELLPOSE" -m eporca.cli segment  --config "$CFG" --fov "$f" 2>&1 | tail -1 || echo "segment FAIL $f"
  echo "=== FOV $f : foci ===";     "$ANALYSIS" -m eporca.cli foci      --config "$CFG" --fov "$f" --workers 16 || echo "foci FAIL $f"
  echo "=== FOV $f : features ==="; "$ANALYSIS" -m eporca.cli features  --config "$CFG" --fov "$f" || echo "features FAIL $f"
done

echo "=== anndata ==="; "$ANALYSIS" -m eporca.cli anndata --config "$CFG"
echo "=== analyze ==="; "$ANALYSIS" -m eporca.cli analyze --config "$CFG"
echo "ALL DONE"
