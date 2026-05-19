#!/usr/bin/env python3

"""
Compute the K0S based ML vertex-tagger score-shape uncertainty.

The input is a 2D histogram with x = m(pi pi) and y = ML score. In each
rebinned ML-score interval, the script projects the invariant-mass
distribution, fits the K0S sidebands with a first-order polynomial, sums the
fitted background prediction in the K0S signal-window bins, and subtracts it
from the observed signal-window yield.

The background-subtracted score distributions are normalised independently for
data and background simulation. Their ratio is therefore a data/MC ML-score
shape ratio, not an absolute vertex-reconstruction correction. The invariant
mass rebinning follows the vertex reconstruction scripts: 8 for 2017/2018 and
16 for 2022/2023.
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

hist_name = "all_vtx_k0_sel/SDVSecVtx_refitMass_vs_ML_score"
uniquedir = "AN-25-092_ML_plots_K0_v3"
base = f"/scratch-cbe/users/alikaan.gueven/AN_plots/ParT_hists/{uniquedir}"

signal = (0.470, 0.530)
sidebands = ((0.440, 0.470), (0.530, 0.560))
score_bin_edges = [
    0.0,
    0.02,
    0.04,
    0.06,
    0.10,
    0.14,
    0.18,
    0.22,
    0.26,
    0.30,
    0.36,
    0.44,
    0.56,
    0.70,
    0.999,
]
ratio_y_min = 0.5
ratio_y_max = 1.5


def build_samples(base):
    return {
        "2017": {
            "data_file": f"{base}/data17/met_2017_hist.root",
            "mc_file": f"{base}/bkg17/all_2017_hist.root",
            "outdir": f"{base}/plots/k0_ml_tagger_unc_2017",
            "lumi_label": "42.1 fb^{-1} (13 TeV)",
            "mass_rebin": 8,
        },
        "2018": {
            "data_file": f"{base}/data18/met_2018_hist.root",
            "mc_file": f"{base}/bkg18/all_2018_hist.root",
            "outdir": f"{base}/plots/k0_ml_tagger_unc_2018",
            "lumi_label": "59.6 fb^{-1} (13 TeV)",
            "mass_rebin": 8,
        },
        "2022_pre": {
            "data_file": f"{base}/data22_pre/jetmet_2022_pre_hist.root",
            "mc_file": f"{base}/bkg22_pre/all_2022pre_hist.root",
            "outdir": f"{base}/plots/k0_ml_tagger_unc_2022_pre",
            "lumi_label": "8.0 fb^{-1} (13.6 TeV)",
            "mass_rebin": 16,
        },
        "2022_post": {
            "data_file": f"{base}/data22_post/jetmet_2022_post_hist.root",
            "mc_file": f"{base}/bkg22_post/all_2022post_hist.root",
            "outdir": f"{base}/plots/k0_ml_tagger_unc_2022_post",
            "lumi_label": "26.7 fb^{-1} (13.6 TeV)",
            "mass_rebin": 16,
        },
        "2023_pre": {
            "data_file": f"{base}/data23_pre/jetmet_2023_pre_hist.root",
            "mc_file": f"{base}/bkg23_pre/all_2023pre_hist.root",
            "outdir": f"{base}/plots/k0_ml_tagger_unc_2023_pre",
            "lumi_label": "18.0 fb^{-1} (13.6 TeV)",
            "mass_rebin": 16,
        },
        "2023_post": {
            "data_file": f"{base}/data23_post/jetmet_2023_post_hist.root",
            "mc_file": f"{base}/bkg23_post/all_2023post_hist.root",
            "outdir": f"{base}/plots/k0_ml_tagger_unc_2023_post",
            "lumi_label": "9.7 fb^{-1} (13.6 TeV)",
            "mass_rebin": 16,
        },
    }


def load_hist(path, name):
    f = ROOT.TFile.Open(path)
    if not f or f.IsZombie():
        raise OSError(f"Could not open {path}")
    h_in = f.Get(hist_name)
    if not h_in:
        f.Close()
        raise KeyError(f"Could not find histogram {hist_name} in {path}")
    h = h_in.Clone(name)
    h.SetDirectory(0)
    f.Close()
    return h


def normalised_shape(h, name):
    shape = h.Clone(name)
    shape.SetDirectory(0)
    total = sum(h.GetBinContent(i) for i in range(1, h.GetNbinsX() + 1))

    for i in range(1, shape.GetNbinsX() + 1):
        if total > 0.0:
            shape.SetBinContent(i, h.GetBinContent(i) / total)
            shape.SetBinError(i, h.GetBinError(i) / total)
        else:
            shape.SetBinContent(i, 0.0)
            shape.SetBinError(i, 0.0)

    return shape, total


def shape_ratio(hdata, hmc, name):
    ratio = hdata.Clone(name)
    ratio.SetDirectory(0)
    ratio.Divide(hmc)
    return ratio


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
    for low, high in zip(score_bin_edges[:-1], score_bin_edges[1:]):
        selected_bins = [
            ibin
            for ibin in range(1, axis.GetNbins() + 1)
            if low <= axis.GetBinCenter(ibin) < high
        ]
        if not selected_bins:
            raise RuntimeError(f"No ML-score source bins found for interval {low:g} to {high:g}")
        groups.append((selected_bins[0], selected_bins[-1], low, high))
    return groups


def yield_in_score_bin(h2, first_score_bin, last_score_bin, mass_rebin):
    mass_hist = h2.ProjectionX(
        f"mass_scorebins_{first_score_bin}_{last_score_bin}_{h2.GetName()}",
        first_score_bin,
        last_score_bin,
        "e",
    )
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
    edges = [groups[0][2]] + [high for _, _, _, high in groups]
    h = ROOT.TH1D(name, title, len(values), array("d", edges))
    h.SetDirectory(0)

    for ibin, (value, error) in enumerate(zip(values, errors), 1):
        h.SetBinContent(ibin, value)
        h.SetBinError(ibin, error)

    return h


def positive_min(*hists):
    values = []
    for h in hists:
        values += [h.GetBinContent(i) for i in range(1, h.GetNbinsX() + 1) if h.GetBinContent(i) > 0.0]
    return min(values) if values else 1.0


def plot_shape(data_shape, mc_shape, ratio, outdir, lumi_label, outname):
    x_min = 0.0
    x_max = 1.0
    y_min = 0.5 * positive_min(data_shape, mc_shape)
    y_max = 5.0 * max(data_shape.GetMaximum(), mc_shape.GetMaximum(), 1.0e-6)

    c = ROOT.TCanvas(outname, "", 800, 800)
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
    mc_shape.SetFillColor(ROOT.kBlue - 9)
    mc_shape.SetLineColor(ROOT.kBlue + 1)
    mc_shape.SetLineWidth(1)
    mc_shape.SetMarkerSize(0)
    mc_shape.SetMinimum(y_min)
    mc_shape.SetMaximum(y_max)
    mc_shape.GetXaxis().SetLabelSize(0)
    mc_shape.GetYaxis().SetTitle("Normalised K^{0}_{S} yield")
    mc_shape.GetYaxis().SetTitleSize(0.055)
    mc_shape.GetYaxis().SetTitleOffset(1.15)
    mc_shape.GetYaxis().SetLabelSize(0.045)
    mc_shape.Draw("hist")

    mc_error = mc_shape.Clone(f"{outname}_mc_stat")
    mc_error.SetFillColor(mc_stat_colour)
    mc_error.SetFillStyle(1001)
    mc_error.SetMarkerSize(0)
    mc_error.SetLineColor(mc_stat_colour)
    mc_error.Draw("E2 same")

    mc_outline = mc_shape.Clone(f"{outname}_mc_outline")
    mc_outline.SetFillStyle(0)
    mc_outline.SetMarkerSize(0)
    mc_outline.Draw("hist same")

    data_shape.SetMarkerStyle(20)
    data_shape.SetMarkerSize(0.8)
    data_shape.SetMarkerColor(ROOT.kBlack)
    data_shape.SetLineColor(ROOT.kBlack)
    data_shape.Draw("E1X0 same")

    leg_data = ROOT.TLegend(0.22, 0.80, 0.42, 0.88)
    leg_data.SetBorderSize(0)
    leg_data.SetFillStyle(0)
    leg_data.SetTextFont(42)
    leg_data.SetTextSize(0.035)
    leg_data.AddEntry(data_shape, "Data", "pe")
    leg_data.Draw()

    leg_mc = ROOT.TLegend(0.52, 0.75, 0.88, 0.88)
    leg_mc.SetBorderSize(0)
    leg_mc.SetFillStyle(0)
    leg_mc.SetTextFont(42)
    leg_mc.SetTextSize(0.035)
    leg_mc.AddEntry(mc_shape, "Background simulation", "f")
    leg_mc.AddEntry(mc_error, "MC statistical uncertainty", "f")
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
    ratio.SetMinimum(ratio_y_min)
    ratio.SetMaximum(ratio_y_max)
    ratio.SetMarkerStyle(20)
    ratio.SetMarkerSize(0.8)
    ratio.SetMarkerColor(ROOT.kBlack)
    ratio.SetLineColor(ROOT.kBlack)
    ratio.GetYaxis().SetTitle("Data/MC")
    ratio.GetYaxis().SetTitleSize(0.12)
    ratio.GetYaxis().SetTitleOffset(0.48)
    ratio.GetYaxis().SetLabelSize(0.10)
    ratio.GetYaxis().SetNdivisions(505)
    ratio.GetXaxis().SetTitle("ML score")
    ratio.GetXaxis().SetTitleSize(0.13)
    ratio.GetXaxis().SetTitleOffset(0.92)
    ratio.GetXaxis().SetLabelSize(0.11)
    ratio.Draw("E1X0")
    line = ROOT.TLine(x_min, 1.0, x_max, 1.0)
    line.SetLineStyle(2)
    line.Draw("same")

    c.SaveAs(f"{outdir}/{outname}.pdf")
    c.SaveAs(f"{outdir}/{outname}.png")
    c._keep = [pad1, pad2, leg_data, leg_mc, cms, line, mc_error, mc_outline]


def run_sample(sample_name, sample):
    outdir = sample["outdir"]
    os.makedirs(outdir, exist_ok=True)

    h_data = load_hist(sample["data_file"], f"data_mass_vs_ml_{sample_name}")
    h_mc = load_hist(sample["mc_file"], f"mc_mass_vs_ml_{sample_name}")
    score_axis = h_data.GetYaxis()
    score_groups = make_score_bins(score_axis)
    rows = []

    for score_bin, (first_score_bin, last_score_bin, score_low, score_high) in enumerate(score_groups, 1):
        data_count, data_background, data_yield, data_error = yield_in_score_bin(
            h_data, first_score_bin, last_score_bin, sample["mass_rebin"]
        )
        mc_count, mc_background, mc_yield, mc_error = yield_in_score_bin(
            h_mc, first_score_bin, last_score_bin, sample["mass_rebin"]
        )

        rows.append(
            {
                "score_bin": score_bin,
                "source_score_bin_low": first_score_bin,
                "source_score_bin_high": last_score_bin,
                "score_low": score_low,
                "score_high": score_high,
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
        f"data_k0_subtracted_yield_vs_ml_score_{sample_name}",
        score_axis,
        score_groups,
        [r["data_subtracted_yield"] for r in rows],
        [r["data_subtracted_error"] for r in rows],
        ";ML score;Background-subtracted K^{0}_{S} yield",
    )
    h_mc_yield = make_score_hist(
        f"mc_k0_subtracted_yield_vs_ml_score_{sample_name}",
        score_axis,
        score_groups,
        [r["mc_subtracted_yield"] for r in rows],
        [r["mc_subtracted_error"] for r in rows],
        ";ML score;Background-subtracted K^{0}_{S} yield",
    )

    h_data_shape, data_total = normalised_shape(h_data_yield, f"data_normalised_ml_score_shape_{sample_name}")
    h_mc_shape, mc_total = normalised_shape(h_mc_yield, f"mc_normalised_ml_score_shape_{sample_name}")
    h_ratio = shape_ratio(h_data_shape, h_mc_shape, f"ratio_data_over_mc_ml_shape_{sample_name}")

    for row in rows:
        ibin = row["score_bin"]
        sf = h_ratio.GetBinContent(ibin)
        valid_ratio = row["data_subtracted_yield"] > 0.0 and row["mc_subtracted_yield"] > 0.0 and sf > 0.0
        delta = abs(1.0 - sf) if valid_ratio else 0.0

        row["mass_rebin"] = sample["mass_rebin"]
        row["data_total_subtracted_yield"] = data_total
        row["mc_total_subtracted_yield"] = mc_total
        row["p_data"] = h_data_shape.GetBinContent(ibin)
        row["p_mc"] = h_mc_shape.GetBinContent(ibin)
        row["shape_ratio_data_over_mc"] = sf
        row["shape_ratio_error"] = h_ratio.GetBinError(ibin)
        row["valid_ratio"] = int(valid_ratio)
        row["abs_ratio_minus_1"] = delta

    valid_rows = [row for row in rows if row["valid_ratio"]]
    if not valid_rows:
        raise RuntimeError(f"No valid data/MC ratio bins found for {sample_name}")

    abs_deviations = sorted(row["abs_ratio_minus_1"] for row in valid_rows)
    max_row = max(valid_rows, key=lambda row: row["abs_ratio_minus_1"])
    delta_max = max_row["abs_ratio_minus_1"]
    rms = math.sqrt(sum(delta**2 for delta in abs_deviations) / len(abs_deviations))
    delta_68 = abs_deviations[math.ceil(0.68 * len(abs_deviations)) - 1]

    plot_shape(h_data_shape, h_mc_shape, h_ratio, outdir, sample["lumi_label"], "k0_ml_massfit_shape_ratio")

    with open(f"{outdir}/k0_ml_massfit_shape_ratios.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    with open(f"{outdir}/k0_ml_tagger_unc_summary.txt", "w") as f:
        f.write(f"Sample: {sample_name}\n")
        f.write(f"Data file: {sample['data_file']}\n")
        f.write(f"MC file: {sample['mc_file']}\n")
        f.write(f"Mass rebin factor: {sample['mass_rebin']}\n")
        f.write(f"ML-score bin edges: {', '.join(f'{edge:g}' for edge in score_bin_edges)}\n")
        f.write("Ratio uncertainty: TH1::Divide using the stored histogram bin errors\n")
        f.write(f"Rebinned ML-score bins: {len(score_groups)}\n")
        f.write(f"Bins with valid data/MC ratio: {len(valid_rows)}\n")
        f.write(f"Largest absolute deviation from unity: {delta_max:.6f}\n")
        f.write(f"RMS of absolute deviations: {rms:.6f}\n")
        f.write(f"68% quantile of absolute deviations: {delta_68:.6f}\n")
        f.write(f"Max-deviation score bin: {max_row['score_low']:.6g} to {max_row['score_high']:.6g}\n")
        f.write(f"Shape ratio data/MC in that bin: {max_row['shape_ratio_data_over_mc']:.6f}\n")

    fout = ROOT.TFile(f"{outdir}/k0_ml_tagger_unc.root", "RECREATE")
    for h in [h_data, h_mc, h_data_yield, h_mc_yield, h_data_shape, h_mc_shape, h_ratio]:
        h.Write()
    fout.Close()

    print(f"{sample_name}: Mass rebin factor: {sample['mass_rebin']}")
    print(f"{sample_name}: Bins with valid data/MC ratio: {len(valid_rows)}")
    print(f"{sample_name}: Largest absolute deviation from unity: {delta_max:.6f}")
    print(f"{sample_name}: 68% quantile of absolute deviations: {delta_68:.6f}")
    print(f"Wrote {outdir}")


def main():
    samples = build_samples(base)
    for sample_name, sample in samples.items():
        run_sample(sample_name, sample)


if __name__ == "__main__":
    main()
