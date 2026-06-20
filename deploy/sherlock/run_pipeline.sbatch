#!/bin/bash
# Full ORTA/eporca pipeline on the Boettiger lab's dedicated Sherlock node (sh-110-12:
# 24 CPU / 384 GB / no GPU). One self-contained Apptainer job; cellpose runs on CPU.
# Snakemake parallelizes across FOVs locally and is resumable -- re-submit to continue.
#
#   sbatch deploy/sherlock/run_pipeline.sbatch
#
#SBATCH -p aboettig
##SBATCH -w sh-110-12          # uncomment to pin the specific node
#SBATCH -J eporca
#SBATCH -c 24
#SBATCH --mem=360G
#SBATCH -t 48:00:00
#SBATCH -o logs/eporca_%j.out
#SBATCH -e logs/eporca_%j.err

set -euo pipefail

# ---------------- EDIT THESE ----------------
REPO="$GROUP_HOME/ORTA"                                              # repo root on Sherlock
IMG="$REPO/deploy/sherlock/eporca.sif"                              # built Apptainer image
DAX_DIR="/oak/stanford/groups/aboettig/EPORCA/2026-04-16_IF"        # staged raw .dax (stage_data.sh)
DATA_DIR="/oak/stanford/groups/aboettig/EPORCA/derived"            # outputs (Oak or $SCRATCH)
SEG_CONCURRENCY=2          # max concurrent cellpose-CPU segment jobs (mem/CPU limiter)
# --------------------------------------------

mkdir -p logs "$DATA_DIR"
CFG="$REPO/deploy/sherlock/config.sherlock.generated.yaml"
BIND="/oak,/scratch"       # make Sherlock storage visible inside the container

# 1) render the cluster config from config.yaml (paths + CPU segmentation; no param drift)
apptainer exec --bind "$BIND" "$IMG" \
  python "$REPO/deploy/sherlock/make_config.py" \
         "$REPO/IF/config/config.yaml" "$CFG" "$DAX_DIR" "$DATA_DIR"

# 2) run the pipeline. --resources gpu=N caps concurrent segment jobs (the Snakefile tags
#    segment with gpu=1); on CPU it's just a concurrency token to avoid thrashing.
apptainer exec --bind "$BIND" "$IMG" bash -lc "
  cd '$REPO' &&
  snakemake -s IF/workflow/Snakefile --configfile '$CFG' \
            -j ${SLURM_CPUS_PER_TASK:-24} --resources gpu=${SEG_CONCURRENCY} \
            --rerun-incomplete --keep-going --printshellcmds
"
echo 'pipeline job finished'
