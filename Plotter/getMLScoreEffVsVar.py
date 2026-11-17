'''ML score efficiency of rotated D candidates in bins of a candidate property, data vs background MC.

Reads the 2D histograms <var>_vs_RotateVtx_MLScore_cat from the RotateK0 plotter output
(configs *_RotateK0_reweightLxy.yaml). The y axis is the score category
  0: score<0.8, 1: 0.8-0.99, 2: 0.99-0.999, 3: >=0.999,
so efficiency = N(category>=3) / N(category>=1) = N(score>=0.999) / N(score>=0.8),
the same definition as getMLScoreEff.py.

For each year, Run 2, Run 3 and the total, the script prints and plots per bin of <var>:
  - the fraction of all candidates (all score categories) in data and MC,
  - the data and MC efficiency and their ratio,
and, for the whole sample, the MC efficiency after reweighting MC to the data <var>
distribution in the same bins (weights from all score categories, kept fixed in the errors).

Example:
  python3 getMLScoreEffVsVar.py --input /scratch-cbe/.../Histos_ParTScoreD_RotateK0_trigSF_reweightLxy \\
      --output /groups/hephy/cms/ang.li/SDV/RotateD_trigSF_reweightLxy/effvsvar
'''
import os
import math
import bisect
import argparse
import ROOT
import matplotlib.pyplot as plt

from getMLScoreEff import YEARS, DATA_FILES, BKG_FILES, efficiency

ROOT.gROOT.SetBatch(True)

HIST_PATH = "All_RotateVtx_{sel}/RotateVtx_{var}_vs_RotateVtx_MLScore_cat"
N_CATEGORIES = 4
NUM_CATEGORY = 3  # score >= 0.999
DEN_CATEGORY = 1  # score >= 0.8

INF = float("inf")
# default bin edges; an infinite first (last) edge includes the underflow (overflow)
DEFAULT_EDGES = {
    "LxySig": [0, 5, 10, 20, 50, 100, INF],
    "Lxy": [0, 0.1, 0.3, 1, 3, 10, INF],
    "pt_before": [0, 1, 2, 3, 5, 10, 30, INF],
    "pAngle_before": [0, 0.05, 0.1, 0.2, 0.5, INF],
    "L_eta": [-INF, -2.5, -2, -1.5, -1, -0.5, 0, 0.5, 1, 1.5, 2, 2.5, INF],
}
AXIS_TITLES = {
    "LxySig": "vertex $L_{xy}$ significance",
    "Lxy": "vertex $L_{xy}$ (cm)",
    "pt_before": "vertex $p_T$ before rotation (GeV)",
    "pAngle_before": "pointing angle before rotation",
    "L_eta": r"vertex $\eta$",
}
GROUPS = {year: [year] for year in YEARS}
GROUPS["Run2"] = ["2017", "2018"]
GROUPS["Run3"] = ["2022pre", "2022post", "2023pre", "2023post", "2024"]
GROUPS["Total"] = list(YEARS)

parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument("--input", type=str, required=True,
                    help="input directory containing the *_hist.root files")
parser.add_argument("--output", type=str, required=True,
                    help="output directory for the plots and the text tables")
parser.add_argument("--var", type=str, nargs="+", default=list(DEFAULT_EDGES),
                    choices=list(DEFAULT_EDGES), help="candidate properties to bin in")
parser.add_argument("--sel", type=str, nargs="+", default=["tight", "all"],
                    help="RotateVtx selections")
parser.add_argument("--edges", type=float, nargs="+", default=None,
                    help="bin edges (only with a single --var); 'inf'/'-inf' include overflow/underflow")


class BinnedCounts:
    '''Sum of weights and sum of squared weights per (coarse bin, score category).'''

    def __init__(self, n_bins):
        self.sumw = [[0.] * N_CATEGORIES for _ in range(n_bins)]
        self.sumw2 = [[0.] * N_CATEGORIES for _ in range(n_bins)]

    def add(self, other):
        for k in range(len(self.sumw)):
            for c in range(N_CATEGORIES):
                self.sumw[k][c] += other.sumw[k][c]
                self.sumw2[k][c] += other.sumw2[k][c]

    def n_bins(self):
        return len(self.sumw)

    def total(self, k):
        return sum(self.sumw[k])

    def passing(self, k):
        '''(sumw, sumw2) of the efficiency numerator in bin k'''
        cats = range(NUM_CATEGORY, N_CATEGORIES)
        return sum(self.sumw[k][c] for c in cats), sum(self.sumw2[k][c] for c in cats)

    def complement(self, k):
        '''(sumw, sumw2) of denominator minus numerator in bin k (disjoint from the numerator)'''
        cats = range(DEN_CATEGORY, NUM_CATEGORY)
        return sum(self.sumw[k][c] for c in cats), sum(self.sumw2[k][c] for c in cats)


def coarse_bin_of(axis, fine_bin, edges):
    '''Index of the coarse bin that fine bin fine_bin of axis falls in, or None if outside the edges.'''
    if fine_bin == 0:
        return 0 if edges[0] == -INF else None
    if fine_bin == axis.GetNbins() + 1:
        return len(edges) - 2 if edges[-1] == INF else None
    k = bisect.bisect_right(edges, axis.GetBinCenter(fine_bin)) - 1
    return k if 0 <= k < len(edges) - 1 else None


def check_edges(axis, edges):
    '''Every finite edge inside the axis range must be a bin edge of the fine histogram.'''
    fine_edges = [axis.GetBinLowEdge(b) for b in range(1, axis.GetNbins() + 2)]
    tolerance = 1e-6 * (axis.GetXmax() - axis.GetXmin()) / axis.GetNbins()
    for edge in edges:
        if axis.GetXmin() < edge < axis.GetXmax():
            assert min(abs(fe - edge) for fe in fine_edges) < tolerance, \
                "edge {} is not a bin edge of the input histogram".format(edge)


def read_counts(fpath, hist_path, edges):
    f = ROOT.TFile.Open(fpath)
    if not f or f.IsZombie():
        raise RuntimeError("cannot open {}".format(fpath))
    h = f.Get(hist_path)
    if not h:
        raise RuntimeError("histogram {} not found in {}".format(hist_path, fpath))
    xaxis = h.GetXaxis()
    check_edges(xaxis, edges)
    assert h.GetNbinsY() == N_CATEGORIES, "expected {} score categories".format(N_CATEGORIES)
    counts = BinnedCounts(len(edges) - 1)
    for bx in range(0, xaxis.GetNbins() + 2):
        k = coarse_bin_of(xaxis, bx, edges)
        if k is None:
            continue
        for c in range(N_CATEGORIES):
            counts.sumw[k][c] += h.GetBinContent(bx, c + 1)
            counts.sumw2[k][c] += h.GetBinError(bx, c + 1) ** 2
    f.Close()
    return counts


def read_group(indir, files_by_year, years, hist_path, edges):
    counts = BinnedCounts(len(edges) - 1)
    for year in years:
        counts.add(read_counts(os.path.join(indir, files_by_year[year]), hist_path, edges))
    return counts


def bin_efficiency(counts, k):
    n_pass, var_pass = counts.passing(k)
    n_comp, var_comp = counts.complement(k)
    if n_pass + n_comp <= 0:
        return float("nan"), float("nan")
    return efficiency(n_pass, var_pass, n_pass + n_comp, var_pass + var_comp)


def weighted_efficiency(counts, weights):
    '''Efficiency over all bins with bin k weighted by weights[k] (weights treated as exact).'''
    n_pass = sum(w * counts.passing(k)[0] for k, w in enumerate(weights))
    var_pass = sum(w ** 2 * counts.passing(k)[1] for k, w in enumerate(weights))
    n_comp = sum(w * counts.complement(k)[0] for k, w in enumerate(weights))
    var_comp = sum(w ** 2 * counts.complement(k)[1] for k, w in enumerate(weights))
    return efficiency(n_pass, var_pass, n_pass + n_comp, var_pass + var_comp)


def ratio(num, den):
    (a, ea), (b, eb) = num, den
    if not b > 0:
        return float("nan"), float("nan")
    return a / b, math.sqrt((ea / b) ** 2 + (a * eb / b ** 2) ** 2)


def fractions(counts):
    total = sum(counts.total(k) for k in range(counts.n_bins()))
    return [counts.total(k) / total for k in range(counts.n_bins())]


def bin_label(lo, hi):
    if lo == -INF:
        return "<{:g}".format(hi)
    if hi == INF:
        return ">={:g}".format(lo)
    return "[{:g},{:g})".format(lo, hi)


def summarise(group, data, mc, edges, var):
    '''Per-bin and total numbers for one group; returns (table lines, per-bin results for plotting).'''
    labels = [bin_label(lo, hi) for lo, hi in zip(edges[:-1], edges[1:])]
    frac_data, frac_mc = fractions(data), fractions(mc)
    per_bin = []
    lines = ["=== {}".format(group),
             "  {:>14s} {:>9s} {:>9s} {:>17s} {:>17s} {:>15s}".format(
                 var, "frac data", "frac MC", "eff data", "eff MC", "data/MC")]
    for k, label in enumerate(labels):
        eff_data, eff_mc = bin_efficiency(data, k), bin_efficiency(mc, k)
        data_over_mc = ratio(eff_data, eff_mc)
        per_bin.append((label, eff_data, eff_mc, data_over_mc))
        lines.append("  {:>14s} {:9.3f} {:9.3f} {:8.4f} +- {:6.4f} {:8.4f} +- {:6.4f} {:6.3f} +- {:5.3f}".format(
            label, frac_data[k], frac_mc[k], *eff_data, *eff_mc, *data_over_mc))
    no_weights = [1.] * data.n_bins()
    eff_data, eff_mc = weighted_efficiency(data, no_weights), weighted_efficiency(mc, no_weights)
    # MC reweighted bin by bin to the data distribution of var; bins without MC keep weight 1
    shape_weights = [fd / fm if fm > 0 else 1. for fd, fm in zip(frac_data, frac_mc)]
    eff_mc_reweighted = weighted_efficiency(mc, shape_weights)
    lines.append("  {:>14s} {:>19s} {:8.4f} +- {:6.4f} {:8.4f} +- {:6.4f} {:6.3f} +- {:5.3f}".format(
        "all bins", "", *eff_data, *eff_mc, *ratio(eff_data, eff_mc)))
    lines.append("  {:>14s} {:>19s} {:>17s} {:8.4f} +- {:6.4f} {:6.3f} +- {:5.3f}".format(
        "MC rw in " + var, "", "", *eff_mc_reweighted, *ratio(eff_data, eff_mc_reweighted)))
    return lines, per_bin


def plot(per_bin, var, sel, group, output):
    labels = [p[0] for p in per_bin]
    x = list(range(len(labels)))
    offset = 0.08
    fig, (ax, ax_ratio) = plt.subplots(2, 1, figsize=(8, 6), sharex=True,
                                       gridspec_kw={"height_ratios": [3, 1]})
    for index, fmt, color, label in ((1, "o", "#0b0b0b", "Data"), (2, "s", "#2a78d6", "Background MC")):
        shift = -offset if index == 1 else offset
        ax.errorbar([xi + shift for xi in x], [p[index][0] for p in per_bin], yerr=[p[index][1] for p in per_bin],
                    fmt=fmt, color=color, markersize=5, capsize=3, linewidth=1.2, label=label)
    ax_ratio.errorbar(x, [p[3][0] for p in per_bin], yerr=[p[3][1] for p in per_bin],
                      fmt="o", color="#0b0b0b", markersize=4, capsize=3, linewidth=1.2)
    ax_ratio.axhline(1., color="#888888", linewidth=0.8, linestyle="--")
    ax.set_ylabel("N(score>=0.999) / N(score>=0.8)")
    ax.set_title("{}, RotateVtx {}".format(group, sel))
    ax.legend(frameon=False)
    ax_ratio.set_ylabel("Data / MC")
    ax_ratio.set_xticks(x)
    ax_ratio.set_xticklabels(labels, rotation=30, ha="right")
    ax_ratio.set_xlabel(AXIS_TITLES[var])
    for a in (ax, ax_ratio):
        a.grid(axis="y", color="#e1e0d9", linewidth=0.8)
        a.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(os.path.join(output, "effvs_{}_{}_{}.png".format(var, sel, group)), dpi=130)
    plt.close(fig)


def main():
    args = parser.parse_args()
    if args.edges is not None:
        assert len(args.var) == 1, "--edges can only be used with a single --var"
        assert all(lo < hi for lo, hi in zip(args.edges[:-1], args.edges[1:])), "--edges must be increasing"
    os.makedirs(args.output, exist_ok=True)

    for var in args.var:
        edges = args.edges if args.edges is not None else DEFAULT_EDGES[var]
        for sel in args.sel:
            hist_path = HIST_PATH.format(sel=sel, var=var)
            lines = ["Efficiency N(score>=0.999)/N(score>=0.8) in bins of {}, from {}".format(var, hist_path),
                     "frac = fraction of all candidates (all scores); 'MC rw in {}' = MC reweighted to the data "
                     "{} distribution in these bins".format(var, var)]
            for group, years in GROUPS.items():
                data = read_group(args.input, DATA_FILES, years, hist_path, edges)
                mc = read_group(args.input, BKG_FILES, years, hist_path, edges)
                group_lines, per_bin = summarise(group, data, mc, edges, var)
                lines += group_lines
                plot(per_bin, var, sel, group, args.output)
            text = "\n".join(lines)
            print(text + "\n")
            with open(os.path.join(args.output, "effvs_{}_{}.txt".format(var, sel)), "w") as f:
                f.write(text + "\n")


if __name__ == "__main__":
    main()
