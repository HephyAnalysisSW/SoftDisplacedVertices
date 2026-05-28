#!/usr/bin/env python3
# Write job_ids.json for ABCD scan limit calculations and submit it.
# Run outside cmssw-el9 after datacard jobs have finished.
# Jobs themselves enter cmssw-el9 via submit_limitcalc.sh.
#
# Example:
# python3 AN-25-092_submit_limit_jobs_v3.py \
#   --uniquedir AN-25-092_ML_plots_limitcalc_merge_w_Ang_v3 \
#   --x-scan 350 700 50 --y-scan 0.990 1.0 0.0002

import argparse

from jobs import ABCDScan, CmsswJobCommand, DEFAULT_UNIQUEDIR, JobIds


def build_jobs(args):
    # Limit jobs are only prepared after datacard files exist.
    scan = ABCDScan(
        uniquedir=args.uniquedir,
        x_min=args.x_scan[0],
        x_max=args.x_scan[1],
        x_step=args.x_scan[2],
        y_min=args.y_scan[0],
        y_max=args.y_scan[1],
        y_step=args.y_scan[2],
    )
    commands = CmsswJobCommand()
    jobs = {}
    missing = 0

    for xcut, ycut in scan.points():
        name = scan.scan_name(xcut, ycut)
        datacard_dir = scan.datacard_dir(xcut, ycut, args.mode)
        limit_dir = scan.limit_dir(xcut, ycut, args.mode)
        datacards = sorted(datacard_dir.glob("*.txt"))

        if not datacards:
            # This usually means the datacard jobs have not finished yet.
            missing += 1
            continue

        for datacard in datacards:
            key = f"{name}__{datacard.stem}"
            jobs[key] = {
                "command": commands.limit_job(datacard, limit_dir),
                "jobid": None,
                "status": "prepared",
                "xcut": xcut,
                "ycut": ycut,
                "datacard": str(datacard),
                "limit_dir": str(limit_dir),
            }

    return scan.base / "limit_jobs" / "job_ids.json", jobs, missing


def main():
    parser = argparse.ArgumentParser(description="Write job_ids.json and submit ABCD scan limit jobs.")
    parser.add_argument("--uniquedir", default=str(DEFAULT_UNIQUEDIR), help="Histogram unique directory.")
    parser.add_argument(
        "--x-scan",
        nargs=3,
        type=float,
        default=[350.0, 700.0, 50.0],
        metavar=("MIN", "MAX", "STEP"),
        help="MET scan as MIN MAX STEP. Default: 350 700 50.",
    )
    parser.add_argument(
        "--y-scan",
        nargs=3,
        type=float,
        default=[0.990, 1.0, 0.0002],
        metavar=("MIN", "MAX", "STEP"),
        help="ML score scan as MIN MAX STEP. Default: 0.990 1.0 0.0002.",
    )
    parser.add_argument("--mode", choices=["Asimov", "observation"], default="Asimov", help="Datacard mode.")
    parser.add_argument("--reuse", action="store_true", help="Submit an existing job_ids.json without rebuilding it.")
    args = parser.parse_args()

    job_path, jobs, missing = build_jobs(args)
    job_ids = JobIds(job_path)

    if not args.reuse:
        job_ids.write(jobs)
        if missing:
            print(f"Skipped {missing} scan points without datacards.")

    job_ids.submit_jobs_in_json()


if __name__ == "__main__":
    main()
