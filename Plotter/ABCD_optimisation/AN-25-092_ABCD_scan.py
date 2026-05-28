#!/usr/bin/env python3

from ctypes import c_double
from pathlib import Path
from types import SimpleNamespace
import importlib.util
import math
import os
import sys

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-sdv")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd
import ROOT
from uncertainties import ufloat


YEAR = "2018"
PLANES = ("GT1", "GT2", "GT3")
YIELD_SCALE = 4.59637
ORIGIN_BR = 1.0

X_LO = 250.0
Y_LO = 0.80
X_EDGES = np.arange(300.0, 701.0, 50.0)
Y_EDGES = np.round(np.arange(0.9900, 0.9999, 0.0002), 5)

PLOTTER = Path("/users/alikaan.gueven/AOD_to_nanoAOD/Plotter_run3/CMSSW_15_0_5/src/SoftDisplacedVertices/Plotter")
LIMITCALC_OOP = PLOTTER / "limitcalc" / "limitcalc_oop"

BKG_ROOT = Path(
    "/scratch-cbe/users/alikaan.gueven/AN_plots/ParT_hists/"
    "AN-25-092_ML_plots_limitcalc_merge_w_Ang_v3_centralprod/"
    "bkg_2018/bkg_2018_hist.root"
)
SIG_DIR = Path(
    "/scratch-cbe/users/alikaan.gueven/AN_plots/ParT_hists/"
    "AN-25-092_ML_plots_limitcalc_privateprod_260527/sig_2018"
)
PLOT_OUTDIR = PLOTTER / "ABCD_optimisation" / "plots"

samples = [
    "C1N2ML_M500_485_ct200_2018_hist0",
    "C1N2ML_M500_485_ct20_2018_hist0",
    "C1N2ML_M500_485_ct20_2018_hist0",
]


sys.path.insert(0, str(LIMITCALC_OOP))
spec = importlib.util.spec_from_file_location(
    "reweighted_pkl_datacards",
    LIMITCALC_OOP / "AN-25-092_make_reweighted_pkl_datacards.py",
)
reweighted = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reweighted)

SignalReweighter = reweighted.SignalReweighter
import utils


ROOT.gROOT.SetBatch(True)
plt.rcParams.update({"figure.dpi": 120, "savefig.dpi": 150})


def safe_z(value):
    return value if math.isfinite(value) else 0.0


def heatmap(ax, df, title, cbar_label, cmap, vmin=None, vmax=None):
    x = df.index.to_numpy(dtype=float)
    y = df.columns.to_numpy(dtype=float)

    dx = np.diff(x)
    dy = np.diff(y)
    x_edges = np.r_[x[0] - dx[0] / 2, x[:-1] + dx / 2, x[-1] + dx[-1] / 2]
    y_edges = np.r_[y[0] - dy[0] / 2, y[:-1] + dy / 2, y[-1] + dy[-1] / 2]

    pcm = ax.pcolormesh(
        x_edges,
        y_edges,
        np.ma.masked_invalid(df.T.to_numpy(dtype=float)),
        cmap=cmap,
        vmin=vmin,
        vmax=vmax,
        shading="flat",
    )

    x_ticks = x[np.unique(np.round(np.linspace(0, len(x) - 1, 6)).astype(int))]
    y_ticks = y[np.unique(np.round(np.linspace(0, len(y) - 1, 6)).astype(int))]

    ax.set_xticks(x_ticks)
    ax.set_yticks(y_ticks)
    ax.set_xticklabels([f"{v:g}" for v in x_ticks], rotation=45, ha="right")
    ax.yaxis.set_major_formatter(mtick.FormatStrFormatter("%.5f"))
    ax.set_xlabel("MET cut")
    ax.set_ylabel("ML cut")
    ax.set_title(title)

    cbar = ax.figure.colorbar(pcm, ax=ax, shrink=0.85)
    cbar.ax.set_ylabel(cbar_label)


def build_tables(hist, plane, reweighter=None, target_br=None, target_ctau=None):
    table_names = [
        "bkg_NA", "bkg_NB", "bkg_NC", "bkg_ND",
        "bkg_NA_unc", "bkg_NB_unc", "bkg_NC_unc", "bkg_ND_unc",
        "sig_NA", "sig_NB", "sig_NC", "sig_ND",
        "sig_NA_unc", "sig_NB_unc", "sig_NC_unc", "sig_ND_unc",
        "A_pred", "A_pred_unc", "delta_A", "delta_A_unc", "Z_A_pred",
    ]
    empty = pd.DataFrame(index=np.round(X_EDGES, 8), columns=np.round(Y_EDGES, 8), dtype=float)
    tables = {name: empty.copy() for name in table_names}

    for x_cut in X_EDGES:
        for y_cut in Y_EDGES:
            x_lo = hist.GetXaxis().FindBin(X_LO)
            x_hi = hist.GetNbinsX() + 1
            x_mid = hist.GetXaxis().FindBin(x_cut)

            y_lo = hist.GetYaxis().FindBin(Y_LO)
            y_hi = hist.GetNbinsY() + 1
            y_mid = hist.GetYaxis().FindBin(y_cut)

            err = c_double(0.0)
            bkg = {
                "A": ufloat(hist.IntegralAndError(x_mid, x_hi, y_mid, y_hi, err), err.value) * YIELD_SCALE,
                "B": ufloat(hist.IntegralAndError(x_lo, x_mid - 1, y_mid, y_hi, err), err.value) * YIELD_SCALE,
                "C": ufloat(hist.IntegralAndError(x_mid, x_hi, y_lo, y_mid - 1, err), err.value) * YIELD_SCALE,
                "D": ufloat(hist.IntegralAndError(x_lo, x_mid - 1, y_lo, y_mid - 1, err), err.value) * YIELD_SCALE,
            }

            for region, value in bkg.items():
                tables[f"bkg_N{region}"].loc[x_cut, y_cut] = value.n
                tables[f"bkg_N{region}_unc"].loc[x_cut, y_cut] = 1.0 if value.n == 0 else value.s

            a_pred = (bkg["B"] * bkg["C"]) / bkg["D"] if bkg["D"].n > 0 else ufloat(float("nan"), float("nan"))

            bkg_delta = {
                region: ufloat(0.0, 1.0) if value.n < 0 else ufloat(value.n, 1.0 if value.n == 0 else value.s)
                for region, value in bkg.items()
            }
            a_pred_delta = (
                (bkg_delta["B"] * bkg_delta["C"]) / bkg_delta["D"]
                if bkg_delta["D"].n > 0 else ufloat(float("nan"), float("nan"))
            )
            delta_a = (
                bkg_delta["A"] - a_pred_delta
                if bkg_delta["D"].n > 0 else ufloat(float("nan"), float("nan"))
            )

            tables["A_pred"].loc[x_cut, y_cut] = a_pred.n
            tables["A_pred_unc"].loc[x_cut, y_cut] = a_pred.s
            tables["delta_A"].loc[x_cut, y_cut] = delta_a.n
            tables["delta_A_unc"].loc[x_cut, y_cut] = delta_a.s

            if reweighter is None:
                continue

            options = SimpleNamespace(xcut=x_cut, xlo=X_LO, ycut=y_cut, ylo=Y_LO)
            sig_values, sig_errors = reweighter.region_sums(plane, options, target_br, target_ctau)
            sig = {region: ufloat(sig_values[region], sig_errors[region]) * YIELD_SCALE for region in "ABCD"}

            for region, value in sig.items():
                tables[f"sig_N{region}"].loc[x_cut, y_cut] = value.n
                tables[f"sig_N{region}_unc"].loc[x_cut, y_cut] = 1.0 if value.n == 0 else value.s

            eps = 0.5
            bkg_n = max(eps, a_pred.n) if np.isfinite(a_pred.n) else eps
            bkg_s = max(eps, a_pred.s) if np.isfinite(a_pred.s) else eps
            unc = math.sqrt((0.10 * bkg_n) ** 2 + bkg_s ** 2)
            tables["Z_A_pred"].loc[x_cut, y_cut] = safe_z(
                ROOT.RooStats.AsimovSignificance(sig["A"].n, bkg_n, unc)
            )

    return tables


def plot_closure(closure_tables):
    variants = {
        "closure": ("", lambda table: -table["delta_A"] / table["bkg_NA"]),
        "closure_plus1sigma": (" +1$\\sigma$", lambda table: -(table["delta_A"] + table["delta_A_unc"]) / table["bkg_NA"]),
        "closure_minus1sigma": (" -1$\\sigma$", lambda table: -(table["delta_A"] - table["delta_A_unc"]) / table["bkg_NA"]),
    }

    for tag, (label, expr) in variants.items():
        fig, axes = plt.subplots(3, 1, figsize=(5, 12), constrained_layout=True)

        for ax, plane in zip(axes, PLANES):
            heatmap(
                ax,
                expr(closure_tables[plane]),
                title=f"{plane} closure{label}",
                cbar_label=r"$(A_{pred} - A) / A$",
                cmap="RdBu",
                vmin=-1.0,
                vmax=1.0,
            )

        fig.savefig(PLOT_OUTDIR / f"multiplane_{tag}.pdf")
        plt.close(fig)


def plot_significance(sample_name, bkg_file):
    pkl_path = SIG_DIR / f"{sample_name}.pkl"
    if not pkl_path.exists():
        raise FileNotFoundError(pkl_path)

    sample_info = utils.parse_signal_name(reweighted.source_sample_name(pkl_path))
    origin_ctau = sample_info.ct

    if sample_info.model == "stop":
        target_ctau = utils.get_stop_ctau_for_br(sample_info.M, sample_info.dM, ORIGIN_BR)
        target_br = ORIGIN_BR
    elif sample_info.model == "C1N2":
        target_ctau = origin_ctau
        target_br = None
    else:
        raise ValueError(f"Unsupported signal model: {sample_info.model}")

    reweighter = SignalReweighter(pkl_path, origin_ctau, origin_br=ORIGIN_BR)
    significance_tables = {}

    for plane in PLANES:
        hist = bkg_file.Get(f"{plane}_evt/MET_pt_corr_vs_leadingvtx_MLscore")
        if not hist:
            raise KeyError(f"Missing background histogram for {plane}")
        significance_tables[plane] = build_tables(hist, plane, reweighter, target_br, target_ctau)

    combined_z = np.sqrt(sum(significance_tables[plane]["Z_A_pred"].pow(2) for plane in PLANES))
    vmax = np.nanmax(combined_z.to_numpy(dtype=float))

    fig, ax = plt.subplots(figsize=(7.5, 5.5), constrained_layout=True)
    heatmap(
        ax,
        combined_z,
        title=(
            f"model: {sample_info.model}, $M$={sample_info.M} GeV, "
            f"$\\Delta M$={sample_info.dM} GeV, $c\\tau$={target_ctau:g} mm"
        ),
        cbar_label=r"Combined Asimov significance",
        cmap="Blues_r",
        vmin=0.0,
        vmax=vmax,
    )

    fig.savefig(PLOT_OUTDIR / f"{sample_name}_significance.pdf")
    plt.close(fig)

    best_met, best_ml = combined_z.stack().idxmax()
    print(f"{sample_name}: best Z={combined_z.loc[best_met, best_ml]:.3f}, MET={best_met:g}, ML={best_ml:.5f}")


def main():
    PLOT_OUTDIR.mkdir(parents=True, exist_ok=True)

    bkg_file = ROOT.TFile.Open(str(BKG_ROOT))
    if not bkg_file or bkg_file.IsZombie():
        raise FileNotFoundError(BKG_ROOT)

    try:
        closure_tables = {}
        for plane in PLANES:
            hist = bkg_file.Get(f"{plane}_evt/MET_pt_corr_vs_leadingvtx_MLscore")
            if not hist:
                raise KeyError(f"Missing background histogram for {plane}")
            closure_tables[plane] = build_tables(hist, plane)

        plot_closure(closure_tables)

        for sample_name in samples:
            plot_significance(sample_name, bkg_file)

    finally:
        bkg_file.Close()


if __name__ == "__main__":
    main()
