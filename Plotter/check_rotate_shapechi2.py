'''Shape chi2 (TH1::Chi2Test "WW NORM CHI2/NDF") data vs bkg MC, old (unweighted) vs new (D-mass reweighted).'''
import ctypes
import ROOT
ROOT.gROOT.SetBatch(True)
ROOT.gErrorIgnoreLevel = ROOT.kError

NEW = "/scratch-cbe/users/ang.li/SoftDV/Histos/Histos_ParTScoreD_RotateK0_trigSF_reweight"
OLD = "/scratch-cbe/users/ang.li/SoftDV/Histos/Histos_ParTScoreD_RotateK0_trigSF"
GROUPS = {"Run2": [("met2017", "background_2017"), ("met2018", "background_2018")],
          "Run3": [("jetmet_" + y, "background_" + y) for y in ["2022pre", "2022post", "2023pre", "2023post", "2024"]]}
# variable, rebin
VARS = [("MLScore", 20), ("MLScore_before", 20), ("mass", 1), ("mass_before", 1), ("pt", 10), ("pt_before", 10),
        ("pAngle", 2), ("pAngle_before", 2), ("Lxy", 20), ("LxySig", 10), ("L_eta", 4)]


def summed(d, names, path):
  tot = None
  for n in names:
    f = ROOT.TFile.Open("{}/{}_hist.root".format(d, n))
    h = f.Get(path)
    if not h:
      f.Close()
      return None
    h = h.Clone()
    h.SetDirectory(0)
    f.Close()
    if tot is None:
      tot = h
    else:
      tot.Add(h)
  return tot


for sel in ("all", "tight"):
  print("\n=== All_RotateVtx_{}: chi2/ndf of data vs bkg MC shapes".format(sel))
  print("{:16s} {:>14s} {:>14s} {:>14s} {:>14s}".format("variable", "Run2 old", "Run2 new", "Run3 old", "Run3 new"))
  for var, rebin in VARS:
    path = "All_RotateVtx_{}/RotateVtx_{}".format(sel, var)
    cells = []
    for g in ("Run2", "Run3"):
      for d in (OLD, NEW):
        hd = summed(d, [p[0] for p in GROUPS[g]], path)
        hm = summed(d, [p[1] for p in GROUPS[g]], path)
        if hd is None or hm is None:
          cells.append("n/a")
          continue
        hd.Rebin(rebin)
        hm.Rebin(rebin)
        # "UW": data are plain counts, MC is weighted; the test compares shapes only
        c, ndf, igood = ctypes.c_double(0), ctypes.c_int(0), ctypes.c_int(0)
        p = hd.Chi2TestX(hm, c, ndf, igood, "UW")
        cells.append("{:6.1f}/{:<4d}".format(c.value, ndf.value))
    print("{:16s} {:>14s} {:>14s} {:>14s} {:>14s}".format(var, *cells))
