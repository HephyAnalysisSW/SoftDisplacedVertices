#!/usr/bin/env python3

import argparse
from pathlib import Path

from jobs import CmsswJobCommand, DEFAULT_BASEDIR, JobIds, workdir_from_uniquedir


def build_jobs(args):
    workdir = workdir_from_uniquedir(args.uniquedir)
    datacard_dir = workdir / "datacards" / args.datacard_dir_name / args.mode
    limit_dir = workdir / "limits" / args.limit_dir_name / args.mode
    job_path = args.job_ids or limit_dir / "job_ids.json"

    commands = CmsswJobCommand()
    jobs = {}
    for datacard in sorted(datacard_dir.glob("*.txt")):
        jobs[datacard.stem] = {
            "command": commands.limit_job(datacard, limit_dir),
            "jobid": None,
            "status": "prepared",
            "datacard": str(datacard),
            "limit_dir": str(limit_dir),
        }

    return job_path, jobs, datacard_dir, limit_dir


def parse_args():
    parser = argparse.ArgumentParser(description="Write job_ids.json and submit limit jobs.")
    parser.add_argument(
        "--uniquedir",
        required=True,
        help=(
            f"Directory name below {DEFAULT_BASEDIR}. "
            "Absolute paths are also accepted."
        ),
    )
    parser.add_argument("--mode", choices=["Asimov", "observation"], default="Asimov")
    parser.add_argument("--datacard-dir-name", default="reweighted_v2")
    parser.add_argument("--limit-dir-name", default="reweighted_v2")
    parser.add_argument("--job-ids", type=Path)
    parser.add_argument("--reuse", action="store_true")
    parser.add_argument("--prepare-only", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    job_path, jobs, datacard_dir, limit_dir = build_jobs(args)
    job_ids = JobIds(job_path)

    if not args.reuse:
        job_ids.write(jobs)
        print(f"datacard-dir: {datacard_dir}")
        print(f"limit-dir: {limit_dir}")

    if not args.prepare_only:
        job_ids.submit_jobs_in_json()


if __name__ == "__main__":
    main()
