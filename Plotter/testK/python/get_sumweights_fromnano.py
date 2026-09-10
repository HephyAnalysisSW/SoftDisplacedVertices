#!/usr/bin/env python3

import json
from pathlib import Path

import ROOT
from tqdm import tqdm


testk_dir = Path(__file__).resolve().parents[1]
softdv_dir = Path(__file__).resolve().parents[3]
input_json = softdv_dir / "Samples/json/eos_central_C1N2_Run3.json"
output_json = testk_dir / "sumWeights_fromnano/central_C1N2.json"

with input_json.open() as f:
    sample_info = json.load(f)["CustomNanoAOD"]

directories = sample_info["dir"]
logical_directories = sample_info["logical_dir"]

sum_weights = {}

for sample in tqdm(directories, desc="Samples", unit="sample"):
    directory = Path(directories[sample])
    logical_directory = Path(logical_directories[sample])
    files = [
        f"root://eos.grid.vbc.ac.at/{logical_directory / path.relative_to(directory)}"
        for path in directory.rglob("*.root")
    ]
    luminosity_blocks = ROOT.RDataFrame("LuminosityBlocks", files)
    sum_weights[sample] = float(
        luminosity_blocks.Sum("GenFilter_sumWeights").GetValue()
    )

with output_json.open("w") as f:
    json.dump({"totalsumWeights": sum_weights}, f, indent=4)
    f.write("\n")
