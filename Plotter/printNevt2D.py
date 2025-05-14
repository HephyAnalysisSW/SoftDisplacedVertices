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

    for SRname in SRnames:
      nevt = {
          }
      nevt_sig_uncert = ctypes.c_double(0)
      fs_sig.append(ROOT.TFile.Open(os.path.join(args.input,fn)))
      hsig = fs_sig[-1].Get(SRname)
      binlow = hsig.FindBin(args.metcut)
      xcut = hsig.GetXaxis().FindBin(700)
      ycut = hsig.GetYaxis().FindBin(20)
      nevt_A_uncert = ctypes.c_double(0)
      nevt_A = hsig.IntegralAndError(xcut,1000000,ycut,1000000,nevt_A_uncert)
      nevt_A_uncert = nevt_A_uncert.value
      nevt_B_uncert = ctypes.c_double(0)
      nevt_B = hsig.IntegralAndError(0,xcut-1,ycut,1000000,nevt_B_uncert)
      nevt_B_uncert = nevt_B_uncert.value
      nevt_C_uncert = ctypes.c_double(0)
      nevt_C = hsig.IntegralAndError(xcut,1000000,0,ycut-1,nevt_C_uncert)
      nevt_C_uncert = nevt_C_uncert.value
      nevt_D_uncert = ctypes.c_double(0)
      nevt_D = hsig.IntegralAndError(0,xcut-1,0,ycut-1,nevt_D_uncert)
      nevt_D_uncert = nevt_D_uncert.value

      for r in ['A','B','C','D']:
        exec("nevt['{0}'] = ufloat(nevt_{0},nevt_{0}_uncert)".format(r))
      out_d[SRname[:SRname.find('s')]] = nevt

    return out_d

def predict(devt,plane,region):
  if region in 'CD':
    f = devts.get('VR1')['D']/devts.get('VR2')['D']
  else:
    f = devts.get('VR1')['B']/devts.get('VR2')['B']
  if 'SR' in plane:
    f = f*f/(1-f)

  return devt.get('VR2')[region]*f

if __name__=="__main__":
  sig_fns = [
      "met_2023_hist.root",
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
      ]


  for i in range(len(sig_fns)):
    devts = getEvts(sig_fns[i],args.SR)
    print("="*20)
    print(sig_fns[i])
    if 'SR' in devts:
      print("Tight signal plane ($\\ngoodtrack \\geq 2$) & ${:.02fL}$ &  ${:.02fL}$ & ${:.02fL}$ & ${:.02fL}$ \\\\".format(devts.get('SR')['A'],devts.get('SR')['B'],devts.get('SR')['C'],devts.get('SR')['D']))
    else:
      print("Tight signal plane ($\\ngoodtrack \\geq 2$) & -- &  -- & -- & -- \\\\")

    print("Loose signal plane ($\\ngoodtrack = 1$)     & ${:.02fL}$ &  ${:.02fL}$ & ${:.02fL}$ & ${:.02fL}$ \\\\".format(devts.get('VR1')['A'],devts.get('VR1')['B'],devts.get('VR1')['C'],devts.get('VR1')['D']))
    print("Control plane  ($\\ngoodtrack = 0$)         & ${:.02fL}$ &  ${:.02fL}$ & ${:.02fL}$ & ${:.02fL}$ \\\\".format(devts.get('VR2')['A'],devts.get('VR2')['B'],devts.get('VR2')['C'],devts.get('VR2')['D']))
    #print("Transfer factor 1 $\\rightarrow$ 2           & ${:.03fL}$ &  ${:.03fL}$ & ${:.03fL}$ & ${:.03fL}$ \\\\".format(devts.get('SR')['A']/devts.get('VR1')['A'],devts.get('SR')['B']/devts.get('VR1')['B'],devts.get('SR')['C']/devts.get('VR1')['C'],devts.get('SR')['D']/devts.get('VR1')['D']))
    #print("Transfer factor 0 $\\rightarrow$ 1           & ${:.03fL}$ &  ${:.03fL}$ & ${:.03fL}$ & ${:.03fL}$ \\\\".format(devts.get('VR1')['A']/devts.get('VR2')['A'],devts.get('VR1')['B']/devts.get('VR2')['B'],devts.get('VR1')['C']/devts.get('VR2')['C'],devts.get('VR1')['D']/devts.get('VR2')['D']))

    print("="*20)
    print("Predictions:")
    if 'SR' in devts:
      print("Tight signal plane ($\\ngoodtrack \\geq 2$) & ${:.02fL}$ &  ${:.02fL}$ & ${:.02fL}$ & ${:.02fL}$ \\\\".format(devts.get('SR')['A'],devts.get('SR')['B'],devts.get('SR')['C'],devts.get('SR')['D']))
    else:
      print("Tight signal plane ($\\ngoodtrack \\geq 2$) & -- &  -- & -- & -- \\\\")
    print("Prediction & ${:.02fL}$ &  ${:.02fL}$ & ${:.02fL}$ & ${:.02fL}$ \\\\".format(predict(devts,'SR','A'),predict(devts,'SR','B'),predict(devts,'SR','C'),predict(devts,'SR','D')))
    print("Loose signal plane ($\\ngoodtrack = 1$)     & ${:.02fL}$ &  ${:.02fL}$ & ${:.02fL}$ & ${:.02fL}$ \\\\".format(devts.get('VR1')['A'],devts.get('VR1')['B'],devts.get('VR1')['C'],devts.get('VR1')['D']))
    print("Prediction     & ${:.02fL}$ &  -- & ${:.02fL}$ & -- \\\\".format(predict(devts,'VR1','A'),predict(devts,'VR1','C')))
    print("Control plane  ($\\ngoodtrack = 0$)         & ${:.02fL}$ &  ${:.02fL}$ & ${:.02fL}$ & ${:.02fL}$ \\\\".format(devts.get('VR2')['A'],devts.get('VR2')['B'],devts.get('VR2')['C'],devts.get('VR2')['D']))
    print("Prediction         & -- &  -- & -- & -- \\\\")

