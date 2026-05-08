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
SIGNAL_RE = re.compile(
    r"^(?P<family>stop(?:ML(?:study)?)?|C1N2(?:ML(?:study)?)?)_"
    r"(?P<params>M\d+_\d+_ct[^_]+_\d{4})_hist\d+\.root$"
)
RAW_HIST_RE = re.compile(r"_hist\d+\.root$")
VALID_ERAS = ("2017", "2018", "2022Pre", "2022Post", "2023Pre", "2023Post", "2024")


def natural_key(path):
    parts = re.split(r"(\d+)", path.name)
    return [int(part) if part.isdigit() else part for part in parts]


def run_hadd(output_file, input_files, dryrun=False):
    if not input_files:
        return

    ordered_files = sorted(input_files, key=natural_key)
    cmd = ["hadd", "-f", str(output_file), *[str(path) for path in ordered_files]]
    if dryrun:
        print('\nCMD:\n', " ".join(cmd), '\n')
    else:
        run(cmd, check=True)
    print("-" * 80)


def is_raw_hist_file(path):
    return bool(RAW_HIST_RE.search(path.name))


def find_eras(files):
    eras = set()
    for path in files:
        if not is_raw_hist_file(path):
            continue
        for era in VALID_ERAS:
            if era in path.name:
                eras.add(era)
    return sorted(eras)


def group_signal_files(files):
    groups = defaultdict(list)
    for path in files:
        match = SIGNAL_RE.match(path.name)
        if not match:
            continue

        family = "stop" if match.group("family").startswith("stop") else "C1N2"
        key = f"{family}_{match.group('params')}"
        groups[key].append(path)

    return groups


def merge_data(files, directory, dryrun):
    for year in find_eras(files):
        year_files = [
            path for path in files
            if path.name.startswith(("met", "jetmet")) and year in path.name and is_raw_hist_file(path)
        ]
        if year_files:
            run_hadd(directory / f"met_{year}_hist.root", year_files, dryrun)


def merge_backgrounds(files, directory, dryrun):
    for year in find_eras(files):
        groups = {
            "wjets": [
                path for path in files
                if path.name.lower().startswith("w") and year in path.name and is_raw_hist_file(path)
            ],
            "zjets": [
                path for path in files
                if path.name.lower().startswith("z") and year in path.name and is_raw_hist_file(path)
            ],
            "qcd": [
                path for path in files
                if path.name.lower().startswith("qcd") and year in path.name and is_raw_hist_file(path)
            ],
            "top": [
                path for path in files
                if (
                    path.name.startswith("tt") or path.name.startswith("st_")
                ) and year in path.name and is_raw_hist_file(path)
            ],
        }

        merged = []
        for sample, sample_files in groups.items():
            if not sample_files:
                continue
            output_file = directory / f"{sample}_{year}_hist.root"
            run_hadd(output_file, sample_files, dryrun)
            merged.append(output_file)

        if merged:
            run_hadd(directory / f"all_{year}_hist.root", merged, dryrun)


def merge_signals(files, directory, dryrun):
    for sample, sample_files in sorted(group_signal_files(files).items()):
        run_hadd(directory / f"{sample}_hist.root", sample_files, dryrun)


def process_directory(directory, dryrun):
    root_files = [path for path in directory.iterdir() if path.is_file() and path.suffix == ".root"]
    if not root_files:
        return

    print(f"Processing {directory}")
    
    merge_data(root_files, directory, dryrun)
    merge_backgrounds(root_files, directory, dryrun)
    merge_signals(root_files, directory, dryrun)


if __name__ == "__main__":
    work_dir = BASE_DIR / args.uniquedir
    if not work_dir.is_dir():
        raise FileNotFoundError(f"Directory not found: {work_dir}")

    subdirs = sorted(path for path in work_dir.iterdir() if path.is_dir())

    for subdir in subdirs:
        process_directory(subdir, args.dryrun)
