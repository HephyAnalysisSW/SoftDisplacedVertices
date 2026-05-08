from subprocess import run
import glob
import os
import shlex
from collections import defaultdict


# Edit this to the datacards directory you want to combine.
DATACARDS_DIR = "/users/alikaan.gueven/AOD_to_nanoAOD/Plotter_run3/CMSSW_15_0_5/src/SoftDisplacedVertices/Plotter/limits/test"


groups = defaultdict(dict)


def split_year_piece(basename):
    for year in ["2017", "2018"]:
        token = f"_{year}"
        idx = basename.rfind(token)
        if idx == -1:
            continue

        prefix = basename[:idx]
        suffix = basename[idx + len(token):]
        if not prefix or not suffix.endswith(".txt"):
            continue

        return prefix, year, suffix

    return None


for path in glob.glob(os.path.join(DATACARDS_DIR, "*.txt")):
    basename = os.path.basename(path)
    parts = split_year_piece(basename)
    if parts is None:
        continue

    prefix, year, suffix = parts
    groups[(prefix, suffix)][year] = path


for (prefix, suffix), cards in sorted(groups.items()):
    if "2017" not in cards or "2018" not in cards:
        continue

    output_path = os.path.join(DATACARDS_DIR, f"{prefix}_run2{suffix}")
    cmd = (
        f"combineCards.py "
        f"y2017={shlex.quote(cards['2017'])} "
        f"y2018={shlex.quote(cards['2018'])} "
        f"> {shlex.quote(output_path)}"
    )

    print("CMD:")
    print(cmd)
    print()
    run(cmd, shell=True)
    print("-" * 80)
    print()
