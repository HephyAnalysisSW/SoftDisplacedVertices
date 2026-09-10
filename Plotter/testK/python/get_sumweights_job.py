#!/usr/bin/env python3

import argparse
import json
from pathlib import Path

from DataFormats.FWLite import Handle, Lumis


parser = argparse.ArgumentParser()
parser.add_argument("--json", required=True)
parser.add_argument("--sample", required=True)
parser.add_argument("--output", required=True)
args = parser.parse_args()

with open(args.json) as f:
    sample_info = json.load(f)["CustomMiniAOD"]

sample_dir = Path(sample_info["dir"][args.sample])
logical_dir = Path(sample_info["logical_dir"][args.sample])

sum_weights = 0.0
sum_pass_weights = 0.0
files = sorted(sample_dir.rglob("*.root"))
handle = Handle("GenFilterInfo")

for file_path in files:
    logical_file = logical_dir / file_path.relative_to(sample_dir)
    file_url = f"root://eos.grid.vbc.ac.at/{logical_file}"
    lumis = Lumis(file_url)
    for lumi in lumis:
        lumi.getByLabel("genFilterEfficiencyProducer", handle)
        info = handle.product()
        sum_weights += info.sumWeights()
        sum_pass_weights += info.sumPassWeights()
    lumis._tfile.Close()

output = {
    "sample": args.sample,
    "dir": str(sample_dir),
    "logical_dir": str(logical_dir),
    "nFiles": len(files),
    "totalsumWeights": sum_weights,
    "totalsumPassWeights": sum_pass_weights,
}

with open(args.output, "w") as f:
    json.dump(output, f, indent=4)
    f.write("\n")
