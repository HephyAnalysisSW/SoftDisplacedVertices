#!/usr/bin/env python3

"""
Plot the K0S sideband fits used for the vertex-reconstruction uncertainty.

The input is the same 2D histogram as in AN-25-092_k0_vtx_reco_unc.py, with
x = m(pi pi) and y = Lxy. For each visible Lxy bin, the script projects the
mass distribution, fits the two sidebands with a ROOT TF1 first-order
polynomial, and saves a plot showing the data and background-simulation fits
for 2017, 2018, and Run 2 separately.

Each regular Lxy bin below 20 cm is plotted separately. One final overflow-style
plot contains all entries with Lxy >= 20 cm, including the ROOT overflow bin.
The output is one PNG/PDF per Lxy bin.
"""

import os

import ROOT


ROOT.gROOT.SetBatch(True)
ROOT.TH1.SetDefaultSumw2(True)
ROOT.gStyle.SetOptStat(0)
ROOT.gStyle.SetOptTitle(0)

uniquedir = "AN-25-092_ML_plots_K0_v3"
base = f"/scratch-cbe/users/alikaan.gueven/AN_plots/ParT_hists/{uniquedir}"
hist_name = "all_vtx_k0_sel_v2/SDVSecVtx_refitMass_vs_SDVSecVtx_Lxy"

samples = {
    "2022_pre": {
        "data_file": f"{base}/data22_pre/jetmet_2022_pre_hist.root",
        "mc_file": f"{base}/bkg22_pre/all_2022pre_hist.root",
        "outdir": f"{base}/plots/k0_vtx_reco_fitplots_2022_pre",
        "lumi_label": "8.0 fb^{-1} (13.6 TeV)",
    },
    "2022_post": {
        "data_file": f"{base}/data22_post/jetmet_2022_post_hist.root",
        "mc_file": f"{base}/bkg22_post/all_2022post_hist.root",
        "outdir": f"{base}/plots/k0_vtx_reco_fitplots_2022_post",
        "lumi_label": "26.7 fb^{-1} (13.6 TeV)",
    },
    "2023_pre": {
        "data_file": f"{base}/data23_pre/jetmet_2023_pre_hist.root",
        "mc_file": f"{base}/bkg23_pre/all_2023pre_hist.root",
        "outdir": f"{base}/plots/k0_vtx_reco_fitplots_2023_pre",
        "lumi_label": "18.0 fb^{-1} (13.6 TeV)",
    },
    "2023_post": {
        "data_file": f"{base}/data23_post/jetmet_2023_post_hist.root",
        "mc_file": f"{base}/bkg23_post/all_2023post_hist.root",
        "outdir": f"{base}/plots/k0_vtx_reco_fitplots_2023_post",
        "lumi_label": "9.7 fb^{-1} (13.6 TeV)",
    },
}

signal = (0.470, 0.530)
sidebands = ((0.440, 0.470), (0.530, 0.560))
plot_lxy_max = 20.0
mass_rebin = 16


def load_hist(path, name):
    f = ROOT.TFile.Open(path)
    h = f.Get(hist_name).Clone(name)
    h.SetDirectory(0)
    f.Close()
    return h


def project_mass(h2, first_lxy_bin, last_lxy_bin, name):
    h = h2.ProjectionX(name, first_lxy_bin, last_lxy_bin, "e")
    h.SetDirectory(0)
    h.Rebin(mass_rebin)
    return h


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
    fit.SetLineColor(ROOT.kRed + 1)
    fit.SetLineWidth(3)
    hfit.Fit(fit, "Q0")
    return fit


def draw_mass_fit(pad, h, fit, lxy_label, cms_extra, lumi_label):
    pad.cd()
    pad.SetLogy()
    pad.SetLeftMargin(0.14)
    pad.SetRightMargin(0.04)
    pad.SetTopMargin(0.12)
    pad.SetBottomMargin(0.13)

    positive_bins = [
        h.GetBinContent(ibin)
        for ibin in range(1, h.GetNbinsX() + 1)
        if h.GetBinContent(ibin) > 0.0
    ]
    y_min = 0.5 * min(positive_bins) if positive_bins else 0.1
    y_max = 5.0 * max(h.GetMaximum(), 1.0)

    h.SetMarkerStyle(20)
    h.SetMarkerSize(0.7)
    h.SetMarkerColor(ROOT.kBlack)
    h.SetLineColor(ROOT.kBlack)
    h.GetXaxis().SetTitle("m_{#pi#pi} (GeV)")
    h.GetYaxis().SetTitle("Vertices")
    h.GetXaxis().SetTitleSize(0.045)
    h.GetYaxis().SetTitleSize(0.045)
    h.GetXaxis().SetLabelSize(0.040)
    h.GetYaxis().SetLabelSize(0.040)
    h.GetYaxis().SetTitleOffset(1.35)
    h.SetMinimum(y_min)
    h.SetMaximum(y_max)
    h.Draw("E1X0")
    fit.Draw("same")

    for x in signal:
        line = ROOT.TLine(x, y_min, x, y_max)
        line.SetLineStyle(2)
        line.SetLineColor(ROOT.kBlue + 1)
        line.Draw("same")
        pad._lines.append(line)

    x_axis = h.GetXaxis()
    x_centre = 0.5 * (signal[0] + signal[1])
    x_ndc = pad.GetLeftMargin() + (x_centre - x_axis.GetXmin()) / (x_axis.GetXmax() - x_axis.GetXmin()) * (
        1.0 - pad.GetLeftMargin() - pad.GetRightMargin()
    )

    cms = ROOT.TLatex()
    cms.SetNDC(True)
    cms.SetTextFont(61)
    cms.SetTextSize(0.060)
    cms.SetTextAlign(11)
    cms.DrawLatex(0.135, 0.90, "CMS")
    cms.SetTextFont(52)
    cms.SetTextSize(0.044)
    cms.DrawLatex(0.25, 0.90, cms_extra)
    cms.SetTextFont(42)
    cms.SetTextAlign(31)
    cms.DrawLatex(0.96, 0.90, lumi_label)
    cms.SetTextAlign(22)
    cms.SetTextSize(0.040)
    cms.DrawLatex(x_ndc, 0.82, lxy_label)
    cms.SetTextAlign(11)
    pad._cms = cms

    chi2 = fit.GetChisquare()
    ndf = fit.GetNDF()

    stats = ROOT.TPaveText(0.72, 0.64, 0.94, 0.80, "NDC")
    stats.SetFillColor(ROOT.kWhite)
    stats.SetFillStyle(1001)
    stats.SetLineColor(ROOT.kBlack)
    stats.SetBorderSize(1)
    stats.SetTextFont(42)
    stats.SetTextSize(0.030)
    stats.SetTextAlign(12)
    stats.AddText("#font[62]{Fit statistics}")
    stats.AddText(f"#chi^{{2}} = {chi2:.1f}")
    stats.AddText(f"ndf = {ndf}")
    stats.AddText(f"#chi^{{2}}/ndf = {chi2 / ndf:.2f}" if ndf > 0 else "#chi^{2}/ndf = -")
    stats.Draw()
    pad._stats = stats


def plot_lxy_bin(data_mass, mc_mass, data_fit, mc_fit, lxy_low, lxy_high, outname, outdir, lumi_label):
    c = ROOT.TCanvas(outname, "", 1200, 550)
    data_pad = ROOT.TPad("data_pad", "", 0.00, 0.00, 0.50, 1.00)
    mc_pad = ROOT.TPad("mc_pad", "", 0.50, 0.00, 1.00, 1.00)
    c._pads = [data_pad, mc_pad]

    data_pad._lines = []
    mc_pad._lines = []
    data_pad.Draw()
    mc_pad.Draw()

    lxy_label = (
        f"L_{{xy}} #geq {lxy_low:.2f} cm"
        if lxy_high is None
        else f"{lxy_low:.2f} #leq L_{{xy}} < {lxy_high:.2f} cm"
    )
    draw_mass_fit(data_pad, data_mass, data_fit, lxy_label, "Preliminary", lumi_label)
    draw_mass_fit(mc_pad, mc_mass, mc_fit, lxy_label, "Simulation preliminary", lumi_label)

    c.SaveAs(f"{outdir}/{outname}.png")
    c.SaveAs(f"{outdir}/{outname}.pdf")


def run_sample(sample_name, sample):
    outdir = sample["outdir"]
    os.makedirs(outdir, exist_ok=True)

    h_data = load_hist(sample["data_file"], f"data_mass_vs_lxy_{sample_name}")
    h_mc = load_hist(sample["mc_file"], f"mc_mass_vs_lxy_{sample_name}")

    lxy_axis = h_data.GetYaxis()
    visible_lxy_bins = [i for i in range(1, lxy_axis.GetNbins() + 1) if lxy_axis.GetBinLowEdge(i) < plot_lxy_max]

    for lxy_bin in visible_lxy_bins:
        lxy_low = lxy_axis.GetBinLowEdge(lxy_bin)
        lxy_high = lxy_axis.GetBinUpEdge(lxy_bin)

        data_mass = project_mass(h_data, lxy_bin, lxy_bin, f"data_mass_{sample_name}_lxybin_{lxy_bin}")
        mc_mass = project_mass(h_mc, lxy_bin, lxy_bin, f"mc_mass_{sample_name}_lxybin_{lxy_bin}")
        data_fit = sideband_fit(data_mass)
        mc_fit = sideband_fit(mc_mass)

        outname = f"k0_mass_fit_lxybin_{lxy_bin:03d}"
        plot_lxy_bin(
            data_mass,
            mc_mass,
            data_fit,
            mc_fit,
            lxy_low,
            lxy_high,
            outname,
            outdir,
            sample["lumi_label"],
        )

    first_overflow_lxy_bin = visible_lxy_bins[-1] + 1
    last_overflow_lxy_bin = lxy_axis.GetNbins() + 1
    lxy_low = lxy_axis.GetBinLowEdge(first_overflow_lxy_bin)

    data_mass = project_mass(
        h_data,
        first_overflow_lxy_bin,
        last_overflow_lxy_bin,
        f"data_mass_{sample_name}_lxybin_overflow",
    )
    mc_mass = project_mass(
        h_mc,
        first_overflow_lxy_bin,
        last_overflow_lxy_bin,
        f"mc_mass_{sample_name}_lxybin_overflow",
    )
    data_fit = sideband_fit(data_mass)
    mc_fit = sideband_fit(mc_mass)
    plot_lxy_bin(
        data_mass,
        mc_mass,
        data_fit,
        mc_fit,
        lxy_low,
        None,
        "k0_mass_fit_lxybin_overflow",
        outdir,
        sample["lumi_label"],
    )

    print(f"Wrote {outdir}")


for sample_name, sample in samples.items():
    run_sample(sample_name, sample)
