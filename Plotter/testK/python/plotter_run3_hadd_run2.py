import argparse
import re
from collections import defaultdict
from pathlib import Path
from subprocess import run


parser = argparse.ArgumentParser()
parser.add_argument("--uniquedir", required=True, help="e.g. AN-25-092_ML_plots3")
parser.add_argument("--dryrun", action="store_true")
args = parser.parse_args()


BASE = Path("/scratch-cbe/users/alikaan.gueven/AN_plots/ParT_hists") / args.uniquedir
YEARS = ("2017", "2018")
SIGNAL_RE = re.compile(
    r"(?P<sample>(?:stop(?:ML(?:study)?)?|C1N2(?:ML(?:study)?)?)_M\d+_\d+_ct[^_]+)"
    r"_(?:2017|2018)_hist\.root$"
)


def hadd(output, inputs):
    inputs = sorted(path for path in inputs if path.is_file())
    if not inputs:
        return

    output.parent.mkdir(exist_ok=True)
    cmd = ["hadd", "-f", str(output), *map(str, inputs)]
    print(" ".join(cmd))
    if not args.dryrun:
        run(cmd, check=True)


def year_files(kind, name):
    return [BASE / f"{kind}{year[-2:]}" / f"{name}_{year}_hist.root" for year in YEARS]


def merge_data():
    hadd(BASE / "data_run2" / "met_run2_hist.root", year_files("data", "met"))


def merge_backgrounds():
    for sample in ("wjets", "zjets", "qcd", "top", "all"):
        hadd(BASE / "bkg_run2" / f"{sample}_run2_hist.root", year_files("bkg", sample))


def merge_signals():
    groups = defaultdict(list)
    for year in YEARS:
        for path in (BASE / f"sig{year[-2:]}").glob(f"*_{year}_hist.root"):
            match = SIGNAL_RE.match(path.name)
            if match:
                groups[match.group("sample")].append(path)

    for sample, inputs in sorted(groups.items()):
        hadd(BASE / "sig_run2" / f"{sample}_run2_hist.root", inputs)


if not BASE.is_dir():
    raise FileNotFoundError(f"Directory not found: {BASE}")

merge_data()
merge_backgrounds()
merge_signals()
