from subprocess import run
import argparse
import glob
import os
import re
import shlex
from collections import defaultdict


parser = argparse.ArgumentParser()
parser.add_argument("--uniquedir", type=str, required=True, help="e.g. vtx_PART_859_epoch_87_testxxx")
args = parser.parse_args()


YEARS = [2017, 2018]
outDir_base = "/scratch-cbe/users/alikaan.gueven/AN_plots/"
work_subdir = "ParT_hists"
unique_dir = args.uniquedir
workbase_dir = os.path.join(outDir_base, work_subdir)
work_dir = os.path.join(workbase_dir, unique_dir)

dirs = {
    "sig17":    os.path.join(work_dir, "sig17"),
    "bkg17":    os.path.join(work_dir, "bkg17"),
    "data17":   os.path.join(work_dir, "data17"),
    "sig18":    os.path.join(work_dir, "sig18"),
    "bkg18":    os.path.join(work_dir, "bkg18"),
    "data18":   os.path.join(work_dir, "data18"),
    "run2":     os.path.join(work_dir, "run2"),
}

os.makedirs(os.path.join(dirs["run2"], "sig"), exist_ok=True)
os.makedirs(os.path.join(dirs["run2"], "bkg"), exist_ok=True)
os.makedirs(os.path.join(dirs["run2"], "data"), exist_ok=True)


def quote_join(paths):
    return " ".join(shlex.quote(path) for path in paths)


def run_cmd(cmd):
    print("CMD:")
    print(cmd)
    print()
    run(cmd, shell=True)
    print("-" * 80)
    print()


def build_signal_groups(sig_dir):
    glob_patterns = []
    for sample_year in YEARS:
        glob_patterns.append(os.path.join(sig_dir, f"stop_M*_ct*_{sample_year}_hist*.root"))
        glob_patterns.append(os.path.join(sig_dir, f"stopML_M*_ct*_{sample_year}_hist*.root"))
        glob_patterns.append(os.path.join(sig_dir, f"stopMLstudy_M*_ct*_{sample_year}_hist*.root"))
        glob_patterns.append(os.path.join(sig_dir, f"C1N2MLstudy_M*_ct*_{sample_year}_hist*.root"))
        glob_patterns.append(os.path.join(sig_dir, f"C1N2ML_M*_ct*_{sample_year}_hist*.root"))

    files = []
    for pattern in glob_patterns:
        files.extend(glob.glob(pattern))

    groups = defaultdict(list)

    re_patterns = []
    re_patterns.append(re.compile(r"(stop_M\d+_\d+_ct[^_]+_(2017|2018))_hist\d+\.root$"))
    re_patterns.append(re.compile(r"(stopML_M\d+_\d+_ct[^_]+_(2017|2018))_hist\d+\.root$"))
    re_patterns.append(re.compile(r"(stopMLstudy_M\d+_\d+_ct[^_]+_(2017|2018))_hist\d+\.root$"))
    re_patterns.append(re.compile(r"(C1N2MLstudy_M\d+_\d+_ct[^_]+_(2017|2018))_hist\d+\.root$"))
    re_patterns.append(re.compile(r"(C1N2ML_M\d+_\d+_ct[^_]+_(2017|2018))_hist\d+\.root$"))

    for input_file in files:
        basename = os.path.basename(input_file)
        for pattern in re_patterns:
            match = pattern.match(basename)
            if match:
                groups[match.group(1)].append(input_file)
                break

    return groups


def hadd_year(year):
    suffix = str(year)[-2:]
    sig_dir = dirs[f"sig{suffix}"]
    bkg_dir = dirs[f"bkg{suffix}"]
    data_dir = dirs[f"data{suffix}"]

    if os.path.isdir(data_dir):
        data_files = sorted(glob.glob(os.path.join(data_dir, f"met{year}*.root")))
        if data_files:
            met_out = os.path.join(data_dir, f"met_{year}_hist.root")
            run_cmd(f"hadd -f {shlex.quote(met_out)} {quote_join(data_files)}")

    if os.path.isdir(bkg_dir):
        wjets_files = sorted(glob.glob(os.path.join(bkg_dir, f"w*{year}*.root")))
        zjets_files = sorted(glob.glob(os.path.join(bkg_dir, f"z*{year}*.root")))
        qcd_files = sorted(glob.glob(os.path.join(bkg_dir, f"qcd*{year}*.root")))
        top_files = sorted(glob.glob(os.path.join(bkg_dir, f"tt*{year}*.root")))
        top_files.extend(sorted(glob.glob(os.path.join(bkg_dir, f"st_*{year}*.root"))))

        bkg_outputs = []
        bkg_groups = [
            ("wjets", wjets_files),
            ("zjets", zjets_files),
            ("qcd", qcd_files),
            ("top", top_files),
        ]

        for process, files in bkg_groups:
            if not files:
                continue
            out_file = os.path.join(bkg_dir, f"{process}_{year}_hist.root")
            run_cmd(f"hadd -f {shlex.quote(out_file)} {quote_join(files)}")
            bkg_outputs.append(out_file)

        if bkg_outputs:
            all_bkg_out = os.path.join(bkg_dir, f"all_{year}_hist.root")
            run_cmd(f"hadd -f {shlex.quote(all_bkg_out)} {quote_join(bkg_outputs)}")

    if os.path.isdir(sig_dir):
        sig_groups = build_signal_groups(sig_dir)
        for key, group in sorted(sig_groups.items()):
            group_out = os.path.join(sig_dir, f"{key}_hist.root")
            run_cmd(f"hadd -f {shlex.quote(group_out)} {quote_join(sorted(group))}")


def build_run2_signal_groups():
    groups = defaultdict(list)
    re_patterns = []
    re_patterns.append(re.compile(r"(stop_M\d+_\d+_ct[^_]+)_(2017|2018)_hist\.root$"))
    re_patterns.append(re.compile(r"(stopML_M\d+_\d+_ct[^_]+)_(2017|2018)_hist\.root$"))
    re_patterns.append(re.compile(r"(stopMLstudy_M\d+_\d+_ct[^_]+)_(2017|2018)_hist\.root$"))
    re_patterns.append(re.compile(r"(C1N2MLstudy_M\d+_\d+_ct[^_]+)_(2017|2018)_hist\.root$"))
    re_patterns.append(re.compile(r"(C1N2ML_M\d+_\d+_ct[^_]+)_(2017|2018)_hist\.root$"))

    for year in YEARS:
        suffix = str(year)[-2:]
        sig_dir = dirs[f"sig{suffix}"]
        if not os.path.isdir(sig_dir):
            continue

        year_files = []
        for sample_year in YEARS:
            for pattern in [
                os.path.join(sig_dir, f"stop_M*_ct*_{sample_year}_hist.root"),
                os.path.join(sig_dir, f"stopML_M*_ct*_{sample_year}_hist.root"),
                os.path.join(sig_dir, f"stopMLstudy_M*_ct*_{sample_year}_hist.root"),
                os.path.join(sig_dir, f"C1N2MLstudy_M*_ct*_{sample_year}_hist.root"),
                os.path.join(sig_dir, f"C1N2ML_M*_ct*_{sample_year}_hist.root"),
            ]:
                year_files.extend(glob.glob(pattern))

        for input_file in year_files:
            basename = os.path.basename(input_file)
            for pattern in re_patterns:
                match = pattern.match(basename)
                if match:
                    groups[match.group(1)].append(input_file)
                    break

    return groups


def hadd_run2():
    run2_sig_dir = os.path.join(dirs["run2"], "sig")
    run2_bkg_dir = os.path.join(dirs["run2"], "bkg")
    run2_data_dir = os.path.join(dirs["run2"], "data")

    data_inputs = []
    for year in YEARS:
        suffix = str(year)[-2:]
        input_file = os.path.join(dirs[f"data{suffix}"], f"met_{year}_hist.root")
        if os.path.isfile(input_file):
            data_inputs.append(input_file)
    if data_inputs:
        run_cmd(
            f"hadd -f {shlex.quote(os.path.join(run2_data_dir, 'met_run2_hist.root'))} "
            f"{quote_join(data_inputs)}"
        )

    for process in ["wjets", "zjets", "qcd", "top", "all"]:
        process_inputs = []
        for year in YEARS:
            suffix = str(year)[-2:]
            input_file = os.path.join(dirs[f"bkg{suffix}"], f"{process}_{year}_hist.root")
            if os.path.isfile(input_file):
                process_inputs.append(input_file)
        if process_inputs:
            run_cmd(
                f"hadd -f {shlex.quote(os.path.join(run2_bkg_dir, f'{process}_run2_hist.root'))} "
                f"{quote_join(process_inputs)}"
            )

    run2_sig_groups = build_run2_signal_groups()
    for key, group in sorted(run2_sig_groups.items()):
        out_file = os.path.join(run2_sig_dir, f"{key}_run2_hist.root")
        run_cmd(f"hadd -f {shlex.quote(out_file)} {quote_join(sorted(group))}")


for year in YEARS:
    hadd_year(year)

hadd_run2()
