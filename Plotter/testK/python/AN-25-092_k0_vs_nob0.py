import os
from array import array
import ROOT

ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)
ROOT.gStyle.SetOptTitle(0)
ROOT.gStyle.SetTitleFont(42, "XYZ")
ROOT.gStyle.SetLabelFont(42, "XYZ")
ROOT.gStyle.SetTitleSize(0.046, "XYZ")
ROOT.gStyle.SetLabelSize(0.040, "XYZ")
ROOT.gStyle.SetPadTickX(1)
ROOT.gStyle.SetPadTickY(1)
ROOT.Math.MinimizerOptions.SetDefaultMaxFunctionCalls(1000000)
ROOT.Math.MinimizerOptions.SetDefaultMaxIterations(100000)


uniquedir = "AN-25-092_ML_plots3"
input_path = f"/scratch-cbe/users/alikaan.gueven/AN_plots/ParT_hists/{uniquedir}/bkg_run2/all_run2_hist.root"
outdir = f"/scratch-cbe/users/alikaan.gueven/AN_plots/ParT_hists/{uniquedir}/plots/k0_vs_nob0"
os.makedirs(outdir, exist_ok=True)

hist_names = {
    "k0": "all_evt/k0_Max_ML_score",
    "nob0": "all_evt/nob0_Max_ML_score",
}

rebin_factor = 4


def load_hist(root_file, name, clone_name):
    hist = root_file.Get(name)
    if not hist:
        raise RuntimeError(f"Histogram not found: {name}")
    if not hist.InheritsFrom("TH1"):
        raise RuntimeError(f"Object is not a TH1 histogram: {name}")

    hist = hist.Clone(clone_name)
    hist.SetDirectory(0)
    hist.Rebin(rebin_factor)

    integral = hist.Integral(1, hist.GetNbinsX())
    if integral <= 0.0:
        raise RuntimeError(f"Histogram has non-positive integral after rebinning: {name}")

    hist.Scale(1.0 / integral)
    return hist, integral


def min_positive_bin(*hists):
    values = []
    for hist in hists:
        values.extend(
            hist.GetBinContent(i)
            for i in range(1, hist.GetNbinsX() + 1)
            if hist.GetBinContent(i) > 0.0
        )
    return min(values) if values else 1.0e-6


def chebyshev_expression(order):
    terms = ["[0]"]
    for i in range(1, order + 1):
        terms.append(f"[{i}]*cos({i}*acos(2*x-1))")
    return " + ".join(terms)


f_in = ROOT.TFile.Open(input_path)
if not f_in or f_in.IsZombie():
    raise RuntimeError(f"Could not open input file: {input_path}")

h_k0, k0_integral = load_hist(f_in, hist_names["k0"], "h_k0_Max_ML_score")
h_nob0, nob0_integral = load_hist(f_in, hist_names["nob0"], "h_nob0_Max_ML_score")
f_in.Close()

h_k0.SetLineColor(ROOT.kRed + 1)
h_k0.SetMarkerColor(ROOT.kRed + 1)
h_k0.SetLineWidth(3)

h_nob0.SetLineColor(ROOT.kBlue + 1)
h_nob0.SetMarkerColor(ROOT.kBlue + 1)
h_nob0.SetLineWidth(3)

bin_width = h_k0.GetXaxis().GetBinWidth(1)
ymin = max(0.4 * min_positive_bin(h_k0, h_nob0), 1.0e-7)
ymax = max(h_k0.GetMaximum(), h_nob0.GetMaximum()) * 35.0

c = ROOT.TCanvas("c", "", 800, 800)
c.SetTicks(1, 1)

top = ROOT.TPad("top", "", 0.0, 0.30, 1.0, 1.0)
bottom = ROOT.TPad("bottom", "", 0.0, 0.0, 1.0, 0.30)

top.SetLeftMargin(0.14)
top.SetRightMargin(0.045)
top.SetTopMargin(0.16)
top.SetBottomMargin(0.025)
top.SetTicks(1, 1)
top.SetLogy(True)

bottom.SetLeftMargin(0.14)
bottom.SetRightMargin(0.045)
bottom.SetTopMargin(0.035)
bottom.SetBottomMargin(0.36)
bottom.SetTicks(1, 1)
bottom.SetGridy(True)

top.Draw()
bottom.Draw()

top.cd()
h_k0.SetMinimum(ymin)
h_k0.SetMaximum(ymax)
h_k0.GetXaxis().SetLabelSize(0)
h_k0.GetXaxis().SetTitleSize(0)
h_k0.GetYaxis().SetTitle(f"Normalised entries / {bin_width:.3f}")
h_k0.GetYaxis().SetTitleSize(0.055)
h_k0.GetYaxis().SetLabelSize(0.047)
h_k0.GetYaxis().SetTitleOffset(1.12)

h_k0.Draw("HIST")
h_nob0.Draw("HIST SAME")

leg = ROOT.TLegend(0.55, 0.68, 0.93, 0.80)
leg.SetBorderSize(0)
leg.SetFillStyle(0)
leg.SetTextFont(42)
leg.SetTextSize(0.034)
leg.AddEntry(h_k0, "K^{0}_{s} vertices", "l")
leg.AddEntry(h_nob0, "#splitline{Vertices within the jets,}{excluding B jets}", "l")
leg.Draw()

latex = ROOT.TLatex()
latex.SetNDC(True)
latex.SetTextColor(ROOT.kBlack)
latex.SetTextAlign(11)
latex.SetTextFont(61)
latex.SetTextSize(0.065)
latex.DrawLatex(0.138, 0.857, "CMS")
latex.SetTextFont(52)
latex.SetTextSize(0.0468)
latex.DrawLatex(0.234, 0.857, "Simulation Preliminary")
latex.SetTextFont(42)
latex.SetTextAlign(31)
latex.DrawLatex(0.955, 0.857, "100 fb^{-1} (13 TeV)")

bottom.cd()
ratio = h_k0.Clone("ratio_k0_over_nob0_Max_ML_score")
ratio.Divide(h_nob0)
ratio.SetLineColor(ROOT.kBlack)
ratio.SetMarkerColor(ROOT.kBlack)
ratio.SetMarkerStyle(20)
ratio.SetMarkerSize(0.55)
ratio.SetLineWidth(2)
ratio.SetMinimum(0.0)
ratio.SetMaximum(2.0)
ratio.GetXaxis().SetTitle("Max ML score")
ratio.GetXaxis().SetTitleSize(0.120)
ratio.GetXaxis().SetLabelSize(0.100)
ratio.GetXaxis().SetTitleOffset(1.05)
ratio.GetYaxis().SetTitle("K^{0}_{S} / no B")
ratio.GetYaxis().SetTitleSize(0.105)
ratio.GetYaxis().SetLabelSize(0.085)
ratio.GetYaxis().SetTitleOffset(0.55)
ratio.GetYaxis().SetNdivisions(505)
ratio.Draw("E1")

first_bin_center = ratio.GetBinCenter(1)
last_bin_center = ratio.GetBinCenter(ratio.GetNbinsX())
fit_order = 26
ratio_fit = ROOT.TF1(
    "ratio_k0_over_nob0_cheb26_fit",
    chebyshev_expression(fit_order),
    first_bin_center,
    last_bin_center,
)
fit_parameters = [
    0.6112009077693326,
    -0.5587765279240455,
    -0.2904416410528204,
    0.2589232158331933,
    0.09091910399481277,
    -0.1685810964486521,
    0.07895515770034985,
    -0.055736557355437547,
    0.05315784764600295,
    -0.0105759481321796,
    -0.0270687132029274,
    0.002008518625282358,
    0.0489447902648774,
    -0.04778353682572737,
    0.008774330496666703,
    5.7431101986251895e-05,
    0.01732940157650891,
    -0.011082704732332218,
    -0.012509169693233098,
    0.013436157025478011,
    0.007798797828373012,
    -0.014293221185240835,
    0.0002707630642848477,
    0.007895018926862757,
    -0.0036959927066548995,
    0.0007292714321852725,
    -0.003123472916783423,
]
for i, value in enumerate(fit_parameters):
    ratio_fit.SetParameter(i, value)
ratio_fit.SetNpx(5000)
ratio_fit.SetLineColor(ROOT.kRed + 1)
ratio_fit.SetLineWidth(3)
ratio.Fit(ratio_fit, "QMRS0")

running_average_window = 5
half_window = running_average_window // 2
running_x = array("d")
running_y = array("d")
running_xerr = array("d")
running_yerr = array("d")

for i in range(1, ratio.GetNbinsX() + 1):
    lower_bin = max(1, i - half_window)
    upper_bin = min(ratio.GetNbinsX(), i + half_window)
    weight_sum = 0.0
    weighted_value_sum = 0.0

    for j in range(lower_bin, upper_bin + 1):
        bin_error = ratio.GetBinError(j)
        if bin_error <= 0.0:
            continue
        weight = 1.0 / (bin_error * bin_error)
        weight_sum += weight
        weighted_value_sum += weight * ratio.GetBinContent(j)

    if weight_sum <= 0.0:
        continue

    running_x.append(ratio.GetBinCenter(i))
    running_y.append(weighted_value_sum / weight_sum)
    running_xerr.append(0.0)
    running_yerr.append((1.0 / weight_sum) ** 0.5)

running_average = ROOT.TGraphErrors(
    len(running_x),
    running_x,
    running_y,
    running_xerr,
    running_yerr,
)
running_average.SetName("ratio_k0_over_nob0_running_average_w5")
running_average.SetTitle("Weighted running average of k0 / nob0")
running_average.SetLineColor(ROOT.kGreen + 2)
running_average.SetMarkerColor(ROOT.kGreen + 2)
running_average.SetLineWidth(3)
running_average.SetMarkerStyle(1)

line = ROOT.TLine(
    ratio.GetXaxis().GetXmin(),
    1.0,
    ratio.GetXaxis().GetXmax(),
    1.0,
)
line.SetLineColor(ROOT.kGray + 2)
line.SetLineStyle(2)
line.SetLineWidth(2)
line.Draw("SAME")
# ratio_fit.Draw("SAME")
# running_average.Draw("L SAME")
ratio.Draw("E1 SAME")

base = "k0_vs_nob0"
c.SaveAs(f"{outdir}/{base}.png")
c.SaveAs(f"{outdir}/{base}.pdf")

f_out = ROOT.TFile(f"{outdir}/{base}.root", "RECREATE")
h_k0.Write()
h_nob0.Write()
ratio.Write()
ratio_fit.Write()
running_average.Write()

chi2 = array("d", [ratio_fit.GetChisquare()])
ndf = array("i", [ratio_fit.GetNDF()])
chi2_ndf = array("d", [chi2[0] / ndf[0] if ndf[0] > 0 else 0.0])
prob = array("d", [ROOT.TMath.Prob(chi2[0], ndf[0]) if ndf[0] > 0 else 0.0])

fit_stats = ROOT.TTree("ratio_fit_chi2_stats", "Ratio fit chi2 statistics")
fit_stats.Branch("chi2", chi2, "chi2/D")
fit_stats.Branch("ndf", ndf, "ndf/I")
fit_stats.Branch("chi2_ndf", chi2_ndf, "chi2_ndf/D")
fit_stats.Branch("prob", prob, "prob/D")
fit_stats.Fill()
fit_stats.Write()
f_out.Close()
