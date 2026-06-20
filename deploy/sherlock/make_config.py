"""Render a Sherlock run config from IF/config/config.yaml, overriding ONLY the
machine-specific keys (paths, interpreters, CPU segmentation). Keeps config.yaml the
single source of truth for detector params -- no drift.

    python make_config.py <src config.yaml> <dst.yaml> <dax_dir> <data_dir>
"""
import sys
import yaml

src, dst, dax_dir, data_dir = sys.argv[1:5]
c = yaml.safe_load(open(src))
c["paths"]["dax_dir"] = dax_dir
c["paths"]["data_dir"] = data_dir
c["interpreters"]["analysis"] = "/opt/envs/analysis/bin/python"
c["interpreters"]["cellpose"] = "/opt/envs/cellpose/bin/python"
c["segmentation"]["use_gpu"] = False     # GPU-less aboettig node -> cellpose on CPU
c["segmentation"]["use_bf16"] = False
yaml.safe_dump(c, open(dst, "w"), sort_keys=False)
print(f"wrote {dst}  (dax_dir={dax_dir}, data_dir={data_dir}, CPU cellpose)")
