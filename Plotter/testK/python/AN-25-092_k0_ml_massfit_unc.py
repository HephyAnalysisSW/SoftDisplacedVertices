#!/usr/bin/env python3

"""
Compute the K0S based ML-tagger score-shape uncertainty using mass fits.

The input is a 2D histogram with x = m(pi pi) and y = ML score. Before fitting,
the ML-score axis is rebinned by grouping ten original score bins at a time. In
each rebinned ML-score interval, the script projects the mass distribution, fits
the K0S sidebands with a first-order polynomial, sums the fitted background
prediction over the K0S signal-window bins, and subtracts it from the
signal-window yield.

The background-subtracted score distributions are normalised independently for
data and background simulation. Their ratio is therefore a data/MC ML-score
shape ratio, not an absolute vertex-reconstruction correction. The script
reports the maximum, RMS, and 68% interval of the absolute deviations from
unity for bins with a valid data/MC ratio.
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
mc_stat_colour = ROOT.TColor.GetColor(254, 208, 26)

uniquedir = "AN-25-092_ML_plots3_k0_v5"
base = f"/scratch-cbe/users/alikaan.gueven/AN_plots/ParT_hists/{uniquedir}"
data_file = f"{base}/data_run2/met_run2_hist.root"
mc_file = f"{base}/bkg_run2/all_run2_hist.root"
hist_name = "all_vtx_k0_sel_v2/SDVSecVtx_mass_vs_ML_score"
outdir = f"{base}/plots/k0_ml_massfit_unc"
os.makedirs(outdir, exist_ok=True)

signal = (0.470, 0.530)
sidebands = ((0.440, 0.470), (0.530, 0.560))
mass_rebin = 4
score_rebin_factor = 20


def load_hist(path, name):
    f = ROOT.TFile.Open(path)
    h = f.Get(hist_name).Clone(name)
    h.SetDirectory(0)
    f.Close()
    return h


def bins(axis, low, high):
    return [i for i in range(1, axis.GetNbins() + 1) if low <= axis.GetBinCenter(i) < high]


def sideband_fit(h):
    hfit = h.Clone(f"{h.GetName()}_sidebands")
    axis = hfit.GetXaxis()

    for ibin in range(1, axis.GetNbins() + 1):
        mass = axis.GetBinCenter(ibin)
        if any(low <= mass < high for low, high in sidebands):
            continue
        hfit.SetBinContent(ibin, 0.0)
        hfit.SetBinError(ibin, 0.0)

    fit = ROOT.TF1(f"fit_{h.GetName()}", "pol1", sidebands[0][0], sidebands[-1][1])
    fit_result = hfit.Fit(fit, "QS0")
    return fit, fit_result


def fitted_bin_sum(fit, fit_result, axis, selected_bins):
    # The histogram is in counts per bin, so sum the fitted bin contents.
    x_sum = sum(axis.GetBinCenter(i) for i in selected_bins)
    n_bins = len(selected_bins)
    value = sum(fit.Eval(axis.GetBinCenter(i)) for i in selected_bins)

    cov00 = fit_result.CovMatrix(0, 0)
    cov01 = fit_result.CovMatrix(0, 1)
    cov11 = fit_result.CovMatrix(1, 1)
    variance = n_bins * n_bins * cov00 + 2.0 * n_bins * x_sum * cov01 + x_sum * x_sum * cov11
    return value, max(variance, 0.0)


def make_score_bins(axis):
    groups = []
    first_bin = 1

    while first_bin <= axis.GetNbins():
        last_bin = min(first_bin + score_rebin_factor - 1, axis.GetNbins())
        groups.append((first_bin, last_bin))
        first_bin = last_bin + 1

    return groups


def yield_in_score_bin(h2, first_score_bin, last_score_bin):
    mass_hist = h2.ProjectionX(f"mass_scorebins_{first_score_bin}_{last_score_bin}_{h2.GetName()}", first_score_bin, last_score_bin, "e")
    mass_hist.Rebin(mass_rebin)
    mass_axis = mass_hist.GetXaxis()
    signal_bins = bins(mass_axis, *signal)

    signal_count = sum(mass_hist.GetBinContent(i) for i in signal_bins)
    signal_variance = sum(mass_hist.GetBinError(i) ** 2 for i in signal_bins)

    fit, fit_result = sideband_fit(mass_hist)
    background, background_variance = fitted_bin_sum(fit, fit_result, mass_axis, signal_bins)
    subtracted_yield = signal_count - background
    subtracted_error = math.sqrt(max(signal_variance + background_variance, 0.0))

    return signal_count, background, subtracted_yield, subtracted_error


def make_score_hist(name, axis, groups, values, errors, title):
    edges = [axis.GetBinLowEdge(groups[0][0])] + [axis.GetBinUpEdge(last_bin) for _, last_bin in groups]
    h = ROOT.TH1D(name, title, len(values), array("d", edges))
    h.SetDirectory(0)

    for ibin, (value, error) in enumerate(zip(values, errors), 1):
        h.SetBinContent(ibin, value)
        h.SetBinError(ibin, error)

    return h


def normalise(h, name):
    out = h.Clone(name)
    out.SetDirectory(0)
    total = sum(h.GetBinContent(i) for i in range(1, h.GetNbinsX() + 1))

    for ibin in range(1, out.GetNbinsX() + 1):
        out.SetBinContent(ibin, h.GetBinContent(ibin) / total)
        out.SetBinError(ibin, h.GetBinError(ibin) / total)

    return out, total


def ratio_hist(hdata, hmc):
    ratio = hdata.Clone("ratio_data_over_mc_ml_shape")
    ratio.SetDirectory(0)

    for ibin in range(1, ratio.GetNbinsX() + 1):
        data_value = hdata.GetBinContent(ibin)
        mc_value = hmc.GetBinContent(ibin)

        if data_value > 0.0 and mc_value > 0.0:
            value = data_value / mc_value
            error = value * math.sqrt((hdata.GetBinError(ibin) / data_value) ** 2 + (hmc.GetBinError(ibin) / mc_value) ** 2)
        else:
            value = 0.0
            error = 0.0

        ratio.SetBinContent(ibin, value)
        ratio.SetBinError(ibin, error)

    return ratio


def positive_min(*hists):
    values = []
    for h in hists:
        values += [h.GetBinContent(i) for i in range(1, h.GetNbinsX() + 1) if h.GetBinContent(i) > 0.0]
    return min(values) if values else 1.0


def plot_score_shapes(hdata, hmc, ratio):
    x_min = hdata.GetXaxis().GetXmin()
    x_max = hdata.GetXaxis().GetXmax()
    y_min = 0.5 * positive_min(hdata, hmc)
    y_max = 5.0 * max(hdata.GetMaximum(), hmc.GetMaximum(), 1.0e-6)

    c = ROOT.TCanvas("k0_ml_massfit_unc", "", 800, 800)
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
    hmc.GetXaxis().SetRangeUser(0, 1)
    hmc.GetXaxis().SetLabelSize(0)
    hmc.GetYaxis().SetTitle("Normalised K^{0}_{S} yield")
    hmc.GetYaxis().SetTitleSize(0.055)
    hmc.GetYaxis().SetTitleOffset(1.15)
    hmc.GetYaxis().SetLabelSize(0.045)
    hmc.Draw("hist")

    hmc_err = hmc.Clone("mc_shape_stat_unc")
    hmc_err.SetFillColor(mc_stat_colour)
    hmc_err.SetFillStyle(1001)
    hmc_err.SetMarkerSize(0)
    hmc_err.SetLineColor(mc_stat_colour)
    hmc_err.Draw("E2 same")

    hmc_outline = hmc.Clone("mc_shape_outline")
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
    cms.DrawLatex(0.96, 0.92, "100 fb^{-1} (13 TeV)")
    cms.SetTextAlign(11)

    pad2.cd()
    ratio.SetMinimum(0.5)
    ratio.SetMaximum(1.6)
    ratio.SetMarkerStyle(20)
    ratio.SetMarkerSize(0.8)
    ratio.SetMarkerColor(ROOT.kBlack)
    ratio.SetLineColor(ROOT.kBlack)
    ratio.GetYaxis().SetTitle("Data/MC")
    ratio.GetYaxis().SetTitleSize(0.12)
    ratio.GetYaxis().SetTitleOffset(0.48)
    ratio.GetYaxis().SetLabelSize(0.10)
    ratio.GetXaxis().SetRangeUser(0, 1)
    ratio.GetYaxis().SetNdivisions(505)
    ratio.GetXaxis().SetTitle("ML score")
    ratio.GetXaxis().SetTitleSize(0.13)
    ratio.GetXaxis().SetTitleOffset(0.92)
    ratio.GetXaxis().SetLabelSize(0.11)
    ratio.Draw("E1X0")

    line = ROOT.TLine(x_min, 1.0, x_max, 1.0)
    line.SetLineStyle(2)
    line.Draw("same")

    c.SaveAs(f"{outdir}/k0_ml_massfit_shape_ratio.pdf")
    c.SaveAs(f"{outdir}/k0_ml_massfit_shape_ratio.png")
    c._keep = [pad1, pad2, leg_data, leg_mc, cms, line, hmc_err, hmc_outline]


h_data = load_hist(data_file, "data_mass_vs_ml")
h_mc = load_hist(mc_file, "mc_mass_vs_ml")
score_axis = h_data.GetYaxis()
score_groups = make_score_bins(score_axis)
rows = []

for score_bin, (first_score_bin, last_score_bin) in enumerate(score_groups, 1):
    data_count, data_background, data_yield, data_error = yield_in_score_bin(h_data, first_score_bin, last_score_bin)
    mc_count, mc_background, mc_yield, mc_error = yield_in_score_bin(h_mc, first_score_bin, last_score_bin)

    rows.append(
        {
            "score_bin": score_bin,
            "source_score_bin_low": first_score_bin,
            "source_score_bin_high": last_score_bin,
            "score_low": score_axis.GetBinLowEdge(first_score_bin),
            "score_high": score_axis.GetBinUpEdge(last_score_bin),
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

h_data_yield = make_score_hist(
    "data_k0_subtracted_yield_vs_ml_score",
    score_axis,
    score_groups,
    [r["data_subtracted_yield"] for r in rows],
    [r["data_subtracted_error"] for r in rows],
    ";ML score;Background-subtracted K^{0}_{S} yield",
)
h_mc_yield = make_score_hist(
    "mc_k0_subtracted_yield_vs_ml_score",
    score_axis,
    score_groups,
    [r["mc_subtracted_yield"] for r in rows],
    [r["mc_subtracted_error"] for r in rows],
    ";ML score;Background-subtracted K^{0}_{S} yield",
)

h_data_shape, data_total = normalise(h_data_yield, "data_normalised_ml_score_shape")
h_mc_shape, mc_total = normalise(h_mc_yield, "mc_normalised_ml_score_shape")
h_ratio = ratio_hist(h_data_shape, h_mc_shape)

for row in rows:
    ibin = row["score_bin"]
    sf = h_ratio.GetBinContent(ibin)
    valid_ratio = row["data_subtracted_yield"] > 0.0 and row["mc_subtracted_yield"] > 0.0 and sf > 0.0
    delta = abs(1.0 - sf) if valid_ratio else 0.0

    row["data_total_subtracted_yield"] = data_total
    row["mc_total_subtracted_yield"] = mc_total
    row["p_data"] = h_data_shape.GetBinContent(ibin)
    row["p_mc"] = h_mc_shape.GetBinContent(ibin)
    row["shape_ratio_data_over_mc"] = sf
    row["shape_ratio_error"] = h_ratio.GetBinError(ibin)
    row["valid_ratio"] = int(valid_ratio)
    row["abs_ratio_minus_1"] = delta

valid_rows = [row for row in rows if row["valid_ratio"]]
abs_deviations = sorted(row["abs_ratio_minus_1"] for row in valid_rows)
max_row = max(valid_rows, key=lambda row: row["abs_ratio_minus_1"])
delta_max = max_row["abs_ratio_minus_1"]
rms = math.sqrt(sum(delta**2 for delta in abs_deviations) / len(abs_deviations))
delta_68 = abs_deviations[math.ceil(0.68 * len(abs_deviations)) - 1]

plot_score_shapes(h_data_shape, h_mc_shape, h_ratio)

with open(f"{outdir}/k0_ml_massfit_shape_ratios.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)

with open(f"{outdir}/k0_ml_massfit_unc_summary.txt", "w") as f:
    f.write(f"ML-score rebin factor: {score_rebin_factor}\n")
    f.write(f"Rebinned ML-score bins: {len(score_groups)}\n")
    f.write(f"Bins with valid data/MC ratio: {len(valid_rows)}\n")
    f.write(f"Maximum absolute deviation from zero: {delta_max:.6f}\n")
    f.write(f"RMS of absolute deviations: {rms:.6f}\n")
    f.write(f"68% interval of absolute deviations: 0 to {delta_68:.6f}\n")
    f.write(f"Max-deviation score bin: {max_row['score_low']:.6g} to {max_row['score_high']:.6g}\n")
    f.write(f"Shape ratio data/MC in that bin: {max_row['shape_ratio_data_over_mc']:.6f}\n")

fout = ROOT.TFile(f"{outdir}/k0_ml_massfit_unc.root", "RECREATE")
for h in [h_data, h_mc, h_data_yield, h_mc_yield, h_data_shape, h_mc_shape, h_ratio]:
    h.Write()
fout.Close()

print(f"ML-score rebin factor: {score_rebin_factor}")
print(f"Rebinned ML-score bins: {len(score_groups)}")
print(f"Bins with valid data/MC ratio: {len(valid_rows)}")
print(f"Maximum absolute deviation from zero: {delta_max:.6f}")
print(f"RMS of absolute deviations: {rms:.6f}")
print(f"68% interval of absolute deviations: {delta_68:.6f}")
print(f"Wrote {outdir}")
