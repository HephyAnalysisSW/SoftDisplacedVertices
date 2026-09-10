#!/usr/bin/env python3

"""Plot vertex-fit ndof for fixed values of SDVSecVtx_tracksSize."""

from pathlib import Path

import awkward as ak
import matplotlib.pyplot as plt
import numpy as np
import uproot


INPUT_FILE = Path(
    "/scratch-cbe/users/alikaan.gueven/ML_KAAN/20260112/data_22/jetmet_2022c/"
    "Run2022C_JetMET_nano_v2/260205_091527/0000/NanoAOD_1.root"
)
OUTPUT_DIR = Path(__file__).resolve().parents[1] / "codex_outputs"


events = uproot.open(f"{INPUT_FILE}:Events")
arrays = events.arrays(["SDVSecVtx_ndof", "SDVSecVtx_tracksSize"])
OUTPUT_DIR.mkdir(exist_ok=True)

for tracks_size in (2, 3, 4, 5):
    ndof = ak.to_numpy(
        ak.flatten(arrays["SDVSecVtx_ndof"][arrays["SDVSecVtx_tracksSize"] == tracks_size])
    )

    plt.figure(figsize=(7, 5))
    plt.hist(ndof, bins=np.arange(0, 8.2, 0.2), histtype="step", linewidth=1.8)
    plt.xlabel("SDVSecVtx_ndof")
    plt.ylabel("Vertices")
    plt.title(f"SDV vertices with tracksSize = {tracks_size}")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / f"SDVSecVtx_ndof_tracksSize{tracks_size}.png", dpi=150)
    plt.close()

    print(f"tracksSize = {tracks_size}: {len(ndof)} vertices")
