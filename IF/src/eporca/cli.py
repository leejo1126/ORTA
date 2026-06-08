"""
Command-line entry points for each pipeline step (used directly and by the
Snakemake workflow). Heavy modules are imported lazily inside each handler so
that, e.g., the segment step doesn't pull in anndata and vice versa.

Usage:
    eporca to-zarr   --config config/config.yaml --fov 0
    eporca segment   --config config/config.yaml --fov 0      # cellpose-gpu python
    eporca foci      --config config/config.yaml --fov 0 [--save-labels]
    eporca features  --config config/config.yaml --fov 0
    eporca anndata   --config config/config.yaml [--no-embed]
    eporca analyze   --config config/config.yaml
"""

from __future__ import annotations

import argparse

from .config import Config


def _cfg(args) -> Config:
    cfg = Config.load(args.config)
    cfg.ensure_dirs()
    return cfg


def cmd_to_zarr(args):
    from .io_zarr import to_zarr
    print(to_zarr(_cfg(args), args.fov))


def cmd_segment(args):
    from .segment import segment_fov
    print(segment_fov(_cfg(args), args.fov))


def cmd_foci(args):
    from .foci import foci_fov
    markers = args.markers.split(",") if args.markers else None
    print(foci_fov(_cfg(args), args.fov, markers=markers,
                   save_labels=args.save_labels, workers=args.workers))


def cmd_features(args):
    from .features import features_fov
    print(features_fov(_cfg(args), args.fov))


def cmd_register(args):
    from .registration import register_fov
    print(register_fov(_cfg(args), args.fov))


def cmd_chromatic_calibrate(args):
    import json
    from .chromatic import calibrate
    print(json.dumps(calibrate(_cfg(args)), indent=2))


def cmd_anndata(args):
    from .anndata_build import build_all
    print(build_all(_cfg(args), embed=not args.no_embed))


def cmd_analyze(args):
    import anndata as ad
    from .analysis import differential, colocalization, correlation, biology
    cfg = _cfg(args)
    adata = ad.read_h5ad(cfg.anndata_path("nuclei"))
    differential.run(adata, cfg)
    colocalization.run(adata, cfg)
    correlation.run(adata, cfg)
    biology.run_all(adata, cfg)
    print(f"analysis figures written to {cfg.figures_dir()}")


def main(argv=None):
    p = argparse.ArgumentParser(prog="eporca", description="EP-ORCA IF pipeline")
    sub = p.add_subparsers(dest="cmd", required=True)

    def add_fov(sp):
        sp.add_argument("--config", required=True)
        sp.add_argument("--fov", type=int, required=True)
        return sp

    add_fov(sub.add_parser("to-zarr")).set_defaults(func=cmd_to_zarr)
    add_fov(sub.add_parser("segment")).set_defaults(func=cmd_segment)

    sp = sub.add_parser("foci"); add_fov(sp)
    sp.add_argument("--markers", default=None, help="comma-separated markers (default: all)")
    sp.add_argument("--save-labels", dest="save_labels", action="store_const",
                    const=True, default=None)
    sp.add_argument("--no-save-labels", dest="save_labels", action="store_const", const=False)
    sp.add_argument("--workers", type=int, default=None,
                    help="nucleus-level parallelism for testing (default: config foci.workers)")
    sp.set_defaults(func=cmd_foci)

    add_fov(sub.add_parser("features")).set_defaults(func=cmd_features)
    add_fov(sub.add_parser("register")).set_defaults(func=cmd_register)

    sp = sub.add_parser("chromatic-calibrate"); sp.add_argument("--config", required=True)
    sp.set_defaults(func=cmd_chromatic_calibrate)

    sp = sub.add_parser("anndata"); sp.add_argument("--config", required=True)
    sp.add_argument("--no-embed", action="store_true"); sp.set_defaults(func=cmd_anndata)

    sp = sub.add_parser("analyze"); sp.add_argument("--config", required=True)
    sp.set_defaults(func=cmd_analyze)

    args = p.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
