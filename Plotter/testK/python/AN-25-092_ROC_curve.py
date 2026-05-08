import os
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



uniquedir = "AN-25-092_ML_plots3_unmatched"

outdir = f"/scratch-cbe/users/alikaan.gueven/AN_plots/ParT_hists/{uniquedir}/plots/ROC"
os.makedirs(outdir, exist_ok=True)

hname = "all_evt/Max_ML_score"
fb = ROOT.TFile.Open(f"/scratch-cbe/users/alikaan.gueven/AN_plots/ParT_hists/{uniquedir}/bkg_run2/all_run2_hist.root")
fs = ROOT.TFile.Open(f"/scratch-cbe/users/alikaan.gueven/AN_plots/ParT_hists/{uniquedir}/sig_run2/stop_M1000_985_ct20_run2_hist.root")
hb = fb.Get(hname)
hs = fs.Get(hname)

nb = hs.GetNbinsX()
stot = hs.Integral(1, nb + 1)
btot = hb.Integral(1, nb + 1)
g = ROOT.TGraph(nb + 1)
pts = []

for i in range(1, nb + 2):
    sig_eff = hs.Integral(i, nb + 1) / stot
    bkg_rej = 1.0 - hb.Integral(i, nb + 1) / btot
    g.SetPoint(i - 1, sig_eff, bkg_rej)
    pts.append((sig_eff, bkg_rej))

pts = sorted(pts)
auc = sum((pts[i + 1][0] - pts[i][0]) * (pts[i + 1][1] + pts[i][1]) / 2.0 for i in range(len(pts) - 1))

g.SetName("ROC_Max_ML_score")
g.SetLineColor(ROOT.kBlue + 1)
g.SetLineWidth(3)

c = ROOT.TCanvas("c", "", 800, 700)
c.SetLeftMargin(0.14)
c.SetRightMargin(0.045)
c.SetBottomMargin(0.13)
c.SetTopMargin(0.12)
c.SetTicks(1, 1)

frame = c.DrawFrame(0.0, 0.0, 1.0, 1.0)
frame.GetXaxis().SetTitle("Signal efficiency (TPR)")
frame.GetYaxis().SetTitle("Background rejection (1 - FPR)")

rand = ROOT.TLine(0.0, 1.0, 1.0, 0.0)
rand.SetLineStyle(2)
rand.SetLineColor(ROOT.kGray + 2)
rand.SetLineWidth(2)
rand.Draw()
g.Draw("L SAME")

leg = ROOT.TLegend(0.20, 0.40, 0.38, 0.48)
leg.SetBorderSize(0)
leg.SetFillStyle(0)
leg.SetTextFont(42)
leg.SetTextSize(0.030)
leg.AddEntry(g, "ParT with Run-2 MC", "l")
leg.AddEntry(rand, "Random classifier", "l")
leg.Draw()
latex = ROOT.TLatex()
latex.SetNDC(True)
latex.SetTextColor(ROOT.kBlack)
latex.SetTextAlign(11)
latex.SetTextFont(61)
latex.SetTextSize(0.050)
latex.DrawLatex(0.138, 0.894, "CMS")
latex.SetTextFont(52)
latex.SetTextSize(0.036)
latex.DrawLatex(0.234, 0.894, "Simulation Preliminary")
latex.SetTextFont(42)
latex.SetTextAlign(31)
latex.DrawLatex(0.955, 0.894, "100 fb^{-1} (13 TeV)")
latex.SetTextAlign(11)
latex.SetTextSize(0.030)
latex.DrawLatex(0.247, 0.20, f"AUC (Run-2) = {auc:.3f}")
c.SaveAs(f"{outdir}/AN-25-092_ROC_curve.png")
c.SaveAs(f"{outdir}/AN-25-092_ROC_curve.pdf")

fout = ROOT.TFile(f"{outdir}/AN-25-092_ROC_curve.root", "RECREATE")
g.Write()
fout.Close()
