#!/usr/bin/env python3
"""
Prepare ABCD scan datacard and limit jobs.

1. python3 AN-25-092_run_ABCDscan.py --prepare datacards
2. python3 AN-25-092_run_ABCDscan.py --prepare limits


"""

import argparse
import getpass
import itertools
import json
import shlex
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
DATACARD_SCRIPT = SCRIPT_DIR / "AN-25-092_make_multiplane_datacards_v2.py"
MAKE_LIMITS_SCRIPT = SCRIPT_DIR / "makeLimits.py"
SBATCH_SCRIPT = SCRIPT_DIR / "submit_limitcalc.sh"

DEFAULT_SCRATCH_BASE = Path(f"/scratch-cbe/users/{getpass.getuser()}/AN_plots/ParT_hists")
DEFAULT_UNIQUEDIR = DEFAULT_SCRATCH_BASE / "AN-25-092_ML_plots_limitcalc_merge_w_Ang_v3"

SCAN_X_MIN  = 350.0
SCAN_X_MAX  = 700.0
SCAN_X_STEP = 50.0
SCAN_Y_MIN  = 0.990
SCAN_Y_MAX  = 1.0
SCAN_Y_STEP = 0.0002


def threshold_token(value):
    text = f"{value:g}"
    return text.replace("-", "m").replace(".", "p")


def scan_name(met_cut, ml_cut):
    return f"MET{threshold_token(met_cut)}_ML{threshold_token(ml_cut)}"


def resolve_uniquedir(value):
    path = Path(value).expanduser()
    if path.is_absolute():
        return path
    return DEFAULT_SCRATCH_BASE / path


def scan_values(scan_min, scan_max, scan_step):
    values = []
    value = scan_min
    stop = scan_max + 0.5 * scan_step
    while value <= stop:
        values.append(round(value, 8))
        value += scan_step
    return values


def shell_join(parts):
    return " ".join(shlex.quote(str(part)) for part in parts)


def datacard_inner_command(args, uniquedir, met_cut, ml_cut, datacard_dir):
    command = [
        "python3",
        "-u",
        str(DATACARD_SCRIPT),
        "--histdir",
        str(uniquedir),
        "--output-dir",
        str(datacard_dir),
        "--xcut",
        str(met_cut),
        "--xlo",
        str(args.xlo),
        "--ycut",
        str(ml_cut),
        "--ylo",
        str(args.ylo),
        "--mode",
        args.mode,
    ]
    if args.data:
        command.append("--data")
    return shell_join(command)


def limit_inner_command(datacard, limit_dir):
    return shell_join([
        "python3",
        "-u",
        str(MAKE_LIMITS_SCRIPT),
        "--datacard",
        str(datacard),
        "--limitdir",
        str(limit_dir),
    ])


def sbatch_command(inner_command):
    return shell_join(["sbatch", str(SBATCH_SCRIPT), inner_command])


def job_info(command):
    return {
        "command": command,
        "jobid": None,
        "status": "prepared",
    }


def write_job_ids(path, job_dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(job_dict, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(job_dict)} jobs to {path}")


def prepare_datacard_jobs(args, uniquedir, scan_base, met_cuts, ml_cuts):
    job_dict = {}
    for met_cut, ml_cut in itertools.product(met_cuts, ml_cuts):
        this_scan_name = scan_name(met_cut, ml_cut)
        datacard_dir = scan_base / this_scan_name / "datacards" / args.mode
        inner_command = datacard_inner_command(args, uniquedir, met_cut, ml_cut, datacard_dir)
        job_dict[this_scan_name] = {
            **job_info(sbatch_command(inner_command)),
            "met_cut": met_cut,
            "ml_cut": ml_cut,
            "datacard_dir": str(datacard_dir),
        }

    write_job_ids(scan_base / "datacard_jobs" / "job_ids.json", job_dict)


def prepare_limit_jobs(args, scan_base, met_cuts, ml_cuts):
    job_dict = {}
    missing = []
    for met_cut, ml_cut in itertools.product(met_cuts, ml_cuts):
        this_scan_name = scan_name(met_cut, ml_cut)
        scan_dir = scan_base / this_scan_name
        datacard_dir = scan_dir / "datacards" / args.mode
        limit_dir = scan_dir / "limits" / args.mode
        datacards = sorted(datacard_dir.glob("*.txt"))
        if not datacards:
            missing.append(str(datacard_dir))
            continue

        for datacard in datacards:
            key = f"{this_scan_name}__{datacard.stem}"
            inner_command = limit_inner_command(datacard, limit_dir)
            job_dict[key] = {
                **job_info(sbatch_command(inner_command)),
                "met_cut": met_cut,
                "ml_cut": ml_cut,
                "datacard": str(datacard),
                "limit_dir": str(limit_dir),
            }

    write_job_ids(scan_base / "limit_jobs" / "job_ids.json", job_dict)
    if missing:
        print(f"Skipped {len(missing)} scan points without datacards.")


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Prepare ABCD threshold scan jobs. Outputs are written below "
            "<uniquedir>/ABCDscan/."
        )
    )
    parser.add_argument(
        "--uniquedir",
        default=str(DEFAULT_UNIQUEDIR),
        help=(
            "Plotter unique directory, either as an absolute path or as a name below "
            f"{DEFAULT_SCRATCH_BASE}. Default: {DEFAULT_UNIQUEDIR}."
        ),
    )
    parser.add_argument(
        "--xlo",
        type=float,
        default=250.0,
        help="Lower MET threshold for regions B and D. Default: 250.",
    )
    parser.add_argument(
        "--ylo",
        type=float,
        default=0.80,
        help="Lower ML score threshold for regions C and D. Default: 0.80.",
    )
    parser.add_argument(
        "--mode",
        choices=["Asimov", "observation"],
        default="Asimov",
        help="Datacard mode. Default: Asimov.",
    )
    parser.add_argument(
        "--data",
        action="store_true",
        help="Use data histograms instead of MC background as the observation source.",
    )
    parser.add_argument(
        "--prepare",
        choices=["datacards", "limits", "all"],
        default="datacards",
        help="Which job_ids.json file to prepare. Default: datacards.",
    )
    args = parser.parse_args()

    uniquedir = resolve_uniquedir(args.uniquedir)
    scan_base = uniquedir / "ABCDscan"
    met_cuts = scan_values(SCAN_X_MIN, SCAN_X_MAX, SCAN_X_STEP)
    ml_cuts = scan_values(SCAN_Y_MIN, SCAN_Y_MAX, SCAN_Y_STEP)

    print(
        f"Preparing {len(met_cuts)} MET thresholds "
        f"({SCAN_X_MIN:g} to {SCAN_X_MAX:g}, step {SCAN_X_STEP:g}) and "
        f"{len(ml_cuts)} ML thresholds "
        f"({SCAN_Y_MIN:g} to {SCAN_Y_MAX:g}, step {SCAN_Y_STEP:g})."
    )

    if args.prepare in {"datacards", "all"}:
        prepare_datacard_jobs(args, uniquedir, scan_base, met_cuts, ml_cuts)
    if args.prepare in {"limits", "all"}:
        prepare_limit_jobs(args, scan_base, met_cuts, ml_cuts)


if __name__ == "__main__":
    main()
