# Usage:
# python3 AN-25-092_make_multiplane_datacards.py --xcut 700 --ycut 0.9990

import argparse
from ctypes import c_double
from pathlib import Path


OUT_DIR_BASE = Path("/scratch-cbe/users/alikaan.gueven/AN_plots")
WORK_SUBDIR = "ParT_hists"
DEFAULT_UNIQUE_DIR = "AN-25-092_ML_plots_limitcalc_v2"
MODE = "observation"

YEAR_BY_DIR = {
    "bkg17":        "2017",
    "bkg18":        "2018",
    "bkg22_pre":    "2022Pre",
    "bkg22_post":   "2022Post",
    "bkg23_pre":    "2023Pre",
    "bkg23_post":   "2023Post",
    "bkg24":        "2024",
}

SIGNAL_FILE_YEAR_BY_DIR = {
    "sig17":        "2018",
    "sig18":        "2018",
    "sig22_pre":    "2018",
    "sig22_post":   "2018",
    "sig23_pre":    "2018",
    "sig23_post":   "2018",
    "sig24":        "2018",
}

ERA_ORDER = [
    "sig17",
    "sig18",
    "sig22_pre",
    "sig22_post",
    "sig23_pre",
    "sig23_post",
    "sig24",
]

# PLANES = ["SP0", "SP1", "SP2", "SP3"]
PLANES = ["SP1", "SP2", "SP3"]
REGIONS = ["A", "B", "C", "D"]


def file_year_token(year):
    return year.lower()


def bkg_dir_for_sig_dir(sig_dir):
    return f"bkg{sig_dir[3:]}"


def datacard_year_for_sig_dir(sig_dir):
    return YEAR_BY_DIR[bkg_dir_for_sig_dir(sig_dir)]


def resolve_histdir(unique_dir, histdir):
    if histdir is not None:
        return Path(histdir)
    return OUT_DIR_BASE / WORK_SUBDIR / unique_dir


def discover_signal_dirs(histdir, requested_eras=None):
    if requested_eras is not None:
        sig_dirs = requested_eras
    else:
        discovered = [path.name for path in histdir.iterdir() if path.is_dir() and path.name.startswith("sig")]
        sig_dirs = sorted(discovered, key=lambda name: (ERA_ORDER.index(name) if name in ERA_ORDER else 999, name))

    usable = []
    for sig_dir in sig_dirs:
        usable.append(sig_dir)

    return usable


def sample_name_from_hist_file(path, year):
    suffix = f"_{file_year_token(year)}_hist.root"
    if not path.name.endswith(suffix):
        return None
    return path.name[:-len(suffix)]


def discover_samples(histdir, sig_dir, requested_samples=None):
    sig_year = SIGNAL_FILE_YEAR_BY_DIR[sig_dir]
    sig_path = histdir / sig_dir
    pattern = f"*_{file_year_token(sig_year)}_hist.root"

    samples = []
    for path in sorted(sig_path.glob(pattern)):
        sample_name = sample_name_from_hist_file(path, sig_year)
        if sample_name is not None:
            samples.append(sample_name)

    if requested_samples is not None:
        return requested_samples

    return samples


def hist_path(histdir, sample_name, sample_type, sample_dir):
    if sample_type == "sig":
        token = file_year_token(SIGNAL_FILE_YEAR_BY_DIR[sample_dir])
        return histdir / sample_dir / f"{sample_name}_{token}_hist.root"
    token = file_year_token(YEAR_BY_DIR[sample_dir])
    return histdir / sample_dir / f"all_{token}_hist.root"


def plane_hist_name(plane):
    return f"{plane}_evt/MET_pt_corr_vs_{plane}_Max_ML_score"


def get_hist(histdir, sample_name, plane, sample_type, sample_dir):
    import ROOT

    file_path = hist_path(
        histdir=histdir,
        sample_name=sample_name,
        sample_type=sample_type,
        sample_dir=sample_dir,
    )
    hist_name = plane_hist_name(plane)
    root_file = ROOT.TFile.Open(str(file_path))
    hist = root_file.Get(hist_name)
    hist.SetDirectory(0)
    root_file.Close()
    return hist


def get_region_yields(hist, xcut, ycut, verbose=False):
    xax = hist.GetXaxis()
    yax = hist.GetYaxis()

    xbin = hist.GetXaxis().FindBin(xcut)
    ybin = hist.GetYaxis().FindBin(ycut)

    last_x_bin = hist.GetNbinsX() + 1
    last_y_bin = hist.GetNbinsY() + 1
    regions = {
        "A": (xbin, last_x_bin, ybin, last_y_bin),
        "B": (1, xbin - 1, ybin, last_y_bin),
        "C": (xbin, last_x_bin, 1, ybin - 1),
        "D": (1, xbin - 1, 1, ybin - 1),
    }

    out = {}
    for region, (bx1, bx2, by1, by2) in regions.items():
        err = c_double(0.0)
        val = hist.IntegralAndError(bx1, bx2, by1, by2, err)
        out[region] = {"yield": val, "error": err.value}

        if verbose:
            print(
                region,
                "x:[", xax.GetBinLowEdge(bx1), ",", xax.GetBinUpEdge(bx2), "]",
                "y:[", yax.GetBinLowEdge(by1), ",", yax.GetBinUpEdge(by2), "]",
            )

    return out


def make_datacard(
    histdir,
    sample_name,
    xcut,
    ycut,
    outfile,
    mode="observation",
    noncl_sys=None,
    sig_dir=None,
    bkg_dir=None,
):
    """
    mode = 'Asimov' or 'observation'
    """
    bins = {}
    yields = {}
    rates = {}
    processes_num = {}
    processes_str = {}

    for plane in PLANES:
        sig_hist = get_hist(
            histdir=histdir,
            sample_name=sample_name,
            plane=plane,
            sample_type="sig",
            sample_dir=sig_dir,
        )

        bkg_hist = get_hist(
            histdir=histdir,
            sample_name=sample_name,
            plane=plane,
            sample_type="bkg",
            sample_dir=bkg_dir,
        )

        sig_table = get_region_yields(sig_hist, xcut=xcut, ycut=ycut)
        bkg_table = get_region_yields(bkg_hist, xcut=xcut, ycut=ycut)

        for region in REGIONS:
            bins[f"{plane}_{region}_sig"] = f"{plane}_{region}"
            bins[f"{plane}_{region}_bkg"] = f"{plane}_{region}"

            sig_val = sig_table[region]["yield"]
            bkg_val = bkg_table[region]["yield"]

            yields[f"{plane}_{region}_sig"] = round(sig_val, 4)

            if mode == "Asimov":
                if region != "A":
                    yields[f"{plane}_{region}_bkg"] = round(bkg_val, 4)
                else:
                    yields[f"{plane}_{region}_bkg"] = round(
                        bkg_table["B"]["yield"] *
                        bkg_table["C"]["yield"] /
                        bkg_table["D"]["yield"],
                        8,
                    )

            if mode == "observation":
                yields[f"{plane}_{region}_bkg"] = round(bkg_val, 4)

            if yields[f"{plane}_{region}_bkg"] < 0:
                yields[f"{plane}_{region}_bkg"] = 0

            rates[f"{plane}_{region}_sig"] = round(sig_val, 4)
            rates[f"{plane}_{region}_bkg"] = 1

            processes_num[f"{plane}_{region}_sig"] = 0
            processes_num[f"{plane}_{region}_bkg"] = 1

            processes_str[f"{plane}_{region}_sig"] = "sig"
            processes_str[f"{plane}_{region}_bkg"] = "bkg"

    systematics_summary = {
        "trigger": {"2017": 0, "2018": 1.027},
        "qcd_s": {"2017": 0, "2018": 1.015},
        "pdf": {"2017": 0, "2018": 1.006},
        "matveto": {"2017": 0, "2018": 1.01},
        "vtxreco": {"2017": 0, "2018": 1.107},
        "uncls_es": {"2017": 0, "2018": 1.013},
        "jes": {"2017": 0, "2018": 1.034},
        "jer": {"2017": 0, "2018": 1.008},
        "pu": {"2017": 0, "2018": 1.032},
        "lumi": {"2017": 0, "2018": 1.02},
    }

    systematics = {key: {} for key in systematics_summary}

    for key, values in systematics_summary.items():
        for plane in PLANES:
            for region in REGIONS:
                systematics[key][f"{plane}_{region}_sig"] = values["2018"]
                systematics[key][f"{plane}_{region}_bkg"] = "-"

    if noncl_sys is not None:
        systematics["nonclosure"] = {}
        for plane in PLANES:
            for region in REGIONS:
                systematics["nonclosure"][f"{plane}_{region}_sig"] = "-"
                systematics["nonclosure"][f"{plane}_{region}_bkg"] = 1.0 + noncl_sys if region == "A" else "-"

    lines = []

    lines.append(f"imax {len(PLANES) * len(REGIONS)}  number of channels")
    lines.append("jmax 1   number of processes -1")
    lines.append("kmax *   number of nuisance parameters (sources of systematical uncertainties)")

    lines.append("-" * 160)

    line = f'{"bin":<14} '
    for key, value in bins.items():
        if key[-3:] == "bkg":
            line += f"{value:<18} "
    lines.append(line)

    line = f'{"observation":<14} '
    for key, value in yields.items():
        if key[-3:] == "bkg":
            line += f"{value:<18} "
    lines.append(line)

    lines.append("-" * 160)

    line = f'{"bin":<20} '
    for value in bins.values():
        line += f"{value:<12} "
    lines.append(line)

    line = f'{"process":<20} '
    for value in processes_str.values():
        line += f"{value:<12} "
    lines.append(line)

    line = f'{"process":<20} '
    for value in processes_num.values():
        line += f"{value:<12} "
    lines.append(line)

    line = f'{"rate":<20} '
    for value in rates.values():
        line += f"{value:<12} "
    lines.append(line)

    lines.append("-" * 160)

    for sys_name, sys_dict in systematics.items():
        line = f"{sys_name:<15}{'lnN':<5} "
        for value in sys_dict.values():
            line += f"{value:<8} "
        lines.append(line)

    lines.append("")

    for key, value in bins.items():
        if processes_str[key] == "bkg":
            line = f"rate_{value:<8}"
            line += f"{'rateParam':<11} "
            line += f"{value:<8} "
            line += f"{processes_str[key]}    "

            if value[-1] == "A":
                b_region = f"rate_{value[:-1]}B"
                c_region = f"rate_{value[:-1]}C"
                d_region = f"rate_{value[:-1]}D"
                line += f"(@0*@1/@2) {b_region},{c_region},{d_region}"
            else:
                line += f"{yields[key]}"

            lines.append(line)

    lines.append("")

    datacard_str = "\n".join(lines)

    outfile = Path(outfile)
    outfile.parent.mkdir(parents=True, exist_ok=True)
    outfile.write_text(datacard_str + "\n", encoding="utf-8")


def make_datacards_for_sig_dir(histdir, sig_dir, xcut, ycut):
    bkg_dir = bkg_dir_for_sig_dir(sig_dir)
    samples = discover_samples(
        histdir=histdir,
        sig_dir=sig_dir,
    )

    output_base = histdir / "datacards"
    datacard_year = datacard_year_for_sig_dir(sig_dir)
    outdir = output_base / datacard_year

    for sample_name in samples:
        outfile = outdir / f"{sample_name}.txt"
        make_datacard(
            histdir=histdir,
            sample_name=sample_name,
            xcut=xcut,
            ycut=ycut,
            outfile=outfile,
            noncl_sys=None,
            mode=MODE,
            sig_dir=sig_dir,
            bkg_dir=bkg_dir,
        )
        print(f"Wrote datacard to: {outfile}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Create Combine ABCD datacards from a plotter unique directory."
    )
    parser.add_argument(
        "--xcut",
        type=float,
        required=True,
        help="MET threshold, e.g. 700.",
    )
    parser.add_argument(
        "--ycut",
        type=float,
        required=True,
        help="ML score threshold, e.g. 0.9998.",
    )

    return parser.parse_args()


def main():
    args = parse_args()
    histdir = resolve_histdir(unique_dir=DEFAULT_UNIQUE_DIR, histdir=None)

    sig_dirs = discover_signal_dirs(histdir=histdir)
    for sig_dir in sig_dirs:
        make_datacards_for_sig_dir(histdir=histdir, sig_dir=sig_dir, xcut=args.xcut, ycut=args.ycut)


if __name__ == "__main__":
    main()
