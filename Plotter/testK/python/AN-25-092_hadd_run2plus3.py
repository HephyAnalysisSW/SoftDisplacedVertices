import argparse
import re
from collections import defaultdict
from pathlib import Path
from subprocess import run


parser = argparse.ArgumentParser()
parser.add_argument("--uniquedir", type=str, required=True, help="e.g. vtx_PART_859_epoch_87_testxxx")
parser.add_argument("--dryrun", action='store_true', help="Should it run the commands or print it?")
args = parser.parse_args()


BASE_DIR = Path("/scratch-cbe/users/alikaan.gueven/AN_plots/ParT_hists")
ERAS = ("2017", "2018", "2022Pre", "2022Post", "2023Pre", "2023Post", "2024")
BACKGROUND_SAMPLES = ("wjets", "zjets", "qcd", "top", "bkg")
SIGNAL_RE = re.compile(
    r"^(?P<sample>(?:stop(?:ML(?:study)?)?|C1N2(?:ML(?:study)?)?)_"
    r"M\d+_\d+_ct[^_]+)_(?P<year>2017|2018|2022Pre|2022Post|2023Pre|2023Post|2024)_hist\.root$",
    re.IGNORECASE,
)


def natural_key(path):
    parts = re.split(r"(\d+)", path.name)
    return [int(part) if part.isdigit() else part for part in parts]


def run_hadd(output_file, input_files, dryrun=False):
    input_files = sorted([path for path in input_files if path.is_file()], key=natural_key)
    if not input_files:
        return

    cmd = ["hadd", "-f", str(output_file), *[str(path) for path in input_files]]
    if dryrun:
        print('\nCMD:\n', " ".join(cmd), '\n')
    else:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        run(cmd, check=True)
    print("-" * 80)


def existing_dirs(work_dir, prefix):
    directories = []
    for era in ERAS:
        directory = work_dir / f"{prefix}_{era}"
        if directory.is_dir():
            directories.append((era, directory))
    return directories


def data_file_for_era(directory, era):
    candidates = [
        directory / f"data_{era}_hist.root",
        directory / f"met_{era}_hist.root",
        directory / f"jetmet_{era}_hist.root",
    ]
    for path in candidates:
        if path.is_file():
            return path
    return None


def merge_data(work_dir, output_dir, dryrun):
    inputs = []
    for era, directory in existing_dirs(work_dir, "data"):
        path = data_file_for_era(directory, era)
        if path is not None:
            inputs.append(path)

    run_hadd(output_dir / "data_run2plus3_hist.root", inputs, dryrun)


def merge_backgrounds(work_dir, output_dir, dryrun):
    for sample in BACKGROUND_SAMPLES:
        inputs = []
        for era, directory in existing_dirs(work_dir, "bkg"):
            path = directory / f"{sample}_{era}_hist.root"
            if path.is_file():
                inputs.append(path)

        run_hadd(output_dir / f"{sample}_run2plus3_hist.root", inputs, dryrun)


def merge_signals(work_dir, output_dir, dryrun):
    groups = defaultdict(list)
    for era, directory in existing_dirs(work_dir, "sig"):
        for path in directory.glob("*_hist.root"):
            match = SIGNAL_RE.match(path.name)
            if not match:
                continue
            groups[match.group("sample")].append(path)

    for sample, input_files in sorted(groups.items()):
        run_hadd(output_dir / f"{sample}_run2plus3_hist.root", input_files, dryrun)


if __name__ == "__main__":
    work_dir = BASE_DIR / args.uniquedir
    if not work_dir.is_dir():
        raise FileNotFoundError(f"Directory not found: {work_dir}")

    output_dir = work_dir / "run2plus3"

    merge_data(work_dir, output_dir, args.dryrun)
    merge_backgrounds(work_dir, output_dir, args.dryrun)
    merge_signals(work_dir, output_dir, args.dryrun)
