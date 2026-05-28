import argparse
import pickle
import re
import shutil
from collections import defaultdict
from pathlib import Path
from subprocess import run

import numpy as np


parser = argparse.ArgumentParser()
parser.add_argument("--uniquedir", type=str, required=True, help="e.g. vtx_PART_859_epoch_87_testxxx")
parser.add_argument("--dryrun", action='store_true', help="Should it run the commands or print it?")
args = parser.parse_args()


BASE_DIR = Path("/scratch-cbe/users/alikaan.gueven/AN_plots/ParT_hists")
SIGNAL_RE = re.compile(
    r"^(?P<family>stop(?:ML(?:study)?)?|C1N2(?:ML(?:study)?)?)_"
    r"(?P<params>M\d+_\d+_ct[^_]+_\d{4})_hist\d+\.(?:root|pkl)$"
)
RAW_HIST_RE = re.compile(r"_hist\d+\.(?:root|pkl)$")
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


def merge_pickle_values(values, key_path=""):
    first = values[0]

    if isinstance(first, dict):
        first_keys = list(first.keys())
        first_key_set = set(first_keys)
        for value in values[1:]:
            if not isinstance(value, dict):
                raise TypeError(f"Mixed pickle structure at {key_path or '<root>'}")
            if set(value.keys()) != first_key_set:
                raise KeyError(f"Mismatched pickle keys at {key_path or '<root>'}")

        return {
            key: merge_pickle_values(
                [value[key] for value in values],
                f"{key_path}.{key}" if key_path else key,
            )
            for key in first_keys
        }

    if isinstance(first, np.ndarray):
        for value in values[1:]:
            if not isinstance(value, np.ndarray):
                raise TypeError(f"Mixed pickle value types at {key_path}")
        return np.concatenate(values, axis=0)

    raise TypeError(f"Unsupported pickle value at {key_path}: {type(first).__name__}")


def run_pickle_merge(output_file, input_files, dryrun=False):
    if not input_files:
        return

    ordered_files = sorted(input_files, key=natural_key)
    print(f"pkl Target file: {output_file}")
    for index, path in enumerate(ordered_files, start=1):
        print(f"pkl Source file {index}: {path}")

    if dryrun:
        print()
    else:
        if len(ordered_files) == 1:
            shutil.copyfile(ordered_files[0], output_file)
            print("-" * 80)
            return

        loaded = [load_pickle(path) for path in ordered_files]

        merged = merge_pickle_values(loaded)
        with open(output_file, "wb") as handle:
            pickle.dump(merged, handle, protocol=pickle.HIGHEST_PROTOCOL)
    print("-" * 80)


def load_pickle(path):
    with open(path, "rb") as handle:
        return pickle.load(handle)


def run_merge(output_file, input_files, dryrun=False):
    if output_file.suffix == ".root":
        run_hadd(output_file, input_files, dryrun)
    elif output_file.suffix == ".pkl":
        run_pickle_merge(output_file, input_files, dryrun)
    else:
        raise ValueError(f"Unsupported output suffix: {output_file.suffix}")


def is_raw_hist_file(path):
    return bool(RAW_HIST_RE.search(path.name))


def is_signal_file(path):
    return bool(SIGNAL_RE.match(path.name))


def era_in_name(era, name):
    return era.lower() in name.lower().replace("_", "")


def find_eras(files):
    eras = set()
    for path in files:
        if not is_raw_hist_file(path):
            continue
        for era in VALID_ERAS:
            if era_in_name(era, path.name):
                eras.add(era)
    return sorted(eras)


def group_signal_files(files):
    groups = defaultdict(list)
    for path in files:
        match = SIGNAL_RE.match(path.name)
        if not match:
            continue

        key = f"{match.group('family')}_{match.group('params')}"
        groups[key].append(path)

    return groups


def merge_data(files, directory, dryrun):
    data_files = [
        path for path in files
        if path.name.startswith(("data", "met", "jetmet")) and is_raw_hist_file(path)
    ]
    if not data_files:
        return

    directory_year = directory.name.removeprefix("data_")
    years = [directory_year] if directory_year in VALID_ERAS else find_eras(data_files)

    for year in years:
        year_files = [path for path in data_files if era_in_name(year, path.name)]
        if directory_year == year:
            year_files = data_files
        if not year_files:
            continue

        output_file = directory / f"data_{year}_hist{year_files[0].suffix}"
        run_merge(output_file, year_files, dryrun)


def merge_backgrounds(files, directory, dryrun):
    for year in find_eras(files):
        groups = {
            "wjets": [
                path for path in files
                if path.name.lower().startswith("w") and era_in_name(year, path.name) and is_raw_hist_file(path)
            ],
            "zjets": [
                path for path in files
                if path.name.lower().startswith("z") and era_in_name(year, path.name) and is_raw_hist_file(path)
            ],
            "qcd": [
                path for path in files
                if path.name.lower().startswith("qcd") and era_in_name(year, path.name) and is_raw_hist_file(path)
            ],
            "top": [
                path for path in files
                if (
                    path.name.startswith("tt") or path.name.startswith("st_")
                ) and era_in_name(year, path.name) and is_raw_hist_file(path)
            ],
        }

        merged = []
        for sample, sample_files in groups.items():
            if not sample_files:
                continue
            output_file = directory / f"{sample}_{year}_hist{sample_files[0].suffix}"
            run_merge(output_file, sample_files, dryrun)
            merged.append(output_file)

        if merged:
            run_merge(directory / f"bkg_{year}_hist{merged[0].suffix}", merged, dryrun)


def merge_signals(files, directory, dryrun):
    for sample, sample_files in sorted(group_signal_files(files).items()):
        run_merge(directory / f"{sample}_hist{sample_files[0].suffix}", sample_files, dryrun)


def process_directory(directory, dryrun):
    root_files = [
        path for path in directory.iterdir()
        if path.is_file() and path.suffix == ".root" and is_raw_hist_file(path)
    ]
    signal_pickle_files = [
        path for path in directory.iterdir()
        if path.is_file() and path.suffix == ".pkl" and is_signal_file(path)
    ]
    if not root_files and not signal_pickle_files:
        return

    print(f"Processing {directory}")

    merge_data(root_files, directory, dryrun)
    merge_backgrounds(root_files, directory, dryrun)
    merge_signals(root_files, directory, dryrun)
    merge_signals(signal_pickle_files, directory, dryrun)


if __name__ == "__main__":
    work_dir = BASE_DIR / args.uniquedir
    if not work_dir.is_dir():
        raise FileNotFoundError(f"Directory not found: {work_dir}")

    subdirs = sorted(path for path in work_dir.iterdir() if path.is_dir())

    for subdir in subdirs:
        process_directory(subdir, args.dryrun)
