#!/usr/bin/env python3

import argparse
import json
from pathlib import Path

import ROOT


parser = argparse.ArgumentParser()
parser.add_argument("--json", required=True)
parser.add_argument("--sample", required=True)
parser.add_argument("--output", required=True)
args = parser.parse_args()

with open(args.json) as f:
    sample_info = json.load(f)["CustomNanoAOD"]

sample_dir = Path(sample_info["dir"][args.sample])
logical_dir = Path(sample_info["logical_dir"][args.sample])
local_files = sorted(sample_dir.rglob("*.root"))
files = [str(path) for path in local_files]

luminosity_blocks = ROOT.RDataFrame("LuminosityBlocks", files)
sum_weights = float(
    luminosity_blocks.Sum("GenFilter_sumWeights").GetValue()
)

output = {
    "sample": args.sample,
    "dir": str(sample_dir),
    "logical_dir": str(logical_dir),
    "nFiles": len(files),
    "totalsumWeights": sum_weights,
}

with open(args.output, "w") as f:
    json.dump(output, f, indent=4)
    f.write("\n")
