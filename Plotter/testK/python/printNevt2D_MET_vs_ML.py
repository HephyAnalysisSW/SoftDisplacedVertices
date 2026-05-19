import argparse
import ctypes
from pathlib import Path

import ROOT
from uncertainties import nominal_value, ufloat


REGIONS = ("A", "B", "C", "D")

HISTOGRAMS = {
    "SP0_evt": "SP0_evt/MET_pt_corr_vs_SP0_Max_ML_score",
    "SP1_evt": "SP1_evt/MET_pt_corr_vs_SP1_Max_ML_score",
    "SP2_evt": "SP2_evt/MET_pt_corr_vs_SP2_Max_ML_score",
    "SP3_evt": "SP3_evt/MET_pt_corr_vs_SP3_Max_ML_score",
}

TABLE_ROWS = (
    ("SP0_evt", r"SP0 ($\ngoodtrack = 0$)"),
    ("SP1_evt", r"SP1 ($\ngoodtrack = 1$)"),
    ("SP2_evt", r"SP2 ($\ngoodtrack = 2$)"),
    ("SP3_evt", r"SP3 ($\ngoodtrack \geq 3$)"),
)

INPUT_FILES = (
    "data_2017/data_2017_hist.root",
    # "data18/met_2018_hist.root",
    # "data22_pre/met_2022_hist.root",
    # "data22_post/met_2022_hist.root",
    # "data23_pre/met_2023_hist.root",
    # "data23_post/met_2023_hist.root",
    # "data24/met_2024_hist.root",
    "bkg_2017/bkg_2017_hist.root",
    "sig_2017/stop_M1000_980_ct200_2018_hist.root",
)


def get_region_bins(hist, x_cut, y_cut):
    x_axis = hist.GetXaxis()
    y_axis = hist.GetYaxis()
    x_bin = x_axis.FindBin(x_cut)
    y_bin = y_axis.FindBin(y_cut)
    last_x_bin = x_axis.GetNbins() + 1
    last_y_bin = y_axis.GetNbins() + 1

    return {
        "A": (x_bin, last_x_bin, y_bin, last_y_bin), # hi MET hi ML
        "B": (1,      x_bin - 1, y_bin, last_y_bin), # lo MET hi ML

        "C": (x_bin, last_x_bin,     1,  y_bin - 1), # hi MET lo ML
        "D": (1,      x_bin - 1,     1,  y_bin - 1), # lo MET lo ML
    }


def get_events(filepath, histograms, x_cut, y_cut):
    root_file = ROOT.TFile.Open(str(filepath))
    if not root_file or root_file.IsZombie():
        raise OSError(f"Could not open ROOT file: {filepath}")

    try:
        events = {}
        for key, hist_name in histograms.items():
            hist = root_file.Get(hist_name)
            if not hist:
                raise ValueError(f"Histogram '{hist_name}' not found in {filepath}")

            events[key] = {}
            for region, bins in get_region_bins(hist, x_cut, y_cut).items():
                err = ctypes.c_double(0)
                count = hist.IntegralAndError(*bins, err)
                events[key][region] = ufloat(count, err.value)

        return events
    finally:
        root_file.Close()


def predict_a(counts):
    if nominal_value(counts["D"]) == 0:
        return None
    return counts["B"] * counts["C"] / counts["D"]


def format_count(count):
    if count is None:
        return r"$--$"
    return f"${count:.2fL}$"


def latex_escape(text):
    return str(text).replace("_", r"\_")


def caption_from_path(filepath):
    path = Path(filepath)
    return latex_escape(f"{path.parent.name}/{path.stem}")


def label_from_path(filepath):
    path = Path(filepath)
    return f"{path.parent.name}_{path.stem}"


def print_latex_table(filepath, events):
    print(r"\begin{table}[htbp!]")
    print(r"    \centering")
    print(r"    \begin{tabular}{l c c c c c}")
    print(r"    \hline")
    print(r"Search plane & A & A pred. & B & C & D \\")
    print(r"    \hline")

    for key, label in TABLE_ROWS:
        counts = events[key]
        values = [
            counts["A"],
            predict_a(counts),
            *(counts[region] for region in REGIONS[1:]),
        ]
        row_values = " & ".join(format_count(value) for value in values)
        print(f"{label} & {row_values} \\\\")

    print(r"    \hline")
    print(r"    \end{tabular}")
    print(fr"    \caption{{{caption_from_path(filepath)}}}")
    print(fr"    \label{{tab:evt_yield_{label_from_path(filepath)}}}")
    print(r"\end{table}")


def parse_args():
    parser = argparse.ArgumentParser(description="Print ABCD yields from 2D ROOT histograms.")
    parser.add_argument("--input_dir", required=True, help="Directory containing .root files")
    parser.add_argument(
        "--xBounds",
        "--x-cut",
        dest="x_cut",
        type=float,
        default=1.5,
        help="x cut value (default: 700)",
    )
    parser.add_argument(
        "--yBounds",
        "--y-cut",
        dest="y_cut",
        type=float,
        default=0.999,
        help="y cut value (default: 700)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    input_dir = Path(args.input_dir)

    for relative_path in INPUT_FILES:
        filepath = input_dir / relative_path
        events = get_events(filepath, HISTOGRAMS, args.x_cut, args.y_cut)
        print_latex_table(filepath, events)


if __name__ == "__main__":
    main()
