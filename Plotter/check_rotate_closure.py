'''Closure: shape of reweighted bkg MC RotateVtx_mass_before vs data, per year (both normalised).'''
import ROOT
ROOT.gROOT.SetBatch(True)

NEW = "/scratch-cbe/users/ang.li/SoftDV/Histos/Histos_ParTScoreD_RotateK0_trigSF_reweight"
OLD = "/scratch-cbe/users/ang.li/SoftDV/Histos/Histos_ParTScoreD_RotateK0_trigSF"
DATA = {"2017": "met2017", "2018": "met2018", "2022pre": "jetmet_2022pre", "2022post": "jetmet_2022post",
        "2023pre": "jetmet_2023pre", "2023post": "jetmet_2023post", "2024": "jetmet_2024", "run3": "jetmet_run3"}


def get(d, f, path):
  tf = ROOT.TFile.Open("{}/{}_hist.root".format(d, f))
  h = tf.Get(path)
  h = h.Clone(f + d[-8:] + path)
  h.SetDirectory(0)
  tf.Close()
  return h


def chi2(hd, hm):
  '''shape chi2 in 1.75-2.0 between two histograms after unit normalisation; returns chi2, ndf, max |ratio-1|'''
  hd, hm = hd.Clone(), hm.Clone()
  for h in (hd, hm):
    h.Scale(1. / h.Integral(0, h.GetNbinsX() + 1))
  c, n, maxdev = 0., 0, 0.
  for b in range(hd.FindFixBin(1.7501), hd.FindFixBin(1.9999) + 1):
    d, m = hd.GetBinContent(b), hm.GetBinContent(b)
    e2 = hd.GetBinError(b) ** 2 + hm.GetBinError(b) ** 2
    if e2 > 0:
      c += (d - m) ** 2 / e2
      n += 1
    if m > 0 and d > 0:
      maxdev = max(maxdev, abs(d / m - 1))
  return c, n, maxdev


for sel in ("all", "tight"):
  path = "All_RotateVtx_{}/RotateVtx_mass_before".format(sel)
  print("\n=== {}: shape chi2/ndf (data vs MC) in 1.75-2.0 GeV, unit-normalised over all bins".format(path))
  print("{:9s} {:>22s} {:>22s}".format("year", "old (unweighted)", "new (reweighted)"))
  for y in ["2017", "2018", "2022pre", "2022post", "2023pre", "2023post", "2024", "run3"]:
    bkg = "background_{}".format(y)
    res = []
    for d in (OLD, NEW):
      try:
        res.append(chi2(get(d, DATA[y], path), get(d, bkg, path)))
      except Exception as e:
        res.append(None)
    print("{:9s} {:>22s} {:>22s}".format(
        y, *["n/a" if r is None else "{:7.1f}/{:3d} max|r-1|={:.3f}".format(*r) for r in res]))

# data must be unchanged between old and new production
print("\n=== data unchanged old vs new (All_RotateVtx_tight/RotateVtx_MLScore integral)")
for y in ["2017", "2018", "2022pre", "2022post", "2023pre", "2023post", "2024"]:
  p = "All_RotateVtx_tight/RotateVtx_MLScore"
  ho, hn = get(OLD, DATA[y], p), get(NEW, DATA[y], p)
  print("{:9s} old {:10.1f} new {:10.1f}".format(y, ho.Integral(0, ho.GetNbinsX() + 1), hn.Integral(0, hn.GetNbinsX() + 1)))
