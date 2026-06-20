#!/bin/bash
# Stage raw .dax from the lab NAS to Sherlock storage (Oak). Run this from a machine that
# can see the NAS (your workstation) -- Sherlock compute/login nodes CANNOT mount the NAS,
# so the data must be copied first. Oak is persistent + lab-owned; $SCRATCH is faster but
# purged (~90 days).
#
# For very large/long transfers prefer Globus (NAS endpoint <-> "Stanford Sherlock"
# endpoint): https://www.sherlock.stanford.edu/docs/storage/data-transfer/#globus
set -euo pipefail

# ---------------- EDIT THESE ----------------
SUNET="your_sunetid"
NAS_SRC="/Volumes/boettiger_nas/EPORCA/2026-04-16_IF/"             # NAS path (mounted locally)
OAK_DST="${SUNET}@dtn.sherlock.stanford.edu:/oak/stanford/groups/aboettig/EPORCA/2026-04-16_IF/"
# --------------------------------------------

# Only the files the pipeline reads: interleaved zscan_647_561_488_405_*.dax + the
# separate Pol2 acquisition zscan_561_*.dax, plus their .inf headers. Add calibration/
# beads_* + 405_only_* only if you'll run chromatic correction.
rsync -avh --progress --partial \
  --include="zscan_647_561_488_405_*.dax" --include="zscan_647_561_488_405_*.inf" \
  --include="zscan_561_*.dax"             --include="zscan_561_*.inf" \
  --exclude="*" \
  "$NAS_SRC" "$OAK_DST"

echo "staged to $OAK_DST  -> set DAX_DIR in run_pipeline.sbatch to the Oak path"
