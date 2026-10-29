import os
import math
import ctypes
import argparse
import ROOT
import matplotlib.pyplot as plt

ROOT.gROOT.SetBatch(True)

HIST_PATH = "All_RotateVtx_tight/RotateVtx_MLScore"
NUM_CUT = 0.999
DEN_CUT = 0.8

# canonical per-era files (avoid double-counting the per-run/sub-era pieces
# that get hadd'ed into these, see haddfiles_run3.sh / haddfiles.sh)
# ordered so that data/background pairs line up under the same year label
YEARS = ["2017", "2018", "2022pre", "2022post", "2023pre", "2023post"]

DATA_FILES = {
    "2017": "met2017_hist.root",
    "2018": "met2018_hist.root",
    "2022pre": "jetmet_2022pre_hist.root",
    "2022post": "jetmet_2022post_hist.root",
    "2023pre": "jetmet_2023pre_hist.root",
    "2023post": "jetmet_2023post_hist.root",
}

BKG_FILES = {
    "2017": "background_2017_hist.root",
    "2018": "background_2018_hist.root",
    "2022pre": "background_2022pre_hist.root",
    "2022post": "background_2022post_hist.root",
    "2023pre": "background_2023pre_hist.root",
    "2023post": "background_2023post_hist.root",
}

parser = argparse.ArgumentParser(
    description="Selection efficiency of the ML score cut (>{}) relative to "
                "the baseline cut (>{}), read from {}".format(
                    NUM_CUT, DEN_CUT, HIST_PATH))
parser.add_argument("--input", type=str,
                     help="input directory containing the *_hist.root files")
parser.add_argument("--hist", type=str, default=HIST_PATH,
                     help="histogram path inside each file")
parser.add_argument("--num-cut", type=float, default=NUM_CUT,
                     help="lower edge of the numerator MLScore selection")
parser.add_argument("--den-cut", type=float, default=DEN_CUT,
                     help="lower edge of the denominator MLScore selection")
parser.add_argument("--output", type=str, default="mlscore_efficiency_by_year.png",
                     help="output path for the data-vs-MC efficiency plot")


def get_counts(fpath, hist_path, num_cut, den_cut):
    f = ROOT.TFile.Open(fpath)
    if not f or f.IsZombie():
        raise RuntimeError("cannot open {}".format(fpath))
    h = f.Get(hist_path)
    if not h:
        raise RuntimeError("histogram {} not found in {}".format(hist_path, fpath))
    h.SetDirectory(0)
    f.Close()

    nbins = h.GetNbinsX()
    err_num = ctypes.c_double(0)
    err_den = ctypes.c_double(0)
    n_num = h.IntegralAndError(h.FindBin(num_cut), nbins + 1, err_num)
    n_den = h.IntegralAndError(h.FindBin(den_cut), nbins + 1, err_den)
    return n_num, err_num.value, n_den, err_den.value


def efficiency(n_num, var_num, n_den, var_den):
    # n_num counts are a strict subset of n_den counts (MLScore>num_cut is
    # nested inside MLScore>den_cut), so the two integrals are correlated.
    # Split into the two disjoint pieces - "pass" (>num_cut) and "complement"
    # ([den_cut, num_cut)) - which *are* independent, and propagate from those.
    if n_den <= 0:
        return 0.0, 0.0
    n_comp = n_den - n_num
    var_comp = max(var_den - var_num, 0.0)
    eff = n_num / n_den
    var_eff = (n_comp ** 2 * var_num + n_num ** 2 * var_comp) / n_den ** 4
    return eff, math.sqrt(var_eff)


def process(label, files_by_year, indir, hist_path, num_cut, den_cut):
    """Compute the efficiency for each year and return {year: (eff, err)}."""
    print("\n=== {} ===".format(label))
    results = {}
    tot_num, tot_den = 0.0, 0.0
    tot_var_num, tot_var_den = 0.0, 0.0
    for year in YEARS:
        fpath = os.path.join(indir, files_by_year[year])
        if not os.path.exists(fpath):
            print("  [skip] {} not found".format(files_by_year[year]))
            continue
        n_num, e_num, n_den, e_den = get_counts(fpath, hist_path, num_cut, den_cut)
        eff, e_eff = efficiency(n_num, e_num ** 2, n_den, e_den ** 2)
        print("  {:10s} N(pass)={:12.2f}  N(base)={:12.2f}  eff={:.4f} +/- {:.4f}"
              .format(year, n_num, n_den, eff, e_eff))
        results[year] = (eff, e_eff)
        tot_num += n_num
        tot_den += n_den
        tot_var_num += e_num ** 2
        tot_var_den += e_den ** 2

    eff, e_eff = efficiency(tot_num, tot_var_num, tot_den, tot_var_den)
    print("  {:10s} N(pass)={:12.2f}  N(base)={:12.2f}  eff={:.4f} +/- {:.4f}"
          .format("TOTAL", tot_num, tot_den, eff, e_eff))
    return results


def plot_efficiency_by_year(data_results, bkg_results, num_cut, den_cut, output):
    years = [y for y in YEARS if y in data_results and y in bkg_results]
    x = list(range(len(years)))
    data_eff = [data_results[y][0] for y in years]
    data_err = [data_results[y][1] for y in years]
    bkg_eff = [bkg_results[y][0] for y in years]
    bkg_err = [bkg_results[y][1] for y in years]

    fig, ax = plt.subplots(figsize=(7, 5))
    offset = 0.06
    ax.errorbar([xi - offset for xi in x], data_eff, yerr=data_err,
                fmt="o", color="#0b0b0b", markersize=6, capsize=3,
                linewidth=1.4, label="Data")
    ax.errorbar([xi + offset for xi in x], bkg_eff, yerr=bkg_err,
                fmt="s", color="#2a78d6", markersize=6, capsize=3,
                linewidth=1.4, label="Background MC")

    ax.set_xticks(x)
    ax.set_xticklabels(years)
    ax.set_xlim(-0.5, len(years) - 0.5)
    ax.set_xlabel("Year")
    ax.set_ylabel("Efficiency  N(MLScore>{}) / N(MLScore>{})".format(num_cut, den_cut))
    ax.grid(axis="y", color="#e1e0d9", linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    print("\nSaved plot to {}".format(output))


if __name__ == "__main__":
    args = parser.parse_args()

    print("Efficiency = N(MLScore>{}) / N(MLScore>{})  from  {}"
          .format(args.num_cut, args.den_cut, args.hist))

    data_results = process("Data", DATA_FILES, args.input, args.hist, args.num_cut, args.den_cut)
    bkg_results = process("Background MC", BKG_FILES, args.input, args.hist, args.num_cut, args.den_cut)

    print("\n=== (Data - MC) / MC ===")
    for year in YEARS:
        if year not in data_results or year not in bkg_results:
            continue
        d, e_d = data_results[year]
        m, e_m = bkg_results[year]
        if m <= 0:
            print("  {:10s} MC efficiency is zero, skipping".format(year))
            continue
        r = (d - m) / m
        # dr/dd = 1/m, dr/dm = -d/m^2; data and MC are independent
        e_r = math.sqrt((e_d / m) ** 2 + (d * e_m / m ** 2) ** 2)
        print("  {:10s} data={:.4f}+/-{:.4f}  MC={:.4f}+/-{:.4f}  (data-MC)/MC={:+.4f} +/- {:.4f}"
              .format(year, d, e_d, m, e_m, r, e_r))

    plot_efficiency_by_year(data_results, bkg_results, args.num_cut, args.den_cut, args.output)
