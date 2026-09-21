#!/usr/bin/env python3
'''Compute the PDF and QCD-scale acceptance uncertainties of a signal sample.

The plotter, run with a *_lhe.yaml config, stores the per-event LHE weights in its pkl
output (2D arrays, one row per event) and the inclusive sums of those weights in the
metadata directory of its ROOT output. This script combines the two into the acceptance

  A_k(region) = ( sum of evt_weight*w_k over the events of the region ) / ( inclusive sum of w_k )

for every variation k, and reports delta_k = A_k/A_nominal - 1. Dividing by the
inclusive sum removes the change of the total cross section, which is covered by the
theory cross-section uncertainty, and leaves the acceptance effect.

QCD scale: envelope of the six (muR,muF) points, dropping the two anti-correlated ones.
PDF: the members of these samples are symmetric-Hessian eigenvectors, so the default
combination is the quadrature sum of their displacements from member 0, with the alphaS
members added in quadrature (--pdf-combination mc68 gives the MC-replica 68% interval
instead, which only applies to a replica set).

Example:
  python3 getPDFScaleUnc.py --input /scratch/.../sig_2018 --output pdfscale_2018.json
'''
import os
import glob
import json
import argparse
import numpy as np
import ROOT

# LHEScaleWeight[i], muF varying fastest:
# 0:(muF 0.5, muR 0.5)  1:(1, 0.5)  2:(2, 0.5)  3:(0.5, 1)  4:(1, 1)  5:(2, 1)
# 6:(0.5, 2)            7:(1, 2)    8:(2, 2)
SCALE_NOMINAL_INDEX = 4
# 2 and 6 are the anti-correlated (muR, muF) combinations and are conventionally dropped
SCALE_ENVELOPE_INDICES = [0, 1, 3, 5, 7, 8]

PDF_CENTRAL_INDEX = 0
PDF_NREPLICAS = 100
# NNPDF *_pdfas sets: central + 100 members + 2 alphaS variations
PDF_SIZE_WITH_ALPHAS = 103
PDF_SIZE_WITHOUT_ALPHAS = 101

# The PDF set of a sample is the first LHA ID in the title of the LHEPdfWeight branch:
#   python3 -c "import ROOT; f=ROOT.TFile.Open('<nano>.root'); print(f.Get('Events').GetBranch('LHEPdfWeight').GetTitle())"
# and its error type is ErrorType in the set's LHAPDF .info file on cvmfs (or the
# combine= attribute of the weightgroup in the LHE header of the parent MiniAOD).
# Both PDF sets appearing in the signal NanoAODs are symmetric-Hessian sets with 103
# members (306000 NNPDF31_nnlo_hessian_pdfas, 325300 NNPDF31_nnlo_as_0118_mc_hessian_pdfas,
# both ErrorType symmhessian+as), hence the 'hessian' default below. The replica set
# 316200, for which 'mc68' would be the right prescription, is in the LHE header but is
# not the group kept in the NanoAOD.
PDF_COMBINATION_DEFAULT = 'hessian'

# the datacard signal region is cell A of the ABCD plane, see
# limitcalc/limitcalc_oop_v2/AN-25-092_make_reweighted_pkl_datacards_v2.py
DEFAULT_PLANES = ['GT1', 'GT2', 'GT3']
DEFAULT_METCUT = 500.0
DEFAULT_MLCUT = 0.999


def getInclusiveSums(histpath):
  '''Read the inclusive LHE weight sums written by the plotter into metadata/.'''
  f = ROOT.TFile.Open(histpath)
  assert f and not f.IsZombie(), "Cannot open {}!".format(histpath)
  sums = {}
  for name in ['genEventSumw', 'LHEScaleSumw', 'LHEPdfSumw']:
    h = f.Get('metadata/{}'.format(name))
    assert h, "{} has no metadata/{}. Was it produced with a *_lhe.yaml config?".format(histpath, name)
    sums[name] = np.array([h.GetBinContent(ib) for ib in range(1, h.GetNbinsX()+1)])
  f.Close()
  return sums


def getAcceptances(weights, variations, inclusive_sums):
  '''Acceptance per variation: selected yield with w_k, over the inclusive sum of w_k.'''
  assert variations.shape[1] == len(inclusive_sums), \
      "{} weights per event but {} inclusive sums!".format(variations.shape[1], len(inclusive_sums))
  selected_yields = weights.dot(variations)
  return selected_yields / inclusive_sums


def scaleUncertainty(acceptances):
  '''Envelope of the six retained (muR,muF) points, relative to the nominal one.'''
  nominal = acceptances[SCALE_NOMINAL_INDEX]
  varied = acceptances[SCALE_ENVELOPE_INDICES]
  return np.max(varied)/nominal - 1, np.min(varied)/nominal - 1


def splitPdfMembers(acceptances):
  '''Split the PDF acceptances into central value, members and alphaS variations.'''
  n = len(acceptances)
  assert n in [PDF_SIZE_WITH_ALPHAS, PDF_SIZE_WITHOUT_ALPHAS], \
      "Unexpected number of PDF weights ({}), this script assumes an NNPDF set with {} or {} members.".format(
          n, PDF_SIZE_WITHOUT_ALPHAS, PDF_SIZE_WITH_ALPHAS)
  central = acceptances[PDF_CENTRAL_INDEX]
  members = acceptances[1:1+PDF_NREPLICAS]
  alphas = acceptances[1+PDF_NREPLICAS:] if n == PDF_SIZE_WITH_ALPHAS else None
  return central, members, alphas


def pdfUncertainty(acceptances, combination):
  '''PDF uncertainty, with the alphaS variation added in quadrature on each side.

  hessian (default) is the symmetric quadrature sum of the member displacements from
  member 0, which is the prescription for the symmetric-Hessian sets these samples
  carry. mc68 orders the member acceptances and takes the central 68% interval; that is
  the MC-replica prescription and applies only to a replica set, where it is asymmetric
  by construction. Applying mc68 to a Hessian set takes the percentile of a set of
  eigenvector displacements, which has no interpretation as an interval and badly
  underestimates the uncertainty.
  '''
  central, members, alphas = splitPdfMembers(acceptances)
  if combination == 'mc68':
    low, high = np.percentile(members, [16., 84.])
    up, down = high/central - 1, low/central - 1
  else:
    spread = np.sqrt(np.sum((members-central)**2)) / central
    up, down = spread, -spread

  alphas_unc = 0.
  if alphas is not None:
    alphas_unc = (alphas[1]-alphas[0]) / (2*central)

  return {
      'pdf_up': up,
      'pdf_down': down,
      'alphas': alphas_unc,
      'total_up': np.sqrt(up**2 + alphas_unc**2),
      'total_down': -np.sqrt(down**2 + alphas_unc**2),
  }


def getRegionMask(events, metcut, mlcut):
  '''Signal-region cell of the ABCD plane.'''
  if metcut is None:
    return np.ones(len(events['evt_weight']), dtype=bool)
  return (events['MET_pt_corr'] >= metcut) & (events['leadingvtx_MLscore'] >= mlcut)


def getUncertainties(events, mask, sums, combination, reweight=None):
  weights = events['evt_weight'][mask]
  if reweight is not None:
    weights = weights * reweight[mask]
  scale_up, scale_down = scaleUncertainty(
      getAcceptances(weights, events['LHEScaleWeight'][mask], sums['LHEScaleSumw']))
  result = pdfUncertainty(
      getAcceptances(weights, events['LHEPdfWeight'][mask], sums['LHEPdfSumw']), combination)
  result['scale_up'] = scale_up
  result['scale_down'] = scale_down
  result['nevents'] = int(np.sum(mask))
  result['yield'] = float(np.sum(weights))
  return result


def getReweighter(sample_name, target_ctau, target_br):
  '''Reuse the ctau/BR reweighting of the datacard writer.

  Signal.__init__ loads the pkl files of every year, which this script does not want,
  so only the name parsing and the weight formulas are reused.
  '''
  import sys
  sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'limitcalc/limitcalc_oop_v2'))
  from datacards import Signal

  class NameOnlySignal(Signal):
    def __init__(self, sample_name):
      self.sample_name = sample_name
      self.parse_name()

  signal = NameOnlySignal(sample_name)
  return signal.reweight_to(target_ctau if target_ctau else signal.ct,
                            target_br if target_br else signal.target_br)


def formatRow(plane, unc):
  '''One line per region, all uncertainties in percent.'''
  return "  {:8s} N={:6d} yield={:10.4g}  scale {:+.2f}/{:+.2f} %  pdf {:+.2f}/{:+.2f} %  alphaS {:+.2f} %  pdf+alphaS {:+.2f}/{:+.2f} %".format(
      plane, unc['nevents'], unc['yield'],
      100*unc['scale_up'], 100*unc['scale_down'], 100*unc['pdf_up'], 100*unc['pdf_down'],
      100*unc['alphas'], 100*unc['total_up'], 100*unc['total_down'])


if __name__ == "__main__":
  parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument('--input', type=str, required=True,
                      help='directory with the merged <sample>_hist.pkl and <sample>_hist.root files')
  parser.add_argument('--postfix', type=str, default='_hist',
                      help='file name postfix of the plotter output (default: _hist)')
  parser.add_argument('--sample', type=str, nargs='+', default=[],
                      help='sample names to process (default: everything in --input)')
  parser.add_argument('--planes', type=str, nargs='+', default=DEFAULT_PLANES,
                      help='pkl regions to evaluate')
  parser.add_argument('--metcut', type=float, default=DEFAULT_METCUT,
                      help='MET_pt_corr cut of the signal region')
  parser.add_argument('--mlcut', type=float, default=DEFAULT_MLCUT,
                      help='leadingvtx_MLscore cut of the signal region')
  parser.add_argument('--whole-plane', action='store_true', default=False,
                      help='evaluate the whole plane instead of the signal-region cell')
  parser.add_argument('--pdf-combination', choices=['mc68', 'hessian'], default=PDF_COMBINATION_DEFAULT,
                      help='PDF member combination (default: %(default)s, the symmetric-Hessian '
                           'quadrature sum matching the ErrorType of these samples; mc68 is the '
                           'MC-replica 68%% interval, only valid for a replica set)')
  parser.add_argument('--reweight', action='store_true', default=False,
                      help='apply the ctau/BR reweighting of the datacard writer first')
  parser.add_argument('--target-ctau', type=float, default=0.,
                      help='target ctau in cm for --reweight (default: the generated one)')
  parser.add_argument('--target-br', type=float, default=0.,
                      help='target branching ratio for --reweight (default: the generated one)')
  parser.add_argument('--output', type=str, default='',
                      help='write the numbers to this json file')
  args = parser.parse_args()

  import pickle

  pklpaths = sorted(glob.glob(os.path.join(args.input, '*{}.pkl'.format(args.postfix))))
  if args.sample:
    pklpaths = [p for p in pklpaths
                if os.path.basename(p)[:-len('{}.pkl'.format(args.postfix))] in args.sample]
  assert pklpaths, "No {} pkl files found in {}!".format(args.postfix, args.input)

  results = {}
  for pklpath in pklpaths:
    sample = os.path.basename(pklpath)[:-len('{}.pkl'.format(args.postfix))]
    sums = getInclusiveSums(pklpath.replace('.pkl', '.root'))
    with open(pklpath, 'rb') as f:
      planes = pickle.load(f)

    reweighter = None
    if args.reweight:
      reweighter = getReweighter(sample.rsplit('_', 1)[0], args.target_ctau, args.target_br)

    print("{} (inclusive sum of gen weights {:.6g})".format(sample, sums['genEventSumw'][0]))
    results[sample] = {}
    for plane in args.planes:
      assert plane in planes, "Region {} not in {}!".format(plane, pklpath)
      events = planes[plane]
      mask = getRegionMask(events, None if args.whole_plane else args.metcut, args.mlcut)
      if np.sum(mask) == 0:
        print("  {:6s} no events, skipping".format(plane))
        continue
      reweight = reweighter.reweight(events) if reweighter is not None else None
      unc = getUncertainties(events, mask, sums, args.pdf_combination, reweight)
      results[sample][plane] = unc
      print(formatRow(plane, unc))

  if args.output:
    with open(args.output, 'w') as f:
      json.dump(results, f, indent=2)
    print("Wrote {}".format(args.output))
