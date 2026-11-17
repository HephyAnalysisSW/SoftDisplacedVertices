#!/usr/bin/env python3
'''Overlay rotated D candidates with gen-matched signal vertices (unit-normalised shapes).

Rotated histograms are read from <region>_RotateVtx_<sel>/RotateVtx_<var> (plotconfig_*_RotateK0_reweight),
signal histograms from <region>_SDVSecVtx_<sigsel>/SDVSecVtx_<var> (plotconfig_Run3_RotateSignal).
Each plot shows: rotated data, rotated background MC, unrotated data (if a "_before" variable exists)
and every signal file.

Example:
  python3 compare_rotate_signal.py \\
    --data Histos/jetmet_run3_hist.root --bkg Histos/background_run3_hist.root \\
    --signal C1N2_M400_395_ct2_run3_hist.root C1N2_M400_390_ct2_run3_hist.root \\
    --signice "M400 #Deltam=5 c#tau=2mm" "M400 #Deltam=10 c#tau=2mm" \\
    --sel tight --sigsel matched3tk --output plots/tight/matched3tk
'''
import os
import argparse
import ROOT

ROOT.gROOT.SetBatch(ROOT.kTRUE)
ROOT.TH1.SetDefaultSumw2(True)
ROOT.gStyle.SetOptStat(0)

# (plot name, rotated variable, unrotated variable or None, signal variable, x range or None, rebin, fold)
# fold=True: contents outside the x range go into the edge bins and the visible range is normalised;
# fold=False: normalised over the full range and only zoomed (fraction of all vertices per bin).
VARIABLES = [
    ("MLScore",      "MLScore", "MLScore_before", "ParTScore", (0., 1.01),  20, True),
    ("MLScore_zoom", "MLScore", "MLScore_before", "ParTScore", (0.99, 1.0),  1, False),
    ("mass",         "mass",    "mass_before",    "mass",      (0., 20.),    1, True),
    ("pt",           "pt",      "pt_before",      "pt",        (0., 30.),    5, True),
    ("pAngle",       "pAngle",  "pAngle_before",  "pAngle",    None,         1, True),
    ("Lxy",          "Lxy",     None,             "Lxy",       (0., 10.),   10, True),
    ("LxySig",       "LxySig",  None,             "LxySig",    (0., 100.),   5, True),
    ("L_eta",        "L_eta",   None,             "L_eta",     (-3., 3.),    5, True),
]
SIGNAL_COLORS = [ROOT.kRed + 1, ROOT.kOrange + 7, ROOT.kGreen + 2, ROOT.kMagenta + 1, ROOT.kCyan + 2, ROOT.kViolet - 6,
                 ROOT.kPink + 9, ROOT.kSpring - 7]


def get_hist(fname, path):
  f = ROOT.TFile.Open(fname)
  assert f and not f.IsZombie(), "Cannot open {}".format(fname)
  h = f.Get(path)
  assert h, "Histogram {} not found in {}".format(path, fname)
  h = h.Clone("{}__{}".format(os.path.basename(fname), path.replace("/", "__")))
  h.SetDirectory(0)
  f.Close()
  return h


def same_binning(h1, h2):
  a1, a2 = h1.GetXaxis(), h2.GetXaxis()
  return h1.GetNbinsX() == h2.GetNbinsX() and a1.GetXmin() == a2.GetXmin() and a1.GetXmax() == a2.GetXmax()


def to_binning(h, ref):
  '''Return h in the binning of ref. Each bin of h must lie inside a single bin of ref.'''
  if same_binning(h, ref):
    return h
  assert h.GetBinContent(0) == 0 and h.GetBinContent(h.GetNbinsX() + 1) == 0, \
      "{}: under/overflow not empty, cannot map to another binning".format(h.GetName())
  out = ref.Clone(h.GetName() + "_rebinned")
  out.Reset()
  for b in range(1, h.GetNbinsX() + 1):
    lo, hi = h.GetXaxis().GetBinLowEdge(b), h.GetXaxis().GetBinUpEdge(b)
    eps = 1e-6 * (hi - lo)
    assert out.FindFixBin(lo + eps) == out.FindFixBin(hi - eps), \
        "{}: bin [{}, {}] straddles two bins of the target binning".format(h.GetName(), lo, hi)
    tb = out.FindFixBin(h.GetBinCenter(b))
    out.SetBinContent(tb, out.GetBinContent(tb) + h.GetBinContent(b))
    out.SetBinError(tb, (out.GetBinError(tb) ** 2 + h.GetBinError(b) ** 2) ** 0.5)
  return out


def prepare(h, xrange, rebin, fold):
  '''Rebin and restrict to xrange. fold=True: contents outside xrange are added to the edge bins
  and the visible range is normalised to unit area; fold=False: normalised over all bins
  (incl. under/overflow) and only the display range is restricted.'''
  if rebin > 1:
    h.Rebin(rebin)
  first, last = 1, h.GetNbinsX()
  if xrange is not None:
    first = h.FindFixBin(xrange[0] + 1e-9)
    last = h.FindFixBin(xrange[1] - 1e-9)
  if not fold:
    integral = h.Integral(0, h.GetNbinsX() + 1)
    if integral > 0:
      h.Scale(1. / integral)
    h.GetXaxis().SetRange(first, last)
    return h
  for edge, outside in ((first, range(0, first)), (last, range(last + 1, h.GetNbinsX() + 2))):
    content, err2 = h.GetBinContent(edge), h.GetBinError(edge) ** 2
    for b in outside:
      content += h.GetBinContent(b)
      err2 += h.GetBinError(b) ** 2
      h.SetBinContent(b, 0.)
      h.SetBinError(b, 0.)
    h.SetBinContent(edge, content)
    h.SetBinError(edge, err2 ** 0.5)
  h.GetXaxis().SetRange(first, last)
  integral = h.Integral(first, last)
  if integral > 0:
    h.Scale(1. / integral)
  return h


def draw(name, curves, xtitle, output, logy):
  c = ROOT.TCanvas("c_" + name, "", 700, 600)
  c.SetLeftMargin(0.13)
  if logy:
    c.SetLogy()
  ymax = max(h.GetMaximum() for h, _, _ in curves)
  positive = [h.GetBinContent(b) for h, _, _ in curves for b in range(h.GetXaxis().GetFirst(), h.GetXaxis().GetLast() + 1) if h.GetBinContent(b) > 0]
  ymin = min(positive) if positive else 1e-6
  legend = ROOT.TLegend(0.45, 0.62, 0.88, 0.89)
  legend.SetBorderSize(0)
  legend.SetFillStyle(0)
  for i, (h, label, opt) in enumerate(curves):
    if i == 0:
      h.SetMaximum(ymax * (30. if logy else 1.4))
      h.SetMinimum(ymin * 0.5 if logy else 0.)
      h.GetXaxis().SetTitle(xtitle)
      h.GetYaxis().SetTitle("Normalised to unit area")
      h.SetTitle("")
    h.Draw(opt if i == 0 else opt + " SAME")
    legend.AddEntry(h, label, "lep" if "PE" in opt else "l")
  legend.Draw()
  for ext in ("png", "pdf"):
    c.SaveAs(os.path.join(output, "{}{}.{}".format(name, "_log" if logy else "", ext)))


def main():
  parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument("--data", required=True, help="hist file with rotated data")
  parser.add_argument("--bkg", default="", help="hist file with rotated background MC")
  parser.add_argument("--bkglabel", default="Bkg MC (reweighted), rotated",
                      help="legend label of the background MC curve")
  parser.add_argument("--signal", nargs="+", required=True, help="signal hist files")
  parser.add_argument("--signice", nargs="+", required=True, help="legend labels of the signal files")
  parser.add_argument("--sel", required=True, help="RotateVtx selection (all, tight)")
  parser.add_argument("--sigsel", required=True, help="SDVSecVtx selection (matched, matched3tk)")
  parser.add_argument("--region", default="All", help="region prefix of the histogram directories")
  parser.add_argument("--output", required=True, help="output directory")
  args = parser.parse_args()
  assert len(args.signal) == len(args.signice), "--signal and --signice need the same length"
  os.makedirs(args.output, exist_ok=True)

  rot_dir = "{}_RotateVtx_{}/RotateVtx_".format(args.region, args.sel)
  sig_dir = "{}_SDVSecVtx_{}/SDVSecVtx_".format(args.region, args.sigsel)
  for name, rot_var, before_var, sig_var, xrange, rebin, fold in VARIABLES:
    h_data = get_hist(args.data, rot_dir + rot_var)
    h_sigs = [get_hist(f, sig_dir + sig_var) for f in args.signal]
    for h in h_sigs:
      assert same_binning(h_data, h), "{}: rotated and signal binnings differ".format(name)
    curves = []
    if before_var is not None:
      h_before = to_binning(get_hist(args.data, rot_dir + before_var), h_data)
      h_before.SetLineColor(ROOT.kGray + 2)
      h_before.SetLineStyle(2)
      h_before.SetLineWidth(2)
      curves.append((prepare(h_before, xrange, rebin, fold), "Data, unrotated", "hist"))
    if args.bkg:
      h_bkg = get_hist(args.bkg, rot_dir + rot_var)
      h_bkg.SetLineColor(ROOT.kBlue + 1)
      h_bkg.SetLineWidth(2)
      curves.append((prepare(h_bkg, xrange, rebin, fold), args.bkglabel, "hist E"))
    for i, (h, label) in enumerate(zip(h_sigs, args.signice)):
      h.SetLineColor(SIGNAL_COLORS[i % len(SIGNAL_COLORS)])
      h.SetLineWidth(2)
      curves.append((prepare(h, xrange, rebin, fold), label, "hist"))
    h_data.SetMarkerStyle(20)
    h_data.SetMarkerSize(0.8)
    h_data.SetLineColor(ROOT.kBlack)
    curves.append((prepare(h_data, xrange, rebin, fold), "Data, rotated", "PE"))
    xtitle = "{} (rotated: RotateVtx_{}, signal: SDVSecVtx_{})".format(name, rot_var, sig_var)
    for logy in (False, True):
      draw(name, curves, xtitle, args.output, logy)


if __name__ == "__main__":
  main()
