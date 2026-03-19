#!/usr/bin/env python3

from subprocess import run
import json
import re
import os

base = "/scratch-cbe/users/alikaan.gueven/AN_plots/ParT_hists/plotconfig_Run2_MLscore_first"

json_files = [
    os.path.join(base, "sig",  "job_ids2018.json"),
    os.path.join(base, "bkg",  "job_ids2018.json"),
    os.path.join(base, "data", "job_ids2018.json"),
]

for json_path in json_files:
    with open(json_path) as f:
        job_dict = json.load(f)

    for key, info in job_dict.items():
        if info.get("status") != "prepared":
            continue

        result = run(info["command"], shell=True, capture_output=True, text=True)

        if result.returncode != 0:
            info["status"] = "submit_failed"
            info["stderr"] = result.stderr.strip()
            print(f"FAILED: {key}")
            continue

        m = re.search(r"\d+", result.stdout)
        info["jobid"] = m.group() if m else None
        info["status"] = "submitted"
        info["stdout"] = result.stdout.strip()

        print(result.stdout.strip())

    with open(json_path, "w") as f:
        json.dump(job_dict, f, indent=2)