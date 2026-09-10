#!/usr/bin/env python3

import json
import subprocess
import sys
from pathlib import Path


testk_dir = Path(__file__).resolve().parents[1]
softdv_dir = Path(__file__).resolve().parents[3]
json_path = softdv_dir / "Samples/json/eos_central_C1N2_Run3.json"
output_dir = testk_dir / "sumWeights/central_C1N2"
jobs_path = output_dir / "job_ids.json"
worker = Path(__file__).with_name("get_sumweights_job.py")

with jobs_path.open() as f:
    jobs = json.load(f)

failed_samples = [
    sample for sample, job in jobs.items() if not Path(job["output"]).exists()
]

print(f"Missing outputs: {len(failed_samples)}")

for sample in failed_samples:
    output = output_dir / f"{sample}.json"
    print(f"Processing {sample}", flush=True)
    subprocess.run(
        [
            sys.executable,
            str(worker),
            "--json",
            str(json_path),
            "--sample",
            sample,
            "--output",
            str(output),
        ],
        check=True,
    )
