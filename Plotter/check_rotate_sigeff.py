'''Score fractions for signal vertices and rotated D candidates (Run 3 totals).'''
import ROOT
ROOT.gROOT.SetBatch(True)

S = "/scratch-cbe/users/ang.li/SoftDV/Histos/Histos_C1N2Run3_RotateSignal"
R = "/scratch-cbe/users/ang.li/SoftDV/Histos/Histos_ParTScoreD_RotateK0_trigSF_reweight"


def fractions(fname, path):
  f = ROOT.TFile.Open(fname)
  h = f.Get(path)
  n = h.GetNbinsX()
  tot = h.Integral(0, n + 1)
  n08 = h.Integral(h.FindBin(0.8), n + 1)
  n0999 = h.Integral(h.FindBin(0.999), n + 1)
  f.Close()
  return tot, n08 / tot, n0999 / tot, n0999 / n08


print("{:32s} {:>10s} {:>10s} {:>10s} {:>16s}".format("sample / selection", "N", "f(>0.8)", "f(>0.999)", "N>0.999/N>0.8"))
for sel in ("all", "tight"):
  for name in ("jetmet_run3", "background_run3"):
    r = fractions("{}/{}_hist.root".format(R, name), "All_RotateVtx_{}/RotateVtx_MLScore".format(sel))
    print("{:32s} {:10.0f} {:10.3f} {:10.4f} {:16.4f}".format("rot {} {}".format(name, sel), *r))
for sigsel in ("matched", "matched3tk"):
  for m2 in (395, 390, 380):
    for ct in (2, 20):
      p = "C1N2_M400_{}_ct{}".format(m2, ct)
      r = fractions("{}/{}_run3_hist.root".format(S, p), "All_SDVSecVtx_{}/SDVSecVtx_ParTScore".format(sigsel))
      print("{:32s} {:10.0f} {:10.3f} {:10.4f} {:16.4f}".format("{} {}".format(p.replace("C1N2_M400_", "M400_"), sigsel), *r))
