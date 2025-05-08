import os
import ROOT
import SoftDisplacedVertices.Samples.Samples as s
ROOT.EnableImplicitMT(4)
ROOT.gROOT.SetBatch(ROOT.kTRUE)
ROOT.TH1.SetDefaultSumw2(True)
ROOT.gStyle.SetOptStat(0)

import argparse

def plot2D(h,name):
  c = ROOT.TCanvas("c","c",800,800)
  pfx = h.ProfileX()
  h.Draw('colz')
  pfx.SetLineWidth(2)
  pfx.SetLineColor(ROOT.kRed)
  pfx.Draw("same")
  c.SetLogz()
  c.SaveAs(args.output+'/'+name+'.png')


parser = argparse.ArgumentParser()
parser.add_argument('--input', type=str, 
                    help='files to compare')
parser.add_argument('--output', type=str,
                    help='output dir')
parser.add_argument('--dirs', type=str, nargs='+',
                    help='directories to compare')
parser.add_argument('--nice', type=str, nargs='+',
                    help='legend names')
parser.add_argument('--commands', type=str, nargs='+',
                    help="Additional commands, such as rebinning or set range etc.")
args = parser.parse_args()
if __name__ == "__main__":
  if not os.path.exists(args.output):
    os.makedirs(args.output)
  f = ROOT.TFile.Open(args.input)
  for n in ['SDVTrack_dphi_jet0_vs_SDVTrack_pfAbsIso03_all','SDVTrack_dphi_jet0_vs_SDVTrack_pfAbsIso03_chg','SDVTrack_dphi_jet0_vs_SDVTrack_pfRelIso03_all','SDVTrack_dphi_jet0_vs_SDVTrack_pfRelIso03_chg','SDVTrack_dR_jet0_vs_SDVTrack_pfAbsIso03_all','SDVTrack_dR_jet0_vs_SDVTrack_pfAbsIso03_chg','SDVTrack_dR_jet0_vs_SDVTrack_pfRelIso03_all','SDVTrack_dR_jet0_vs_SDVTrack_pfRelIso03_chg']:
    for d in args.dirs:
      h = f.Get(d+'/'+n)
      if not h:
        print("{} not found!".format(d+'/'+n))
      plot2D(h,d+'_'+n)
