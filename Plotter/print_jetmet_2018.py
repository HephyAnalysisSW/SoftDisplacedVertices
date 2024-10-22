# python3 print_jetmet_2018.py --input /scratch-cbe/users/alikaan.gueven/AN_plots/jetmet_histograms \ 
# --SR SRs_evt/MET_pt_corr_vs_SRsMaxLxySig VR1s_evt/MET_pt_corr_vs_VR1sMaxLxySig VR2s_evt/MET_pt_corr_vs_VR2sMaxLxySig --metcut 0

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
import pandas as pd

parser = argparse.ArgumentParser()
parser.add_argument('--input', type=str,
                        help='input dir')
parser.add_argument('--SR', type=str, nargs='+', 
                        help='Signal region')
parser.add_argument('--metcut', type=float, #nargs='+', 
                        help='MET cut')
args = parser.parse_args()


def getEvts(fn, SRnames):
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

def print_fluctuations(d, fluctuated, nominal, plane):
  print("A:    ", (d[fluctuated][plane]["A"] - d[nominal][plane]["A"]) / d[nominal][plane]["A"])
  print("B:    ", (d[fluctuated][plane]["B"] - d[nominal][plane]["B"]) / d[nominal][plane]["B"])
  print("C:    ", (d[fluctuated][plane]["C"] - d[nominal][plane]["C"]) / d[nominal][plane]["C"])
  print("D:    ", (d[fluctuated][plane]["D"] - d[nominal][plane]["D"]) / d[nominal][plane]["D"])

def makeSysUncTable(dsig_fn, subdirs, outDir=args.input):
  def df(x,y):
    """
    Assuming the measurements respcet Poissonian statistics for f=X/Y:
    Calculates the df assuming X random variable is defined as X = Y + Z, or 
                               Y random variable is defined as Y = X + Z.
    """

    if x.n>=y.n:
      df2 = (x/y).n**2 * ((x.s/x.n)**2 + (y.s/y.n)**2 -2*(y.s**2/(x*y).n))
    elif x.n<y.n:
      df2 = (x/y).n**2 * ((x.s/x.n)**2 + (y.s/y.n)**2 -2*(x.s**2/(x*y).n))
    if df2<0 and abs(df2)>1e-8:
      print("-"*60)
      print("WARNING: df squared is negative. How??")
      print("df2 = ", df2)
      print("fluctuated yield: ", x.n)
      print("nominal    yield: ", y.n)
      print("fluctuated yield [stat. unc.]: ", x.s)
      print("nominal yield    [stat. unc.]: ", y.s)
      print("Setting df2 to 0.")
      df2 = 0
      print("-"*60)
    elif df2<0 and abs(df2)<=1e-8:
      # Minimal numerical errors are okay.
      df2 = 0
    return df2**0.5
  for subdir in subdirs[1:]:
    storeDir = os.path.join(outDir, subdir)
    store = pd.HDFStore(os.path.join(storeDir, 'SysUnc.h5'), 'w')
    for sig_fn in dsig_fn.keys():
      sysUncTable_n = pd.DataFrame(columns=['A', 'B', 'C', 'D'], index=['SR', 'VR1', 'VR2'], dtype=float)
      sysUncTable_s = pd.DataFrame(columns=['A', 'B', 'C', 'D'], index=['SR', 'VR1', 'VR2'], dtype=float)
      
      fluctuated = subdir
      nominal = "jet_nom_met_smear_2018"
      
      d = dsig_fn[sig_fn]
      for plane in d[subdir].keys():
        for region in d[subdir][plane].keys():
          try:
            sysUncTable_n.loc[plane, region] = ((d[fluctuated][plane][region] - d[nominal][plane][region]) / d[nominal][plane][region]).n
          except ZeroDivisionError:
            sysUncTable_n.loc[plane, region] = 0.0
            
          try:
            sysUncTable_s.loc[plane, region] = df(d[fluctuated][plane][region], d[nominal][plane][region])
          except ZeroDivisionError:
            sysUncTable_s.loc[plane, region] = 0.0
  

      store[sig_fn + '_n'] = sysUncTable_n
      store[sig_fn + '_s'] = sysUncTable_s
    store.close()

def makeYieldTable(dsig_fn, subdirs, outDir=args.input):
  for subdir in subdirs:
    storeDir = os.path.join(outDir, subdir)
    store = pd.HDFStore(os.path.join(storeDir, 'Yields.h5'), 'w')
    for sig_fn in dsig_fn.keys():
      yieldTable    = pd.DataFrame(columns=['A', 'B', 'C', 'D'], index=['SR', 'VR1', 'VR2'], dtype=float)
      yieldUncTable = pd.DataFrame(columns=['A', 'B', 'C', 'D'], index=['SR', 'VR1', 'VR2'], dtype=float)
      
  
      d = dsig_fn[sig_fn]
      for plane in d[subdir].keys():
        for region in d[subdir][plane].keys():
          yieldTable.loc[plane, region]    = d[subdir][plane][region].n
          yieldUncTable.loc[plane, region] = d[subdir][plane][region].s
  
      store[sig_fn + '_n'] = yieldTable
      store[sig_fn + '_s'] = yieldUncTable
      # print(store[subdir])
    store.close()
    
  
if __name__=="__main__":
  sig_fns = [
    "stop_M600_575_ct0p2_2018",
    "stop_M600_580_ct2_2018",
    "stop_M600_585_ct20_2018",
    "stop_M600_588_ct200_2018",

    "stop_M1000_975_ct0p2_2018",
    "stop_M1000_980_ct2_2018",
    "stop_M1000_985_ct20_2018",
    "stop_M1000_988_ct200_2018",

    "stop_M1400_1375_ct0p2_2018",
    "stop_M1400_1380_ct2_2018",
    "stop_M1400_1385_ct20_2018",
    "stop_M1400_1388_ct200_2018",
    ]
  
  sig_fns = [sample + "_hist.root" for sample in sig_fns]
  
  # Nominal is always the first.
  # Don't touch this.
  subdirs = ["jet_nom_met_smear_2018",
             "jet_jerdown_met_smear_jerdown_2018",
             "jet_jerup_met_smear_jerup_2018",
             "jet_jesdown_met_smear_jesdown_2018",
             "jet_jesup_met_smear_jesup_2018",
             "jet_nom_met_smear_uedown_2018",
             "jet_nom_met_smear_ueup_2018",
             ]
  

  dsig_fn = {}
  print("="*40)
  for sig_fn in sig_fns:
    print("Accessing ", sig_fn)
    devt = {}
    for subdir in subdirs:
      devt[subdir] = getEvts(os.path.join(subdir, sig_fn), args.SR)

    dsig_fn[sig_fn[:-10]] = devt

  debug = False
  # Calculate systematic uncertainties
  if not debug:
    makeSysUncTable(dsig_fn, subdirs, outDir=args.input)
    makeYieldTable(dsig_fn, subdirs, outDir=args.input)
  elif debug:
    print()
    print("JER Down")
    print("."*10)

    for plane in devt[subdir].keys():
      print()
      print(plane)
      print("-"*20)
      print_fluctuations(devt, "jet_jerdown_met_smear_jerdown", "jet_nom_met_smear", plane)

    print()
    print("JER Up")
    print("."*10)

    for plane in devt[subdir].keys():
      print()
      print(plane)
      print("-"*20)
      print_fluctuations(devt, "jet_jerup_met_smear_jerup", "jet_nom_met_smear", plane)

    print()
    print("JES Up")
    print("."*10)

    for plane in devt[subdir].keys():
      print()
      print(plane)
      print("-"*20)
      print_fluctuations(devt, "jet_jesup_met_smear_jesup", "jet_nom_met_smear", plane)

    print()
    print("JES Down")
    print("."*10)

    for plane in devt[subdir].keys():
      print()
      print(plane)
      print("-"*20)
      print_fluctuations(devt, "jet_jesdown_met_smear_jesdown", "jet_nom_met_smear", plane)