#!/usr/bin/env python3

"""
Script to check job completion and create resubmission file for failed jobs
Usage: ./check_jobs.py /path/to/job
"""

import sys
import os
import re
from pathlib import Path
import json

def main():
    if len(sys.argv) != 3:
        print("Usage: ./check_jobs.py /path/to/job /path/to/json")
        sys.exit(1)
    
    job_dir = Path(sys.argv[1])
    jsonpath = Path(sys.argv[2])

    with open(jsonpath, "r") as fj:
        dinfo = json.load(fj)
        sw = dinfo["CustomNanoAOD"]["totalsumWeights"]

    d = {
            str(job_dir.name):{
                'dir':{}
                }
            }
    for x in job_dir.iterdir(): 
        if job_dir.is_dir() and x!=job_dir/"input":
            d[str(job_dir.name)]['dir'][str(x.name)] = str(x)
        d[str(job_dir.name)]["totalsumWeights"] = sw
            
    with open("sample.json", "w") as f:
        json.dump(d, f, indent=4)


if __name__ == "__main__":
    main()
