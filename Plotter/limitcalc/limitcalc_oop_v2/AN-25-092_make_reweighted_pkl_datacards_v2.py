#!/usr/bin/env python3

import argparse
from pathlib import Path

from datacards import (
    DEFAULT_BASEDIR,
    DEFAULT_C1N2_CTAUS,
    DEFAULT_STOP_BRS,
    DEFAULT_YEARS,
    DatacardMaker,
    load_samples,
    workdir_from_uniquedir,
)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--uniquedir",
        required=True,
        help=(
            f"Directory name below {DEFAULT_BASEDIR}. "
            "Absolute paths are also accepted."
        ),
    )
    parser.add_argument("--xcut", type=float, default=500.0)
    parser.add_argument("--xlo", type=float, default=250.0)
    parser.add_argument("--ycut", type=float, default=0.999)
    parser.add_argument("--ylo", type=float, default=0.80)
    parser.add_argument("--mode", choices=["Asimov", "observation"], default="Asimov")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--datacard-dir-name", default="reweighted_v3")
    parser.add_argument("--dryrun", action="store_true")
    parser.add_argument("--stop-br", nargs="+", type=float, default=DEFAULT_STOP_BRS)
    parser.add_argument("--c1n2-ctau", nargs="+", type=float, default=DEFAULT_C1N2_CTAUS)
    return parser.parse_args()


def main():
    args = parse_args()
    workdir = workdir_from_uniquedir(args.uniquedir)
    output_dir = args.output_dir or workdir / "datacards" / args.datacard_dir_name / args.mode

    signals, data = load_samples(workdir, DEFAULT_YEARS)
    maker = DatacardMaker(
        signals,
        data,
        output_dir,
        args.xcut,
        args.xlo,
        args.ycut,
        args.ylo,
        args.mode,
        args.stop_br,
        args.c1n2_ctau,
    )
    if args.dryrun:
        maker.dryrun()
    else:
        maker.write()

    print(f"WORKDIR: {workdir}")
    print(f"Signals: {len(signals)}")
    print(f"Data years: {', '.join(data.values)}")


if __name__ == "__main__":
    main()
