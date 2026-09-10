#!/usr/bin/env python3

import json
import subprocess
from pathlib import Path


json_path = (
    Path(__file__).resolve().parents[3] / "Samples/json/central_C1N2_2223.json"
)
eos_mount = Path("/eos/vbc/experiments/cms")

with json_path.open() as f:
    datasets = json.load(f)

datasets = {name: dataset.strip("'\"") for name, dataset in datasets.items()}
dirs = {}
logical_dirs = {}

for name, dataset in datasets.items():
    print(name, flush=True)
    result = subprocess.run(
        [
            "dasgoclient",
            "-query",
            f"file dataset={dataset} instance=prod/phys03",
            "-limit",
            "1",
        ],
        stdout=subprocess.PIPE,
        text=True,
        check=True,
    )
    logical_dir = Path(result.stdout.strip()).parents[2]
    logical_dirs[name] = str(logical_dir)
    dirs[name] = str(eos_mount / logical_dir.relative_to("/"))

data = {
    "CustomNanoAOD": {
        "dataset": datasets,
        "dir": dirs,
        "logical_dir": logical_dirs,
    }
}

with json_path.open("w") as f:
    json.dump(data, f, indent=4)
    f.write("\n")
