import os
import uuid
import shutil
import itertools
import ctypes
import subprocess
from uncertainties import ufloat
import math
import ROOT
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import matplotlib as mpl
import SoftDisplacedVertices.Plotter.plotter as p
import SoftDisplacedVertices.Plotter.plot_setting as ps
import SoftDisplacedVertices.Samples.Samples as s
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--input', type=str,
                        help='input dir')
parser.add_argument('--inputHEM', type=str,
                        help='input dir with HEM veto')
parser.add_argument('--SR', type=str, nargs='+', 
                        help='Signal region')
parser.add_argument('--metcut', type=float, #nargs='+', 
                        help='MET cut')
args = parser.parse_args()

def dict_product(dicts):
    return (dict(zip(dicts, x)) for x in itertools.product(*dicts.values()))

def getbErr(b,uncert,l,syst):
  # Poisson statistical uncertainty
  # Pearson’s chi2 intervals
  b_low = math.sqrt(b*l+l*l/4)-l/2
  b_high = math.sqrt(b*l+l*l/4)+l/2
  b_stat = max(abs(b_high),(b_low))/b
  b_syst2 = syst*syst + (uncert/b)*(uncert/b)
  #return b*math.sqrt(b_stat*b_stat + b_syst*b_syst)
  return b*math.sqrt(b_syst2)

def sig(s,b,b_err):
  return math.sqrt(2*((s+b)*math.log(((s+b)*(b+b_err*b_err))/(b*b+(s+b)*b_err*b_err)) - (b*b/(b_err*b_err))*math.log(1+(b_err*b_err*s)/(b*(b+b_err*b_err)))))

def getEvts(fn,SRnames):
    out_d = {}
    fs_sig = []
    nevt_sigs = {}
    nevt_uncert_sigs = {}
    for SRname in SRnames:
      SRname_full = "{}/MET_pt".format(SRname)
      nevt_sig_uncert = ctypes.c_double(0)
      fs_sig.append(ROOT.TFile.Open(os.path.join(args.input,fn)))
      hsig = fs_sig[-1].Get(SRname_full)
      binlow = hsig.FindBin(args.metcut)
      nevt_sig = hsig.IntegralAndError(binlow,1000000,nevt_sig_uncert)
      nevt_sig_uncert = nevt_sig_uncert.value
      nevt_sigs[SRname] = ufloat(nevt_sig, nevt_sig_uncert)
      nevt_uncert_sigs[SRname] = nevt_sig_uncert

    out_d['nevt_sigs'] = nevt_sigs
    out_d['nevt_uncert_sigs'] = nevt_uncert_sigs

    return out_d

def getEvtsHEM(fn,SRnames):
    out_d = {}
    fs_sig = []
    nevt_sigs = {}
    nevt_uncert_sigs = {}
    for SRname in SRnames:
      SRname_full = "{}/MET_pt".format(SRname)
      nevt_sig_uncert = ctypes.c_double(0)
      fs_sig.append(ROOT.TFile.Open(os.path.join(args.inputHEM,fn)))
      hsig = fs_sig[-1].Get(SRname_full)
      binlow = hsig.FindBin(args.metcut)
      nevt_sig = hsig.IntegralAndError(binlow,1000000,nevt_sig_uncert)
      nevt_sig_uncert = nevt_sig_uncert.value
      nevt_sigs[SRname] = ufloat(nevt_sig, nevt_sig_uncert)
      nevt_uncert_sigs[SRname] = nevt_sig_uncert

    out_d['nevt_sigs'] = nevt_sigs
    out_d['nevt_uncert_sigs'] = nevt_uncert_sigs

    return out_d

def getEvts_total(fn,SRnames,HEM):
  if not HEM:
    return getEvts(fn,SRnames)
  fHEM = 0.6477
  evt = getEvts(fn,SRnames)
  evtHEM = getEvtsHEM(fn,SRnames)
  out_d = {}
  nevt_sigs = {}
  nevt_uncert_sigs = {}
  for r in SRnames:
    nevt = evt['nevt_sigs'][r].n
    nevtHEM = evtHEM['nevt_sigs'][r].n
    f = (nevt*(1-fHEM)+nevtHEM*fHEM)/nevt
    nevt_final = evt['nevt_sigs'][r]*f
    nevt_sigs[r] = nevt_final
    nevt_uncert_sigs[r] = nevt_final.s

  out_d['nevt_sigs'] = nevt_sigs
  out_d['nevt_uncert_sigs'] = nevt_uncert_sigs

  return out_d
  

def predict(devt,region):
  if 'lowLxy' in region:
    f = devts.get('VR1_CRlowLxylowMET_evt')/devts.get('VR2_CRlowLxylowMET_evt')
  else:
    f = devts.get('VR1_CRlowMET_evt')/devts.get('VR2_CRlowMET_evt')
  if 'SR' in region:
    f = f*f/(1-f)

  return devt.get('VR2'+region[region.find('_'):])*f

if __name__=="__main__":
  sig_fns = [
      "met2017_hist.root",
      "met2018_hist.root",
      #"background_2017_hist.root",
      #"background_2018_hist.root",
      #"stop_M600_575_ct0p2_2018_hist.root",
      #"stop_M600_580_ct2_2018_hist.root",
      #"stop_M600_585_ct20_2018_hist.root",
      #"stop_M600_588_ct200_2018_hist.root",
      #"stop_M1000_975_ct0p2_2018_hist.root",
      #"stop_M1000_980_ct2_2018_hist.root",
      #"stop_M1000_985_ct20_2018_hist.root",
      #"stop_M1000_988_ct200_2018_hist.root",
      #"stop_M1400_1375_ct0p2_2018_hist.root",
      #"stop_M1400_1380_ct2_2018_hist.root",
      #"stop_M1400_1385_ct20_2018_hist.root",
      #"stop_M1400_1388_ct200_2018_hist.root",
      #"stop_M600_575_ct0p2_2017_hist.root",
      #"stop_M600_580_ct2_2017_hist.root",
      #"stop_M600_585_ct20_2017_hist.root",
      #"stop_M600_588_ct200_2017_hist.root",
      #"stop_M1000_975_ct0p2_2017_hist.root",
      #"stop_M1000_980_ct2_2017_hist.root",
      #"stop_M1000_985_ct20_2017_hist.root",
      #"stop_M1000_988_ct200_2017_hist.root",
      #"stop_M1400_1375_ct0p2_2017_hist.root",
      #"stop_M1400_1380_ct2_2017_hist.root",
      #"stop_M1400_1385_ct20_2017_hist.root",
      #"stop_M1400_1388_ct200_2017_hist.root",
      ]

  #sig_fns = []
  #for fn in os.listdir(args.input):
  #  if '.root' in fn:
  #    sig_fns.append(fn)

  HEM = False
  if args.inputHEM is not None:
    HEM = True

  for i in range(len(sig_fns)):
    devts = getEvts_total(sig_fns[i],args.SR,HEM)['nevt_sigs']
    #print(sig_fns[i])
    #print("="*20)
    #print("\\multirow{{3}}{{*}}{{{}}} & Tight signal plane & ${:.02fL}$ &  ${:.02fL}$ & ${:.02fL}$ & ${:.02fL}$ \\\\".format(sig_fns[i].replace('_2017_hist.root','').replace('_2018_hist.root','').replace('_','\\_'),devts.get('SR_evt'),devts.get('SR_CRlowMET_evt'),devts.get('SR_CRlowLxy_evt'),devts.get('SR_CRlowLxylowMET_evt')))
    #print("&Loose signal plane     & ${:.02fL}$ &  ${:.02fL}$ & ${:.02fL}$ & ${:.02fL}$ \\\\".format(devts.get('VR1_evt'),devts.get('VR1_CRlowMET_evt'),devts.get('VR1_CRlowLxy_evt'),devts.get('VR1_CRlowLxylowMET_evt')))
    #print("&Control plane        & ${:.02fL}$ &  ${:.02fL}$ & ${:.02fL}$ & ${:.02fL}$ \\\\".format(devts.get('VR2_evt'),devts.get('VR2_CRlowMET_evt'),devts.get('VR2_CRlowLxy_evt'),devts.get('VR2_CRlowLxylowMET_evt')))
    #print("\\hline")
    #print("Transfer factor 1 $\\rightarrow$ 2           & ${:.03fL}$ &  ${:.03fL}$ & ${:.03fL}$ & ${:.03fL}$ \\\\".format(devts.get('SR_evt')/devts.get('VR1_evt'),devts.get('SR_CRlowMET_evt')/devts.get('VR1_CRlowMET_evt'),devts.get('SR_CRlowLxy_evt')/devts.get('VR1_CRlowLxy_evt'),devts.get('SR_CRlowLxylowMET_evt')/devts.get('VR1_CRlowLxylowMET_evt')))
    #print("Transfer factor 0 $\\rightarrow$ 1           & ${:.03fL}$ &  ${:.03fL}$ & ${:.03fL}$ & ${:.03fL}$ \\\\".format(devts.get('VR1_evt')/devts.get('VR2_evt'),devts.get('VR1_CRlowMET_evt')/devts.get('VR2_CRlowMET_evt'),devts.get('VR1_CRlowLxy_evt')/devts.get('VR2_CRlowLxy_evt'),devts.get('VR1_CRlowLxylowMET_evt')/devts.get('VR2_CRlowLxylowMET_evt')))

    print("="*20)
    f_prompt = devts.get('VR1_CRlowLxylowMET_evt')/devts.get('VR2_CRlowLxylowMET_evt')
    f_displaced = devts.get('VR1_CRlowMET_evt')/devts.get('VR2_CRlowMET_evt')
    print("Predictions:")
    #print("Tight signal plane ($\\ngoodtrack \\geq 2$) & ${:.02fL}$ &  ${:.02fL}$ & ${:.02fL}$ & ${:.02fL}$ \\\\".format(devts.get('SR_evt'),devts.get('SR_CRlowMET_evt'),devts.get('SR_CRlowLxy_evt'),devts.get('SR_CRlowLxylowMET_evt')))
    print("Tight signal plane ($\\ngoodtrack \\geq 2$) & -- &  -- & -- & -- \\\\")
    print("Prediction & ${:.02fL}$ &  ${:.02fL}$ & ${:.02fL}$ & ${:.02fL}$ \\\\".format(predict(devts,'SR_evt'),predict(devts,'SR_CRlowMET_evt'),predict(devts,'SR_CRlowLxy_evt'),predict(devts,'SR_CRlowLxylowMET_evt')))
    #print("Loose signal plane ($\\ngoodtrack = 1$)     & ${:.02fL}$ &  ${:.02fL}$ & ${:.02fL}$ & ${:.02fL}$ \\\\".format(devts.get('VR1_evt'),devts.get('VR1_CRlowMET_evt'),devts.get('VR1_CRlowLxy_evt'),devts.get('VR1_CRlowLxylowMET_evt')))
    print("Loose signal plane ($\\ngoodtrack = 1$)     & -- &  ${:.02fL}$ & -- & ${:.02fL}$ \\\\".format(devts.get('VR1_CRlowMET_evt'),devts.get('VR1_CRlowLxylowMET_evt')))
    print("Prediction     & ${:.02fL}$ &  -- & ${:.02fL}$ & -- \\\\".format(predict(devts,'VR1_evt'),predict(devts,'VR1_CRlowLxy_evt')))
    print("Control plane  ($\\ngoodtrack = 0$)         & ${:.02fL}$ &  ${:.02fL}$ & ${:.02fL}$ & ${:.02fL}$ \\\\".format(devts.get('VR2_evt'),devts.get('VR2_CRlowMET_evt'),devts.get('VR2_CRlowLxy_evt'),devts.get('VR2_CRlowLxylowMET_evt')))
    print("Prediction         & -- &  -- & -- & -- \\\\")

