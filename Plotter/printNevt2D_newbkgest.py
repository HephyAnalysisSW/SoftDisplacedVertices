# python3 ../printNevt2D_newbkgest.py --input /scratch-cbe/users/alikaan.gueven/AN_plots/checks_2023/val_yields_v2/data --SR TP_evt/MET_pt_corr_vs_TP_MaxLxySig MP_evt/MET_pt_corr_vs_MP_MaxLxySig LP_evt/MET_pt_corr_vs_LP_MaxLxySig CP_evt/MET_pt_corr_vs_CP_MaxLxySig --metcut 0

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
parser.add_argument('--blind', action='store_true',
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
      binlow = hsig.GetXaxis().FindBin(args.metcut)
      xcut = hsig.GetXaxis().FindBin(700)
      #xcut = hsig.GetXaxis().FindBin(375)
      ycut = hsig.GetYaxis().FindBin(20)
      nevt_A_uncert = ctypes.c_double(0)
      nevt_A = hsig.IntegralAndError(xcut,1000000,ycut,1000000,nevt_A_uncert)
      nevt_A_uncert = nevt_A_uncert.value
      nevt_B_uncert = ctypes.c_double(0)
      nevt_B = hsig.IntegralAndError(binlow,xcut-1,ycut,1000000,nevt_B_uncert)
      nevt_B_uncert = nevt_B_uncert.value
      nevt_C_uncert = ctypes.c_double(0)
      nevt_C = hsig.IntegralAndError(xcut,1000000,0,ycut-1,nevt_C_uncert)
      nevt_C_uncert = nevt_C_uncert.value
      nevt_D_uncert = ctypes.c_double(0)
      nevt_D = hsig.IntegralAndError(binlow,xcut-1,0,ycut-1,nevt_D_uncert)
      nevt_D_uncert = nevt_D_uncert.value

      for r in ['A','B','C','D']:
        exec("nevt['{0}'] = ufloat(nevt_{0},nevt_{0}_uncert)".format(r))
      namedict = {
          'CP': 'VR2',
          'LP': 'VR1',
          'TP': 'SRg2tk',
          'MP': 'SR2tk',
          'SRs': 'SR',
          }
      for k in namedict:
        if k in SRname:
          SRname_new = namedict[k]
          break
      out_d[SRname_new] = nevt

    return out_d

def predict_full_old(devt, year):
  flxysig = {
      "2017":{
        "VR2": ufloat(0.1696,0.0007),
        "VR1": ufloat(0.3076,0.0020),
        "SR2tk": ufloat(0.410,0.005),
        "SRg2tk": ufloat(0.475,0.016),
        },
      "2018":{
        "VR2": ufloat(0.1634,0.0005),
        "VR1": ufloat(0.3002,0.0017),
        "SR2tk": ufloat(0.402,0.004),
        "SRg2tk": ufloat(0.446,0.013),
        },
      }
  devt_pred = {}
  f = (devt['VR1']['B']+devt['VR1']['D'])/(devt['VR2']['B']+devt['VR2']['D'])
  nevt_lowMET = {}
  nevt_lowMET['SR2tk'] = (devt['VR2']['B']+devt['VR2']['D'])*f*f
  nevt_lowMET['SRg2tk'] = (devt['VR2']['B']+devt['VR2']['D'])*f*f*f/(1-f)
  nevt_highMET = {}
  nevt_highMET['VR1'] = (devt['VR2']['A']+devt['VR2']['C'])*f
  nevt_highMET['SR2tk'] = (devt['VR2']['A']+devt['VR2']['C'])*f*f
  nevt_highMET['SRg2tk'] = (devt['VR2']['A']+devt['VR2']['C'])*f*f*f/(1-f)
  for p in ['VR1', 'SR2tk', 'SRg2tk']:
    if p not in devt_pred:
      devt_pred[p] = {}
    devt_pred[p]['A'] = nevt_highMET[p] * flxysig[year][p]
    devt_pred[p]['C'] = nevt_highMET[p] * (1-flxysig[year][p])
  for p in ['SR2tk', 'SRg2tk']:
    devt_pred[p]['B'] = nevt_lowMET[p] * flxysig[year][p]
    devt_pred[p]['D'] = nevt_lowMET[p] * (1-flxysig[year][p])

  return devt_pred

def predict_full(devt, year):
  flxysig = {
      "2017":{
        "VR2": ufloat(0.1696,0.0007),
        "VR1": ufloat(0.3076,0.0020),
        "SR2tk": ufloat(0.410,0.005),
        "SRg2tk": ufloat(0.475,0.016),
        },
      "2018":{
        "VR2": ufloat(0.1634,0.0005),
        "VR1": ufloat(0.3002,0.0017),
        "SR2tk": ufloat(0.402,0.004),
        "SRg2tk": ufloat(0.446,0.013),
        },
      }
  f_template = {
      # for SRs
#       "2017":[ufloat(0.2739625323155715,0.0020679193640467984),ufloat(0.12491055456171735,0.0025068171917859666),ufloat(0.10132474042248478,0.006320915430064782)],
#       "2018":[ufloat(0.24506216861492666,0.001537914056888967),ufloat(0.12323654077307522,0.002092500819829968),ufloat(0.09984599589322382,0.005309110829516144)]
      # for VRs
      "2017":[ufloat(0.13285279780009165,0.001119882408262738),ufloat(0.08988270714420121,0.002478808233462371),ufloat(0.0942079553384508,0.008481460187598525)],
      "2018":[ufloat(0.13410967262889364,0.001057429455682389),ufloat(0.09346562876877536,0.002366967574060018),ufloat(0.09853372434017596,0.007967773035127754)]
      # for SRs in lowMET regions
      #"2017":[ufloat(0.2432649431179515,0.0019328333229164032),ufloat(0.12501269422159034,0.0026723220930593436),ufloat(0.10276198212835093,0.006784425919156141)],
      #"2018":[ufloat(0.24607038408185264,0.0016459552913450505),ufloat(0.12362657091561939,0.0022333372630241035),ufloat(0.10252686610514086,0.0057298720022788035)]


      #"2017":[ufloat(0.11564880657392787,0.0008622675482771354),ufloat(0.1391698639693059,0.0028106319487075804),ufloat(0.10132474042248478,0.006320915430064782)],
      #"2018":[ufloat(0.11672617311391638,0.0006937482016627025),ufloat(0.12323654077307522,0.002092500819829968),ufloat(0.09984599589322382,0.005309110829516144)]
      }
  devt_pred = {}
  f_base = (devt['VR1']['B']+devt['VR1']['D'])/(devt['VR2']['B']+devt['VR2']['D'])
  scale_f = f_base/f_template[year][0]
  fs = [f_template[year][i]*(f_base/f_template[year][0]) for i in range(len(f_template[year]))]
  nevt_lowMET = {}
  nevt_lowMET['SR2tk'] = (devt['VR2']['B']+devt['VR2']['D'])*fs[0]*fs[1]
  nevt_lowMET['SRg2tk'] = (devt['VR2']['B']+devt['VR2']['D'])*fs[0]*fs[1]*fs[2]
  nevt_highMET = {}
  nevt_highMET['VR1'] = (devt['VR2']['A']+devt['VR2']['C'])*fs[0]
  nevt_highMET['SR2tk'] = (devt['VR2']['A']+devt['VR2']['C'])*fs[0]*fs[1]
  nevt_highMET['SRg2tk'] = (devt['VR2']['A']+devt['VR2']['C'])*fs[0]*fs[1]*fs[2]
  for p in ['VR1', 'SR2tk', 'SRg2tk']:
    if p not in devt_pred:
      devt_pred[p] = {}
    devt_pred[p]['A'] = nevt_highMET[p] * flxysig[year][p]
    devt_pred[p]['C'] = nevt_highMET[p] * (1-flxysig[year][p])
  for p in ['SR2tk', 'SRg2tk']:
    devt_pred[p]['B'] = nevt_lowMET[p] * flxysig[year][p]
    devt_pred[p]['D'] = nevt_lowMET[p] * (1-flxysig[year][p])

  return devt_pred

def predict(devt,plane,region):
  if region in 'CD':
    f = devts.get('VR1')['D']/devts.get('VR2')['D']
  else:
    f = devts.get('VR1')['B']/devts.get('VR2')['B']
  if 'SR' in plane:
    f = f*f/(1-f)
    #f = f*f
    #f = f*f*f/(1-f)

  return devt.get('VR2')[region]*f

if __name__=="__main__":
  sig_fns = [
      #"met2017_hist.root",
      #"met2018_hist.root",
      "met_2023_hist.root",
      #"background_2017_hist.root",
      #"background_2018_hist.root",
      #"stop_M600_575_ct0p2_2018_hist.root",
      #"stop_M600_580_ct2_2018_hist.root",
      # "stop_M600_585_ct20_2017_hist.root",
      # "stop_M600_585_ct20_2018_hist.root",
      #"stop_M600_588_ct200_2018_hist.root",
      #"stop_M1000_975_ct0p2_2018_hist.root",
      #"stop_M1000_980_ct2_2018_hist.root",
      # "stop_M1000_985_ct20_2017_hist.root",
      # "stop_M1000_985_ct20_2018_hist.root",
      #"stop_M1000_988_ct200_2018_hist.root",
      #"stop_M1400_1375_ct0p2_2018_hist.root",
      #"stop_M1400_1380_ct2_2018_hist.root",
      #"stop_M1400_1385_ct20_2018_hist.root",
      #"stop_M1400_1388_ct200_2018_hist.root",
      #"qcd_2018_hist.root",
      #"st_2018_hist.root",
      #"ttbar_2018_hist.root",
      #"wjets_2018_hist.root",
      #"zjets_2018_hist.root",
      ]

  for i in range(len(sig_fns)):
    devts = getEvts(sig_fns[i],args.SR)
    year = ''
    if '2017' in sig_fns[i]:
      year = '2017'
    elif '2018' in sig_fns[i]:
      year = '2018'
    else:
      year = '2017'
    devts_pred = predict_full(devts, year)
    ### Print TFs
    #print("="*20)
    #print(sig_fns[i])
    #if 'SR' in devts:
    #  print("Tight signal plane ($\\ngoodtrack \\geq 2$) & ${:.02fL}$ &  ${:.02fL}$ & ${:.02fL}$ & ${:.02fL}$ \\\\".format(devts.get('SR')['A'],devts.get('SR')['B'],devts.get('SR')['C'],devts.get('SR')['D']))
    #else:
    #  print("Tight signal plane ($\\ngoodtrack \\geq 2$) & -- &  -- & -- & -- \\\\")

    #print("Loose signal plane ($\\ngoodtrack = 1$)     & ${:.02fL}$ &  ${:.02fL}$ & ${:.02fL}$ & ${:.02fL}$ \\\\".format(devts.get('VR1')['A'],devts.get('VR1')['B'],devts.get('VR1')['C'],devts.get('VR1')['D']))
    #print("Control plane  ($\\ngoodtrack = 0$)         & ${:.02fL}$ &  ${:.02fL}$ & ${:.02fL}$ & ${:.02fL}$ \\\\".format(devts.get('VR2')['A'],devts.get('VR2')['B'],devts.get('VR2')['C'],devts.get('VR2')['D']))

    #print("Transfer factor 1 $\\rightarrow$ 2           & ${:.03fL}$ &  ${:.03fL}$ & ${:.03fL}$ & ${:.03fL}$ \\\\".format(devts.get('SR')['A']/devts.get('VR1')['A'],devts.get('SR')['B']/devts.get('VR1')['B'],devts.get('SR')['C']/devts.get('VR1')['C'],devts.get('SR')['D']/devts.get('VR1')['D']))
    #print("Transfer factor 0 $\\rightarrow$ 1           & ${:.03fL}$ &  ${:.03fL}$ & ${:.03fL}$ & ${:.03fL}$ \\\\".format(devts.get('VR1')['A']/devts.get('VR2')['A'],devts.get('VR1')['B']/devts.get('VR2')['B'],devts.get('VR1')['C']/devts.get('VR2')['C'],devts.get('VR1')['D']/devts.get('VR2')['D']))

    ### Print background estimation tables
    #print("="*20)
    #print("Predictions:")
    if not args.blind:
      print("Tight plane ($\\ngoodtrack \\geq 3$) & ${:.02fL}$ &  ${:.02fL}$ & ${:.02fL}$ & ${:.02fL}$ \\\\".format(devts.get('SRg2tk')['A'],devts.get('SRg2tk')['B'],devts.get('SRg2tk')['C'],devts.get('SRg2tk')['D']))
    else:
      print("Tight plane ($\\ngoodtrack \\geq 3$) & -- &  -- & -- & -- \\\\")
    print("Prediction & ${:.02fL}$ &  ${:.02fL}$ & ${:.02fL}$ & ${:.02fL}$ \\\\".format(devts_pred['SRg2tk']['A'],devts_pred['SRg2tk']['B'],devts_pred['SRg2tk']['C'],devts_pred['SRg2tk']['D']))
    if not args.blind:
      print("Medium plane ($\\ngoodtrack = 2$) & ${:.02fL}$ &  ${:.02fL}$ & ${:.02fL}$ & ${:.02fL}$ \\\\".format(devts.get('SR2tk')['A'],devts.get('SR2tk')['B'],devts.get('SR2tk')['C'],devts.get('SR2tk')['D']))
    else:
      print("Medium plane ($\\ngoodtrack = 2$) & -- &  -- & -- & -- \\\\")
    print("Prediction & ${:.02fL}$ &  ${:.02fL}$ & ${:.02fL}$ & ${:.02fL}$ \\\\".format(devts_pred['SR2tk']['A'],devts_pred['SR2tk']['B'],devts_pred['SR2tk']['C'],devts_pred['SR2tk']['D']))
    print("Loose plane ($\\ngoodtrack = 1$)     & ${:.02fL}$ &  ${:.02fL}$ & ${:.02fL}$ & ${:.02fL}$ \\\\".format(devts.get('VR1')['A'],devts.get('VR1')['B'],devts.get('VR1')['C'],devts.get('VR1')['D']))
    print("Prediction     & ${:.02fL}$ &  -- & ${:.02fL}$ & -- \\\\".format(devts_pred['VR1']['A'],devts_pred['VR1']['C']))
    print("Control plane  ($\\ngoodtrack = 0$)         & ${:.02fL}$ &  ${:.02fL}$ & ${:.02fL}$ & ${:.02fL}$ \\\\".format(devts.get('VR2')['A'],devts.get('VR2')['B'],devts.get('VR2')['C'],devts.get('VR2')['D']))
    print("Prediction         & -- &  -- & -- & -- \\\\")

    ### Print signal events
    #print("\\multirow{{3}}{{*}}{{{}}} & Tight plane & ${:.02fL}$ &  ${:.02fL}$ & ${:.02fL}$ & ${:.02fL}$ \\\\".format(sig_fns[i].replace('_2017_hist.root','').replace('_2018_hist.root',''),devts.get('SRg2tk')['A'],devts.get('SRg2tk')['B'],devts.get('SRg2tk')['C'],devts.get('SRg2tk')['D']))
    ##print("&Prediction & ${:.02fL}$ &  ${:.02fL}$ & ${:.02fL}$ & ${:.02fL}$ \\\\".format(predict(devts,'SR','A'),predict(devts,'SR','B'),predict(devts,'SR','C'),predict(devts,'SR','D')))
    #print("&Medium plane & ${:.02fL}$ &  ${:.02fL}$ & ${:.02fL}$ & ${:.02fL}$ \\\\".format(devts.get('SR2tk')['A'],devts.get('SR2tk')['B'],devts.get('SR2tk')['C'],devts.get('SR2tk')['D']))
    #print("&Loose plane     & ${:.02fL}$ &  ${:.02fL}$ & ${:.02fL}$ & ${:.02fL}$ \\\\".format(devts.get('VR1')['A'],devts.get('VR1')['B'],devts.get('VR1')['C'],devts.get('VR1')['D']))
    ##print("&Prediction     & ${:.02fL}$ &  -- & ${:.02fL}$ & -- \\\\".format(predict(devts,'VR1','A'),predict(devts,'VR1','C')))
    #print("&Control plane          & ${:.02fL}$ &  ${:.02fL}$ & ${:.02fL}$ & ${:.02fL}$ \\\\".format(devts.get('VR2')['A'],devts.get('VR2')['B'],devts.get('VR2')['C'],devts.get('VR2')['D']))
    ##print("&Prediction         & -- &  -- & -- & -- \\\\")
    #print("\\hline")
