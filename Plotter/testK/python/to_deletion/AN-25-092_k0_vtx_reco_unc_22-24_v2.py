#!/usr/bin/env python3

"""
Compute the K0S based vertex reconstruction uncertainty.

The input is a 2D histogram with x = m(pi pi) and y = Lxy. The Lxy axis is
rebinned to the explicit analysis binning before extracting the yield. In each
rebinned Lxy interval, the script projects the mass distribution, fits the two
K0S sidebands with a first-order polynomial, sums the fitted background in the
K0S signal-window bins, and subtracts it from the observed signal-window yield.

The MC yield is normalised to data in the low displacement region Lxy < 1 cm.
After this normalisation, the script computes the data/MC ratio versus Lxy, the
largest post-normalisation deviation from unity, and the 68% quantile of those
deviations for Lxy >= 1 cm.

Outputs are produced separately for 2017, 2018, and Run 2: a CSV table, a ROOT
file with the input and derived histograms, a data_v_background simulation plot
with a ratio panel, and a text summary.
"""

import csv
import math
import os
from array import array

import ROOT


ROOT.gROOT.SetBatch(True)
ROOT.TH1.SetDefaultSumw2(True)
ROOT.gStyle.SetOptStat(0)
ROOT.gStyle.SetOptTitle(0)
# ROOT.TGaxis.SetExponentOffset(-0.10, 0.00, "Y")
mc_stat_colour = ROOT.TColor.GetColor(254, 208, 26)

# Inputs from the K0 control-sample histogram production.
uniquedir = "AN-25-092_ML_plots_K0_v3"
base = f"/scratch-cbe/users/alikaan.gueven/AN_plots/ParT_hists/{uniquedir}"
hist_name = "all_vtx_k0_sel_v2/SDVSecVtx_refitMass_vs_SDVSecVtx_Lxy"

samples = {
    "2022_pre": {
        "data_file": f"{base}/data22_pre/jetmet_2022_pre_hist.root",
        "mc_file": f"{base}/bkg22_pre/all_2022pre_hist.root",
        "outdir": f"{base}/plots/k0_vtx_reco_unc_2022_pre_v2",
        "lumi_label": "8.0 fb^{-1} (13.6 TeV)",
    },
    "2022_post": {
        "data_file": f"{base}/data22_post/jetmet_2022_post_hist.root",
        "mc_file": f"{base}/bkg22_post/all_2022post_hist.root",
        "outdir": f"{base}/plots/k0_vtx_reco_unc_2022_post_v2",
        "lumi_label": "26.7 fb^{-1} (13.6 TeV)",
    },
    "2023_pre": {
        "data_file": f"{base}/data23_pre/jetmet_2023_pre_hist.root",
        "mc_file": f"{base}/bkg23_pre/all_2023pre_hist.root",
        "outdir": f"{base}/plots/k0_vtx_reco_unc_2023_pre_v2",
        "lumi_label": "18.0 fb^{-1} (13.6 TeV)",
    },
    "2023_post": {
        "data_file": f"{base}/data23_post/jetmet_2023_post_hist.root",
        "mc_file": f"{base}/bkg23_post/all_2023post_hist.root",
        "outdir": f"{base}/plots/k0_vtx_reco_unc_2023_post_v2",
        "lumi_label": "9.7 fb^{-1} (13.6 TeV)",
    },
}

# K0 mass window, sidebands, and low-Lxy MC normalisation region.
signal = (0.470, 0.530)
sidebands = ((0.440, 0.470), (0.530, 0.560))
norm_lxy_max = 1.0
mass_rebin = 16
lxy_bin_edges = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.5, 9.0, 11.0, 13.0, 15.0, 17.0, 19.0, 22.0, 27.0, 32.0, 40.0]


def load_hist(path, name):
    # Clone and detach the histogram so it survives after the ROOT file is closed.
    f = ROOT.TFile.Open(path)
    h = f.Get(hist_name).Clone(name)
    h.SetDirectory(0)
    f.Close()
    return h


def bins(axis, low, high):
    return [i for i in range(1, axis.GetNbins() + 1) if low <= axis.GetBinCenter(i) < high]


def lxy_bin_groups(axis):
    groups = []
    for low, high in zip(lxy_bin_edges[:-1], lxy_bin_edges[1:]):
        selected_bins = bins(axis, low, high)
        if not selected_bins:
            raise RuntimeError(f"No source Lxy bins found for interval {low:g} to {high:g} cm")
        groups.append((selected_bins[0], selected_bins[-1], low, high))
    return groups


def make_lxy_hist(name, bin_edges, values, errors, title):
    h = ROOT.TH1D(name, title, len(bin_edges) - 1, array("d", bin_edges))
    h.SetDirectory(0)
    for i, (value, error) in enumerate(zip(values, errors), 1):
        h.SetBinContent(i, value)
        h.SetBinError(i, error)
    return h


def plot_data_mc(hdata, hmc, outdir, lumi_label, sample_name):
    x_min = hdata.GetXaxis().GetXmin()
    x_max = hdata.GetXaxis().GetXmax()
    y_min = 0.5 * min(hdata.GetMinimum(), hmc.GetMinimum())
    y_max = 5.0 * max(hdata.GetMaximum(), hmc.GetMaximum())
    canv = ROOT.TCanvas(f"k0_vtx_reco_unc_{sample_name}", "", 800, 800)
    pad1 = ROOT.TPad("pad1", "", 0.0, 0.30, 1.0, 1.0)
    pad2 = ROOT.TPad("pad2", "", 0.0, 0.00, 1.0, 0.30)
    pad1.SetBottomMargin(0.02)
    pad1.SetLeftMargin(0.13)
    pad1.SetRightMargin(0.04)
    pad1.SetTopMargin(0.10)
    pad2.SetTopMargin(0.04)
    pad2.SetBottomMargin(0.32)
    pad2.SetLeftMargin(0.13)
    pad2.SetRightMargin(0.04)
    pad1.Draw()
    pad2.Draw()

    pad1.cd()
    pad1.SetLogy()
    hmc.SetFillColor(ROOT.kBlue - 9)
    hmc.SetLineColor(ROOT.kBlue + 1)
    hmc.SetLineWidth(1)
    hmc.SetMarkerSize(0)
    hmc.SetMinimum(y_min)
    hmc.SetMaximum(y_max)
    hmc.GetXaxis().SetLabelSize(0)
    hmc.GetYaxis().SetTitle("Background-subtracted K^{0}_{S} yield")
    hmc.GetYaxis().SetTitleSize(0.055)
    hmc.GetYaxis().SetTitleOffset(1.15)
    hmc.GetYaxis().SetLabelSize(0.045)
    hmc.Draw("hist")

    hmc_err = hmc.Clone("k0_yield_mc_norm_err")
    hmc_err.SetFillColor(mc_stat_colour)
    hmc_err.SetFillStyle(1001)
    hmc_err.SetMarkerSize(0)
    hmc_err.SetLineColor(mc_stat_colour)
    hmc_err.Draw("E2 same")

    hmc_outline = hmc.Clone("k0_yield_mc_norm_outline")
    hmc_outline.SetFillStyle(0)
    hmc_outline.SetMarkerSize(0)
    hmc_outline.Draw("hist same")

    hdata.SetMarkerStyle(20)
    hdata.SetMarkerSize(0.8)
    hdata.SetMarkerColor(ROOT.kBlack)
    hdata.SetLineColor(ROOT.kBlack)
    hdata.Draw("E1X0 same")

    leg_data = ROOT.TLegend(0.22, 0.80, 0.42, 0.88)
    leg_data.SetBorderSize(0)
    leg_data.SetFillStyle(0)
    leg_data.SetTextFont(42)
    leg_data.SetTextSize(0.035)
    leg_data.AddEntry(hdata, "Data", "pe")
    leg_data.Draw()

    leg_mc = ROOT.TLegend(0.52, 0.75, 0.88, 0.88)
    leg_mc.SetBorderSize(0)
    leg_mc.SetFillStyle(0)
    leg_mc.SetTextFont(42)
    leg_mc.SetTextSize(0.035)
    leg_mc.AddEntry(hmc, "Background simulation", "f")
    leg_mc.AddEntry(hmc_err, "MC statistical uncertainty", "f")
    leg_mc.Draw()

    cms = ROOT.TLatex()
    cms.SetNDC(True)
    cms.SetTextFont(61)
    cms.SetTextSize(0.065)
    cms.DrawLatex(0.13, 0.92, "CMS")
    cms.SetTextFont(52)
    cms.SetTextSize(0.048)
    cms.DrawLatex(0.235, 0.92, "Preliminary")
    cms.SetTextFont(42)
    cms.SetTextAlign(31)
    cms.DrawLatex(0.96, 0.92, lumi_label)
    cms.SetTextAlign(11)

    pad2.cd()
    ratio = hdata.Clone("ratio_data_over_mc")
    ratio.Divide(hmc)
    ratio.SetMinimum(0.6)
    ratio.SetMaximum(1.4)
    ratio.GetYaxis().SetTitle("Data/MC")
    ratio.GetYaxis().SetTitleSize(0.12)
    ratio.GetYaxis().SetTitleOffset(0.48)
    ratio.GetYaxis().SetLabelSize(0.10)
    ratio.GetYaxis().SetNdivisions(505)
    ratio.GetXaxis().SetTitle("L_{xy} (cm)")
    ratio.GetXaxis().SetTitleSize(0.13)
    ratio.GetXaxis().SetTitleOffset(0.92)
    ratio.GetXaxis().SetLabelSize(0.11)
    ratio.Draw("E1X0")
    line = ROOT.TLine(x_min, 1.0, x_max, 1.0)
    line.SetLineStyle(2)
    line.Draw("same")

    canv.SaveAs(f"{outdir}/k0_yield_data_mc_ratio.pdf")
    canv.SaveAs(f"{outdir}/k0_yield_data_mc_ratio.png")
    canv._keep = [pad1, pad2, leg_data, leg_mc, cms, line, hmc_err, hmc_outline]
    return ratio


def sideband_fit(h):
    # ROOT TF1 fit to f(m) = const + slope*m, using only sideband bins.
    hfit = h.Clone(f"{h.GetName()}_sidebands")
    ax = hfit.GetXaxis()
    for ibin in range(1, ax.GetNbins() + 1):
        x = ax.GetBinCenter(ibin)
        if any(lo <= x < hi for lo, hi in sidebands):
            continue
        hfit.SetBinContent(ibin, 0.0)
        hfit.SetBinError(ibin, 0.0)

    fit = ROOT.TF1(f"fit_{h.GetName()}", "pol1", sidebands[0][0], sidebands[-1][1])
    fit_result = hfit.Fit(fit, "QS0")
    return fit, fit_result


def fitted_bin_sum(fit, fit_result, axis, selected_bins):
    # The histogram is in counts per bin, so sum the fitted bin contents.
    #
    # f(x) = p0 + p1 x
    #
    # V = (Var(p0)      Cov(p0,p1))
    #     (Cov(p0,p1)   Var(p1))
    #
    #
    # n_bins = N
    # x_sum  = X
    # value  = B
    #
    # uncertainty on:
    # B = N p_0 + X p_1
    # is:
    # Var(B) = (dB/dp0)^2 Var(p0) + 
    #


    x_sum = sum(axis.GetBinCenter(i) for i in selected_bins)
    n_bins = len(selected_bins)
    value = sum(fit.Eval(axis.GetBinCenter(i)) for i in selected_bins)

    cov00 = fit_result.CovMatrix(0, 0)
    cov01 = fit_result.CovMatrix(0, 1)
    cov11 = fit_result.CovMatrix(1, 1)
    variance = n_bins * n_bins * cov00 + 2.0 * n_bins * x_sum * cov01 + x_sum * x_sum * cov11
    return value, max(variance, 0.0)


def yield_in_lxy_bin(h2, first_lxy_bin, last_lxy_bin):
    mass_hist = h2.ProjectionX(f"mass_lxybin_{first_lxy_bin}_{h2.GetName()}", first_lxy_bin, last_lxy_bin, "e")
    mass_hist.Rebin(mass_rebin)

    mass_axis = mass_hist.GetXaxis()
    signal_bins = bins(mass_axis, *signal)
    signal_window_count = sum(mass_hist.GetBinContent(i) for i in signal_bins)
    signal_window_variance = sum(mass_hist.GetBinError(i) ** 2 for i in signal_bins)

    fit, fit_result = sideband_fit(mass_hist)
    fitted_background, fitted_background_variance = fitted_bin_sum(fit, fit_result, mass_axis, signal_bins)

    subtracted_yield = signal_window_count - fitted_background
    subtracted_yield_error = math.sqrt(max(signal_window_variance + fitted_background_variance, 0.0))

    return signal_window_count, fitted_background, subtracted_yield, subtracted_yield_error


def run_sample(sample_name, sample):
    outdir = sample["outdir"]
    os.makedirs(outdir, exist_ok=True)

    h_data = load_hist(sample["data_file"], f"data_mass_vs_lxy_{sample_name}")
    h_mc = load_hist(sample["mc_file"], f"mc_mass_vs_lxy_{sample_name}")

    lxy_axis = h_data.GetYaxis()
    rows = []
    lxy_groups = lxy_bin_groups(lxy_axis)

    # Extract the background-subtracted K0 yield separately in each rebinned Lxy interval.
    for out_bin, (first_lxy_bin, last_lxy_bin, lxy_low, lxy_high) in enumerate(lxy_groups, 1):
        data_count, data_background, data_yield, data_error = yield_in_lxy_bin(
            h_data, first_lxy_bin, last_lxy_bin
        )
        mc_count, mc_background, mc_yield, mc_error = yield_in_lxy_bin(
            h_mc, first_lxy_bin, last_lxy_bin
        )

        rows.append(
            {
                "bin": out_bin,
                "source_lxy_bin_low": first_lxy_bin,
                "source_lxy_bin_high": last_lxy_bin,
                "lxy_low": lxy_low,
                "lxy_high": lxy_high,
                "lxy": 0.5 * (lxy_low + lxy_high),
                "data_signal_count": data_count,
                "data_fitted_background": data_background,
                "data_subtracted_yield": data_yield,
                "data_subtracted_error": data_error,
                "mc_signal_count": mc_count,
                "mc_fitted_background": mc_background,
                "mc_subtracted_yield": mc_yield,
                "mc_subtracted_error": mc_error,
            }
        )

    data_norm = sum(r["data_subtracted_yield"] for r in rows if r["lxy"] < norm_lxy_max)
    mc_norm = sum(r["mc_subtracted_yield"] for r in rows if r["lxy"] < norm_lxy_max)
    rnorm = data_norm / mc_norm
    post_norm_deviations = []

    # Normalise MC at low Lxy, then take the largest post-normalisation deviation.
    for r in rows:
        data_yield = r["data_subtracted_yield"]
        mc_yield = r["mc_subtracted_yield"]
        rho = data_yield / (rnorm * mc_yield) if data_yield > 0.0 and mc_yield > 0.0 else 0.0
        r["rho"] = rho
        r["abs_rho_minus_1"] = abs(rho - 1.0) if rho else 0.0
        if r["lxy"] >= norm_lxy_max:
            post_norm_deviations.append(r["abs_rho_minus_1"])

    post_norm_deviations = sorted(post_norm_deviations)
    largest_deviation = post_norm_deviations[-1]
    deviation_68 = post_norm_deviations[math.ceil(0.68 * len(post_norm_deviations)) - 1]

    bin_edges = lxy_bin_edges
    title = ";L_{xy} (cm);Background-subtracted K^{0}_{S} yield"
    h_yield_data = make_lxy_hist(
        f"k0_yield_data_{sample_name}",
        bin_edges,
        [r["data_subtracted_yield"] for r in rows],
        [r["data_subtracted_error"] for r in rows],
        title,
    )
    h_yield_mc = make_lxy_hist(
        f"k0_yield_mc_norm_{sample_name}",
        bin_edges,
        [rnorm * r["mc_subtracted_yield"] for r in rows],
        [rnorm * r["mc_subtracted_error"] for r in rows],
        title,
    )
    h_ratio = plot_data_mc(h_yield_data, h_yield_mc, outdir, sample["lumi_label"], sample_name)

    with open(f"{outdir}/k0_vtx_reco_unc.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    fout = ROOT.TFile(f"{outdir}/k0_vtx_reco_unc.root", "RECREATE")
    h_data.Write("input_data")
    h_mc.Write("input_mc")
    h_yield_data.Write("k0_yield_data")
    h_yield_mc.Write("k0_yield_mc_norm")
    h_ratio.Write("ratio_data_over_mc")
    fout.Close()

    with open(f"{outdir}/summary.txt", "w") as f:
        f.write(f"R_norm = {rnorm:.8g}\n")
        f.write(f"Largest post-normalisation deviation for Lxy >= {norm_lxy_max:g} cm = {largest_deviation:.8g}\n")
        f.write(f"68% post-normalisation deviation for Lxy >= {norm_lxy_max:g} cm = {deviation_68:.8g}\n")

    print(f"{sample_name}: R_norm = {rnorm:.8g}")
    print(f"{sample_name}: Largest post-normalisation deviation for Lxy >= {norm_lxy_max:g} cm = {largest_deviation:.8g}")
    print(f"{sample_name}: 68% post-normalisation deviation for Lxy >= {norm_lxy_max:g} cm = {deviation_68:.8g}")
    print(f"Wrote {outdir}")


for sample_name, sample in samples.items():
    run_sample(sample_name, sample)
