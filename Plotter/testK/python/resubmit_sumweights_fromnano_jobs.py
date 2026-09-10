#!/usr/bin/env python3

import json
import subprocess
from pathlib import Path


testk_dir = Path(__file__).resolve().parents[1]
output_dir = testk_dir / "sumWeights_fromnano"
jobs_path = output_dir / "job_ids.json"
submit_script = testk_dir / "sh/submit_to_cpu1.sh"

with jobs_path.open() as f:
    jobs = json.load(f)

result = subprocess.run(
    [
        "squeue",
        "--jobs",
        ",".join(job["jobid"] for job in jobs.values()),
        "--noheader",
        "--format=%A|%T",
    ],
    stdout=subprocess.PIPE,
    text=True,
    check=True,
)
active_jobs = dict(line.split("|", 1) for line in result.stdout.splitlines())

for sample, job in jobs.items():
    if Path(job["output"]).exists():
        continue

    old_job_id = job["jobid"]
    if old_job_id in active_jobs:
        print(sample, old_job_id, active_jobs[old_job_id])
        continue

    result = subprocess.run(
        ["sbatch", str(submit_script), job["command"]],
        stdout=subprocess.PIPE,
        text=True,
        check=True,
    )
    job["jobid"] = result.stdout.split()[-1]
    print(sample, old_job_id, "->", job["jobid"])

with jobs_path.open("w") as f:
    json.dump(jobs, f, indent=4)
    f.write("\n")
