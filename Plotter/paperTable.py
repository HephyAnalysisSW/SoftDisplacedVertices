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

def addEvts(l_evt):
  output = {}
  for r in l_evt[0]:
    n = l_evt[0][r]
    for i in range(1,len(l_evt)):
      n += l_evt[i][r]
    output[r] = n

  return output

def predict_all(l_evt):
  rs = [
      'SR_evt',
      'SR_CRlowMET_evt',
      'SR_CRlowLxy_evt',
      'SR_CRlowLxylowMET_evt',
      'VR1_evt',
      'VR1_CRlowLxy_evt',
      ]
  l_predict = []
  for evt in l_evt:
    pre = {}
    for r in rs:
      pre[r] = predict(evt,r)
    l_predict.append(pre)
  return addEvts(l_predict)

def predict(devt,region):
  if 'lowLxy' in region:
    f = devts.get('VR1_CRlowLxylowMET_evt')/devts.get('VR2_CRlowLxylowMET_evt')
  else:
    f = devts.get('VR1_CRlowMET_evt')/devts.get('VR2_CRlowMET_evt')
  if 'SR' in region:
    f = f*f/(1-f)

  return devt.get('VR2'+region[region.find('_'):])*f

if __name__=="__main__":


  devts17 = getEvts("met2017_hist.root",args.SR)['nevt_sigs']
  devts18 = getEvts("met2018_hist.root",args.SR)['nevt_sigs']
  devts = addEvts([devts17,devts18])
  pred = predict_all([devts17,devts18])
  f_prompt = devts.get('VR1_CRlowLxylowMET_evt')/devts.get('VR2_CRlowLxylowMET_evt')
  f_displaced = devts.get('VR1_CRlowMET_evt')/devts.get('VR2_CRlowMET_evt')
  print("Predictions:")
  #print("Tight signal plane ($\\ngoodtrack \\geq 2$) & ${:.02fL}$ &  ${:.02fL}$ & ${:.02fL}$ & ${:.02fL}$ \\\\".format(devts.get('SR_evt'),devts.get('SR_CRlowMET_evt'),devts.get('SR_CRlowLxy_evt'),devts.get('SR_CRlowLxylowMET_evt')))
  print("Tight signal plane  & -- &  -- & -- & -- \\\\")
  print("Prediction & ${:.02fL}$ &  ${:.02fL}$ & ${:.02fL}$ & ${:.02fL}$ \\\\".format(pred['SR_evt'],pred['SR_CRlowMET_evt'],pred['SR_CRlowLxy_evt'],pred['SR_CRlowLxylowMET_evt']))
  #print("Loose signal plane ($\\ngoodtrack = 1$)     & ${:.02fL}$ &  ${:.02fL}$ & ${:.02fL}$ & ${:.02fL}$ \\\\".format(devts.get('VR1_evt'),devts.get('VR1_CRlowMET_evt'),devts.get('VR1_CRlowLxy_evt'),devts.get('VR1_CRlowLxylowMET_evt')))
  print("Loose signal plane      & -- &  ${:.0f}$ & -- & ${:.0f}$ \\\\".format(devts.get('VR1_CRlowMET_evt').n,devts.get('VR1_CRlowLxylowMET_evt').n))
  print("Prediction     & ${:.02fL}$ &  -- & ${:.02fL}$ & -- \\\\".format(pred['VR1_evt'],pred['VR1_CRlowLxy_evt']))
  print("Control plane  & ${:.0f}$ &  ${:.0f}$ & ${:.0f}$ & ${:.0f}$ \\\\".format(devts.get('VR2_evt').n,devts.get('VR2_CRlowMET_evt').n,devts.get('VR2_CRlowLxy_evt').n,devts.get('VR2_CRlowLxylowMET_evt').n))
  print("Prediction         & -- &  -- & -- & -- \\\\")

