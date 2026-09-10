#!/usr/bin/env python3

import json
import subprocess
from pathlib import Path


json_path = (
    Path(__file__).resolve().parents[3]
    / "Samples/json/eos_central_C1N2_Run3.json"
)
output_path = json_path.with_name(f"{json_path.stem}_edited.json")
eos_mount = Path("/eos/vbc/experiments/cms")


def das(query):
    return subprocess.run(
        ["dasgoclient", "-query", query, "-limit", "1"],
        stdout=subprocess.PIPE,
        text=True,
        check=True,
    ).stdout.strip()


with json_path.open() as f:
    data = json.load(f)

datasets = {}
dirs = {}
logical_dirs = {}

for name, nano_dataset in data["CustomNanoAOD"]["dataset"].items():
    print(name, flush=True)
    dataset = das(f"parent dataset={nano_dataset} instance=prod/phys03")
    logical_dir = Path(
        das(f"file dataset={dataset} instance=prod/phys03")
    ).parents[2]

    datasets[name] = dataset
    logical_dirs[name] = str(logical_dir)
    dirs[name] = str(eos_mount / logical_dir.relative_to("/"))

data["CustomMiniAOD"] = {
    "dataset": datasets,
    "dir": dirs,
    "logical_dir": logical_dirs,
}

with output_path.open("w") as f:
    json.dump(data, f, indent=4)
    f.write("\n")
