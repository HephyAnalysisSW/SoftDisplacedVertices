#!/usr/bin/env python3

import json
import subprocess
from pathlib import Path


testk_dir = Path(__file__).resolve().parents[1]
softdv_dir = Path(__file__).resolve().parents[3]
json_path = softdv_dir / "Samples/json/eos_central_C1N2_Run3.json"
output_dir = testk_dir / "sumWeights/central_C1N2"
worker = Path(__file__).with_name("get_sumweights_job.py")
submit_script = testk_dir / "sh/submit_to_cpu1.sh"

with json_path.open() as f:
    samples = json.load(f)["CustomMiniAOD"]["dir"]

jobs = {}

for sample in samples:
    output = output_dir / f"{sample}.json"
    command = f"python3 {worker} --json {json_path} --sample {sample} --output {output}"
    result = subprocess.run(
        ["sbatch", str(submit_script), command],
        stdout=subprocess.PIPE,
        text=True,
        check=True,
    )
    job_id = result.stdout.split()[-1]
    jobs[sample] = {"jobid": job_id, "command": command, "output": str(output)}
    print(sample, job_id)

with (output_dir / "job_ids.json").open("w") as f:
    json.dump(jobs, f, indent=4)
    f.write("\n")
