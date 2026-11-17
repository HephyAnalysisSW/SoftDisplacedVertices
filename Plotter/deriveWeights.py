#!/usr/bin/env python3
'''Derive per-object reweighting factors from the ratio of two histograms.

The weights are the bin-by-bin ratio numerator/denominator, i.e. they reweight the
denominator distribution to match the numerator. The output ROOT file can be fed to
the plotter via the objects -> <obj> -> custom_weights config block:

  objects:
    SDVSecVtx:
      custom_weights:
        - file: weights_Lxy.root
          hist: w_SDVSecVtx_Lxy
          var: SDVSecVtx_Lxy

Example:
  python3 deriveWeights.py \
    --numerator data_hist.root:SR_SDVSecVtx_all/SDVSecVtx_Lxy \
    --denominator mc_hist.root:SR_SDVSecVtx_all/SDVSecVtx_Lxy \
    --name w_SDVSecVtx_Lxy --normalize \
    --output weights_Lxy.root
'''
import os
import math
import argparse
from array import array
import ROOT

ROOT.gROOT.SetBatch(ROOT.kTRUE)
ROOT.TH1.SetDefaultSumw2(True)


def getHist(spec):
  '''Load a histogram from a "file.root:path/to/hist" specification.'''
  assert ':' in spec, "Histogram specification '{}' must be file.root:path/to/hist".format(spec)
  path, histname = spec.rsplit(':', 1)
  assert os.path.exists(path), "File {} does not exist!".format(path)
  f = ROOT.TFile.Open(path)
  h = f.Get(histname)
  assert h, "Histogram {} not found in {}!".format(histname, path)
  h.SetDirectory(0)
  f.Close()
  return h


def regroup(h, edges, name):
  '''Return h regrouped into variable bins with the given edges.

  Every edge inside the axis range of h must coincide with a bin edge of h. If the last
  (first) edge lies above (below) the axis range, the overflow (underflow) of h is added to
  the last (first) new bin, so that e.g. edges ending in 1000 for an axis ending at 10 put
  everything above 10 into the last bin. Content outside the new edges goes to the
  under/overflow of the result (ignored by the normalisation, as without --edges).
  '''
  ax = h.GetXaxis()
  low_edges = [ax.GetBinLowEdge(b) for b in range(1, ax.GetNbins() + 2)]
  tol = 1e-6 * (ax.GetXmax() - ax.GetXmin()) / ax.GetNbins()
  for e in edges:
    if ax.GetXmin() < e < ax.GetXmax():
      assert min(abs(le - e) for le in low_edges) < tol, \
          "Edge {} is not a bin edge of {}!".format(e, h.GetName())
  out = ROOT.TH1D(name, h.GetTitle(), len(edges) - 1, array('d', edges))
  out.SetDirectory(0)
  out.GetXaxis().SetTitle(ax.GetTitle())
  for b in range(0, ax.GetNbins() + 2):
    if b == 0:
      if edges[0] >= ax.GetXmin():
        continue
      target = 1
    elif b == ax.GetNbins() + 1:
      if edges[-1] <= ax.GetXmax():
        continue
      target = out.GetNbinsX()
    else:
      target = out.FindFixBin(ax.GetBinCenter(b))
    out.SetBinContent(target, out.GetBinContent(target) + h.GetBinContent(b))
    out.SetBinError(target, math.hypot(out.GetBinError(target), h.GetBinError(b)))
  return out


def deriveWeights(h_num, h_den, normalize, rebin, default_weight, edges=None):
  assert h_num.GetNbinsX() == h_den.GetNbinsX(), \
      "Binning mismatch: numerator has {} bins, denominator has {}!".format(h_num.GetNbinsX(), h_den.GetNbinsX())
  if edges:
    assert rebin == 1, "--edges and --rebin cannot be combined!"
    assert all(lo < hi for lo, hi in zip(edges[:-1], edges[1:])), "--edges must be increasing!"
    h_num = regroup(h_num, edges, "numerator_regrouped")
    h_den = regroup(h_den, edges, "denominator_regrouped")
  if rebin > 1:
    h_num.Rebin(rebin)
    h_den.Rebin(rebin)
  if normalize:
    assert h_num.Integral() > 0 and h_den.Integral() > 0, "Cannot normalize a histogram with zero integral!"
    h_num.Scale(1. / h_num.Integral())
    h_den.Scale(1. / h_den.Integral())
  h_weight = h_num.Clone()
  h_weight.Divide(h_den)
  for ib in range(1, h_weight.GetNbinsX() + 1):
    if h_den.GetBinContent(ib) == 0:
      h_weight.SetBinContent(ib, default_weight)
      h_weight.SetBinError(ib, 0.)
  return h_weight


if __name__ == "__main__":
  parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument('--numerator', type=str, required=True,
                      help='target histogram, as file.root:path/to/hist')
  parser.add_argument('--denominator', type=str, required=True,
                      help='histogram to be reweighted, as file.root:path/to/hist')
  parser.add_argument('--output', type=str, required=True,
                      help='output ROOT file (updated in place, so several weights can share one file)')
  parser.add_argument('--name', type=str, default='',
                      help='name of the weight histogram (default: w_<numerator hist name>)')
  parser.add_argument('--normalize', action='store_true', default=False,
                      help='normalize both histograms to unit area first (shape-only weights)')
  parser.add_argument('--rebin', type=int, default=1,
                      help='rebin both histograms by this factor before taking the ratio')
  parser.add_argument('--default-weight', type=float, default=1.,
                      help='weight assigned to bins with an empty denominator')
  parser.add_argument('--edges', type=float, nargs='+', default=None,
                      help='regroup both histograms into variable bins with these edges before taking the '
                           'ratio (edges inside the axis range must be existing bin edges; a last edge above '
                           'the axis range folds the overflow into the last bin)')
  args = parser.parse_args()

  h_num = getHist(args.numerator)
  h_den = getHist(args.denominator)
  h_weight = deriveWeights(h_num, h_den, args.normalize, args.rebin, args.default_weight, args.edges)
  name = args.name if args.name else 'w_{}'.format(h_num.GetName())
  h_weight.SetName(name)
  h_weight.SetTitle(';{};weight'.format(h_num.GetXaxis().GetTitle()))

  fout = ROOT.TFile(args.output, "UPDATE")
  h_weight.Write(name, ROOT.TObject.kOverwrite)
  fout.Close()
  print("Wrote weight '{}' to {}".format(name, args.output))
