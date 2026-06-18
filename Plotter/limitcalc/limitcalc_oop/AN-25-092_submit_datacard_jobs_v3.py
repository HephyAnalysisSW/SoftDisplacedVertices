#!/usr/bin/env python3
# Write job_ids.json for ABCD scan datacard creation and submit it.
# Run outside cmssw-el9. Jobs themselves enter cmssw-el9 via submit_limitcalc.sh.
#
# Example:
# python3 AN-25-092_submit_datacard_jobs_v3.py \
#   --uniquedir AN-25-092_ML_plots_limitcalc_merge_w_Ang_v3 \
#   --x-scan 350 700 50 --y-scan 0.990 1.0 0.0002

import argparse

from jobs import ABCDScan, CmsswJobCommand, DEFAULT_UNIQUEDIR, JobIds


def build_jobs(args):
    # One job per scan point. Each job creates all signal-sample datacards for
    # that threshold pair.
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

    for xcut, ycut in scan.points():
        name = scan.scan_name(xcut, ycut)
        datacard_dir = scan.datacard_dir(xcut, ycut, args.mode)
        jobs[name] = {
            "command": commands.datacard_job(
                uniquedir=scan.uniquedir,
                output_dir=datacard_dir,
                xcut=xcut,
                xlo=args.xlo,
                ycut=ycut,
                ylo=args.ylo,
                mode=args.mode,
                use_data=args.data,
            ),
            "jobid": None,
            "status": "prepared",
            "xcut": xcut,
            "ycut": ycut,
            "datacard_dir": str(datacard_dir),
        }

    return scan.base / "datacard_jobs" / "job_ids.json", jobs


def main():
    parser = argparse.ArgumentParser(description="Write job_ids.json and submit ABCD scan datacard jobs.")
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
    parser.add_argument("--xlo", type=float, default=250.0, help="Lower MET threshold.")
    parser.add_argument("--ylo", type=float, default=0.80, help="Lower ML score threshold.")
    parser.add_argument("--mode", choices=["Asimov", "observation"], default="Asimov", help="Datacard mode.")
    parser.add_argument("--data", action="store_true", help="Use data histograms as observation source.")
    args = parser.parse_args()

    job_path, jobs = build_jobs(args)
    job_ids = JobIds(job_path)

    job_ids.write(jobs)
    job_ids.submit_jobs_in_json()


if __name__ == "__main__":
    main()
