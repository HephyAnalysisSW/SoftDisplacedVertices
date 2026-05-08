#!/usr/bin/env python3
import argparse
from subprocess import run
from pathlib import Path
import json
import re
import os


parser = argparse.ArgumentParser()

help_S = """All the jobs starting after this time/date will be searched. 
The argument will be passed to sacct.
Pass the date-time like this: 2024-11-14T00:00:00"""

parser.add_argument('-S', type=str, help=help_S)
parser.add_argument('--uniquedir', type=str, required=True, help='e.g. vtx_PART_859_epoch_87_testxxx')

args = parser.parse_args()

work_dir = Path("/scratch-cbe/users/alikaan.gueven/AN_plots/ParT_hists")

if __name__=="__main__":
    base = work_dir / args.uniquedir
    subdirs = sorted(path for path in base.iterdir() if path.is_dir())
    json_files = []
    for subdir in subdirs:
        json_files.append(base / subdir / "job_ids.json")

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