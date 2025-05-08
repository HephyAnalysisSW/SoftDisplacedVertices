# This script reads from ROOT files including MLscore distribution for SRs and CRs
# and will converts those numbers into datacard for limit plot
# Make sure to run this with env with ROOT

import ROOT
import ctypes
import argparse
import math
import pandas as pd
import numpy as np
import os
import pickle as pkl

parser = argparse.ArgumentParser()
parser.add_argument('--year', help="which year it is printing")
parser.add_argument('--scale', type=float, default=1, help="which year it is printing")
parser.add_argument('--output', help="output dir")
parser.add_argument('--HEM', action="store_true", help="output dir")
args = parser.parse_args()

def getABCDSyst(year):
  # This is for fake MET veto at 0.5
  #s = {
  #  '20161': 0.031,
  #  '20162': 0.605,
  #  '2017': 0.189,
  #  '2018': 0.108,
  #}

  #This is for fake MET veto at 0.6
  #s = {
  #  '20161': 0.033,
  #  '20162': 0.615,
  #  '2017': 0.192,
  #  '2018': 0.11,
  #}
  s = {
    #'2017': 0.514,
    #'2018': 0.514,
  }

  return s[str(year)]

def getmapvetosyst(ctau_str):
  ctau = float(ctau_str.replace('p','.'))
  flog = ROOT.TF1("flog","TMath::Log(0.65*x-0.07)",0,max(ctau*2,1000))
  syst_func = flog.Eval(ctau)*0.01
  syst = max(0,syst_func)
  return syst

def getTFs(year):
  tfs = {
      '2017':{
        '_F1_': 0.2740,
        '_F1ERR_': 0.0020,
        '_F2_': 0.1249,
        '_F2ERR_': 0.0025,
        '_F3_': 0.1013,
        '_F3ERR_': 0.0063,
        '_FLXY_1_': 0.3076,
        '_FLXY1ERR_': 0.0020,
        '_FLXY_2_': 0.410,
        '_FLXY2ERR_': 0.005,
        '_FLXY_3_': 0.475,
        '_FLXY3ERR_': 0.016,
        },
      '2018':{
        '_F1_': 0.2451,
        '_F1ERR_': 0.0015,
        '_F2_': 0.1232,
        '_F2ERR_': 0.0021,
        '_F3_': 0.0998,
        '_F3ERR_': 0.0053,
        '_FLXY_1_': 0.3002,
        '_FLXY1ERR_': 0.0017,
        '_FLXY_2_': 0.402,
        '_FLXY2ERR_': 0.004,
        '_FLXY_3_': 0.446,
        '_FLXY3ERR_': 0.013,
        }
      }
  return tfs[year]

def getPDFUncert(mg, dm, ct, year):
  '''
  This function returns the PDF uncertainty for a given gluino mass (mg), mass splitting (dm), ctau (ct), and year
  '''
  p0 = {}
  p0[100] = {
    20161: 3.018E-05,
    20162: 3.027E-05,
    2017: 2.391E-05,
    2018: 2.596E-05,
  }
  p0[200] = {
    20161: 1.422E-05,
    20162: 1.927E-05,
    2017: 1.324E-05,
    2018: 1.55E-05,
  }
  
  p1 = {}
  p1[100] = {}
  p1[200] = {}
  p1[100][20161] = {
    0.1: 0.06294,
    0.3: 0.01014,
    1: -0.01016,
    3: -0.00856,
    10: -0.00596,
    30: 0.01244,
    100: 0.00934,
    300: 0.02424,
    1000: 0.03284,
  }
  p1[200][20161] = {
    0.1: 0.06816,
    0.3: 0.01976,
    1: -0.00444,
    3: -0.01134,
    10: -0.00804,
    30: 0.00506,
    100: 0.01646,
    300: 0.02556,
    1000: 0.03756,
  }
  p1[100][20162] = {
    0.1: 0.04696,
    0.3: 0.00456,
    1: -0.00564,
    3: -0.00264,
    10: -0.00614,
    30: -0.00114,
    100: 0.00766,
    300: 0.02016,
    1000: 0.02716,
  }
  p1[200][20162] = {
    0.1: 0.07456,
    0.3: 0.00746,
    1: -0.00634,
    3: -0.02054,
    10: -0.01874,
    30: -0.00444,
    100: 0.00656,
    300: 0.01096,
    1000: 0.02726,
  }
  p1[100][2017] = {
    0.1: 0.05958,
    0.3: 0.01558,
    1: 0.00048,
    3: -0.00142,
    10: -0.00142,
    30: 0.00538,
    100: 0.01728,
    300: 0.02728,
    1000: 0.03278,
  }
  p1[200][2017] = {
    0.1: 0.06022,
    0.3: 0.01582,
    1: -0.00678,
    3: -0.01088,
    10: -0.00908,
    30: -0.00008,
    100: 0.01232,
    300: 0.02182,
    1000: 0.02972,
  }
  p1[100][2018] = {
    0.1: 0.05678,
    0.3: 0.00918,
    1: -0.00032,
    3: 0.00578,
    10: 0.00638, 
    30: 0.00788,
    100: 0.01928, 
    300: 0.02878, 
    1000: 0.03128,
  }
  p1[200][2018] = {
    0.1: 0.0613,
    0.3: 0.014,
    1: -0.013,
    3: -0.0127,
    10: -0.0106,
    30: -0.0022,
    100: 0.0071, 
    300: 0.0243, 
    1000: 0.0311,
  }

  return p0[dm][year]*mg+p1[dm][year][float(ct)/1000]

def getSystUncert(dm, year):
  '''
  This function returns a dictionary that includes systematic cources
  '''
  csv_path = 'sig_syst_csv.csv'
  df = pd.read_csv(csv_path, index_col=0)
  #source_dm_dependent = ["vtxreco", "MET_JetRes", "MET_JetEn", "MET_UnclusterEn"]
  source_dm_dependent = []
  #source_dm_independent = ["trigger","vtxreco","jetmet","tkreco","pu", "l1", "intlumi"]
  source_dm_independent = ["trigger","vtxreco","jes","jer","uncEn","tauveto","pu", "l1", "intlumi","qcdscale","pdf"]
  #source_dm_independent = ["trackreco", "trigger", "trigger_ele", "pu", "l1", "intlumi"]
  s = {}
  for source in source_dm_dependent:
    s[source] = df[str(year)][source+'_'+str(dm)]
  for source in source_dm_independent:
    if source+"A" in df[str(year)] and source+"C" in df[str(year)]:
      s[source+"A"] = df[str(year)][source+"A"]
      s[source+"C"] = df[str(year)][source+"C"]
    else:
      s[source] = df[str(year)][source]

  return s

def getNumSigEvents(fn, regions, SF, HEMpath=None, HEMfrac=None):
  if (HEMpath is None) or (HEMfrac is None):
    return getNumEvents(fn, regions, SF, useData=False)
  noHEM = getNumEvents(fn, regions, SF, useData=False)
  HEM = getNumEvents(HEMpath, regions, SF, useData=False)
  res = noHEM
  for i in range(len(regions)):
    res['weighted'][i] = noHEM['weighted'][i]*(1-HEMfrac) + HEM['weighted'][i]*HEMfrac
    res['raw'][i] = int(noHEM['raw'][i]*(1-HEMfrac) + HEM['raw'][i]*HEMfrac)
  return res

def predictEvents(d):
  f_displaced = d['weighted'][9]/d['weighted'][13]
  f_prompt = d['weighted'][11]/d['weighted'][15]
  d['weighted'][0] = d['weighted'][12]*f_displaced*f_displaced*f_displaced/(1-f_displaced)
  d['weighted'][1] = d['weighted'][13]*f_displaced*f_displaced*f_displaced/(1-f_displaced)
  d['weighted'][4] = d['weighted'][12]*f_displaced*f_displaced
  d['weighted'][5] = d['weighted'][13]*f_displaced*f_displaced
  d['weighted'][8] = d['weighted'][12]*f_displaced
  d['weighted'][2] = d['weighted'][14]*f_prompt*f_prompt*f_prompt/(1-f_prompt)
  d['weighted'][3] = d['weighted'][15]*f_prompt*f_prompt*f_prompt/(1-f_prompt)
  d['weighted'][6] = d['weighted'][14]*f_prompt*f_prompt
  d['weighted'][7] = d['weighted'][15]*f_prompt*f_prompt
  d['weighted'][10] = d['weighted'][14]*f_prompt
  return d

def getNumEvents(fn, regions, SF=1, useData=True, blind=True):
  '''
  This function return a dictionary including:
    raw: raw number of events in the region
    weighted: weighted number of events in the region
    stat_uncert: statistical uncertainty of number of events in the region
  '''
  d = {
    'raw': [],
    'weighted': [],
    'stat_uncert': [],
  }
  f = ROOT.TFile(fn)
  for r in regions:
    h = f.Get(r+'/MET_pt')
    nevt_uncert = ctypes.c_double(0)
    binL = 0
    binH = 1000000
    nevt = h.IntegralAndError(binL,binH,nevt_uncert)
    if nevt<=0:
      nevt = 0.000001
      #nevt = 1
    nevt_raw = h.GetEntries()
    if useData and blind and (r in blinding_regions):
    #if blind and (r in blinding_regions):
      d['raw'].append(0)
      d['weighted'].append(0)
      d['stat_uncert'].append(0.00)
    else:
      d['raw'].append(int(nevt_raw))
      d['weighted'].append(nevt*SF)
      d['stat_uncert'].append(nevt_uncert.value*SF)
  #if useData:
  #  d = predictEvents(d)

  return d

def getNumEventsCtau(fnbase, ctau, SF):

  def loadall(filename):
    # ["MLScore", "vtx_ntk", "weight", "ctau0", "ctau1"]
    l = []
    with open(filename, "rb") as f:
        while True:
            try:
                l.append(pkl.load(f))
            except EOFError:
                break
    return l

  def getctauweight(ct,origin,target):
    eq_origin = (1/origin)*np.exp(-ct/origin)
    eq_target = (1/target)*np.exp(-ct/target)
    return eq_target/eq_origin

  d = {
    'raw': [],
    'weighted': [],
    'stat_uncert': [],
  }

  if os.path.exists(filepath+fnbase % (ctau)+'.pkl'):
    f = loadall(filepath+fnbase % (ctau)+'.pkl')
    idx_regions = [
      ((f[1]>=5).flatten()) & ((f[0]>0.2).flatten()),
      ((f[1]>=5).flatten()) & ((f[0]<0.2).flatten()),
      ((f[1]==4).flatten()) & ((f[0]>0.2).flatten()),
      ((f[1]==4).flatten()) & ((f[0]<0.2).flatten()),
      ((f[1]==3).flatten()) & ((f[0]>0.2).flatten()),
      ((f[1]==3).flatten()) & ((f[0]<0.2).flatten()),
    ]
    for i in range(len(idx_regions)):
      idx_select = idx_regions[i]
      d['raw'].append(int(len(f[2][idx_select])))
      d['weighted'].append(np.sum(f[2][idx_select])*SF)
      d['stat_uncert'].append(0.00)
  else:
    ctau_list = np.array([100,1000,10000,100000,1000000])
    idx_pos = np.searchsorted(ctau_list, ctau, side='right')
    found = False
    while (idx_pos<len(ctau_list)):
      if os.path.exists(filepath+fnbase % (ctau_list[idx_pos])+'.pkl'):
        found = True
        break
      else:
        idx_pos += 1
    if not found:
      idx_pos = len(ctau_list)-1
      while (idx_pos>=0):
        if os.path.exists(filepath+fnbase % (ctau_list[idx_pos])+'.pkl'):
          found = True
          break
        else:
          idx_pos -= 1
    if not found:
      print("No files available for reweighting!")
    f = loadall(filepath+fnbase % (ctau_list[idx_pos])+'.pkl')
    w = []
    for i in range(len(f[3])):
      w.append(getctauweight(f[3][i],ctau_list[idx_pos]/10000,ctau/10000)*getctauweight(f[4][i],ctau_list[idx_pos]/10000,ctau/10000)*f[2][i])
    w = np.array(w)
    idx_regions = [
      ((f[1]>=5).flatten()) & ((f[0]>0.2).flatten()),
      ((f[1]>=5).flatten()) & ((f[0]<0.2).flatten()),
      ((f[1]==4).flatten()) & ((f[0]>0.2).flatten()),
      ((f[1]==4).flatten()) & ((f[0]<0.2).flatten()),
      ((f[1]==3).flatten()) & ((f[0]>0.2).flatten()),
      ((f[1]==3).flatten()) & ((f[0]<0.2).flatten()),
    ]
    for i in range(len(idx_regions)):
      idx_select = idx_regions[i]
      d['raw'].append(int(len(w[idx_select])))
      d['weighted'].append(np.sum(w[idx_select])*SF)
      d['stat_uncert'].append(0.00)

  return d


def getYield(nevt):
  err = math.sqrt(nevt)
  lo_bound = int(round(max(0, nevt - 5*err)))
  hi_bound = int(round(nevt + 5*err))
  #return "{} [{},{}]".format(nevt, lo_bound, hi_bound)
  return "{}".format(nevt)


template = '''
# Signal sample: _SIGNAL_
# Expected limit datacard for MC
imax _NCHANNELS_  number of channels
jmax 1  number of backgrounds
kmax _NUNCERT_  number of nuisance parameters (sources of systematic uncertainty)
------------
# Analysis channel and observed number of events
bin _CHANNELNAME_ 
observation _OBSERVATION_
------------
# now we list the expected number of events for signal and all backgrounds in that bin
# the second 'process' line must have a positive number for backgrounds, and 0 for signal
# then we list the independent sources of uncertainties, and give their effect (syst. error)
# on each process and bin
bin              _CHANNELNAMERATE_
process          _PROCESSNAMERATE_ 
process          _PROCESSIDXRATE_
rate             _PROCESSRATE_
----STATISTICAL UNCERTAINTIES-----
_STATUNCERTSIG_
_STATUNCERTBKG_
-----SYSTEMATIC UNCERTAINTIES----- 
_SYSTUNCERT_
_SYSTUNCERTSIG_
-----ABCD IMPLEMENTATION----- 
_ABCD_
'''

if not os.path.exists(args.output):
  os.makedirs(args.output)
useData = True
channels = []
dirs = []
for ngoodtrk,rn in zip([3,2,1,0],['SR_g2tk','SR_2tk','VR1','VR2']):
  for r,dn in zip(['A','B','C','D'],['_evt','_CRlowMET_evt','_CRlowLxy_evt','_CRlowLxylowMET_evt']):
    channels.append('{}{}_{}'.format(r,ngoodtrk,args.year))
    dirs.append('{}{}'.format(rn,dn))
processes = ['signal','background']
processidx = ['0','1']
channelnamerate = ''
for _ in channels:
  channelnamerate += ('\t'+_)*len(processes)
processnamerate = ('\t'+'\t'.join(processes))*len(channels)
processidxrate = ('\t'+'\t'.join(processidx))*len(channels)

filepathData = '/eos/vbc/group/cms/ang.li/Histos_datacard_mapveto_2g2regions_noPU/'

blinding_regions = []

bkg = 'background_{}_hist.root'.format(args.year)
data = 'met{}_hist.root'.format(args.year)
if useData:
  d_bkg = getNumEvents(filepathData+data,dirs,SF=1,useData=True)
else:
  d_bkg = getNumEvents(filepathMC+bkg,dirs,SF=1,useData=False)
n_uncerts_bkg = 0
bkg_stat_uncert = ''
syst_uncert = ''

abcd = '''
CMS_EXO24033_f_1__YEAR_          param       _F1_  _F1ERR_
CMS_EXO24033_f_2__YEAR_          param       _F2_  _F2ERR_
CMS_EXO24033_f_3__YEAR_          param       _F3_  _F3ERR_
CMS_EXO24033_flxy_1__YEAR_       param       _FLXY_1_  _FLXY1ERR_
CMS_EXO24033_flxy_2__YEAR_       param       _FLXY_2_  _FLXY2ERR_
CMS_EXO24033_flxy_3__YEAR_       param       _FLXY_3_  _FLXY3ERR_

CMS_EXO24033_b1__YEAR_    rateParam   B1__YEAR_   background    _B1YIELD_
CMS_EXO24033_d1__YEAR_    rateParam   D1__YEAR_   background    _D1YIELD_
CMS_EXO24033_a0__YEAR_    rateParam   A0__YEAR_   background    _A0YIELD_
CMS_EXO24033_b0__YEAR_    rateParam   B0__YEAR_   background    _B0YIELD_
CMS_EXO24033_c0__YEAR_    rateParam   C0__YEAR_   background    _C0YIELD_
CMS_EXO24033_d0__YEAR_    rateParam   D0__YEAR_   background    _D0YIELD_
CMS_EXO24033_a1__YEAR_    rateParam   A1__YEAR_   background    ((@0+@1)/(@2+@3)*(@4+@5)*@6) CMS_EXO24033_b1__YEAR_,CMS_EXO24033_d1__YEAR_,CMS_EXO24033_b0__YEAR_,CMS_EXO24033_d0__YEAR_,CMS_EXO24033_a0__YEAR_,CMS_EXO24033_c0__YEAR_,CMS_EXO24033_flxy_1__YEAR_
CMS_EXO24033_c1__YEAR_    rateParam   C1__YEAR_   background    ((@0+@1)/(@2+@3)*(@4+@5)*(1-@6)) CMS_EXO24033_b1__YEAR_,CMS_EXO24033_d1__YEAR_,CMS_EXO24033_b0__YEAR_,CMS_EXO24033_d0__YEAR_,CMS_EXO24033_a0__YEAR_,CMS_EXO24033_c0__YEAR_,CMS_EXO24033_flxy_1__YEAR_
CMS_EXO24033_b2__YEAR_    rateParam   B2__YEAR_   background    ((@0+@1)/(@2+@3)*(@0+@1)*@4/@5*@6) CMS_EXO24033_b1__YEAR_,CMS_EXO24033_d1__YEAR_,CMS_EXO24033_b0__YEAR_,CMS_EXO24033_d0__YEAR_,CMS_EXO24033_f_2__YEAR_,CMS_EXO24033_f_1__YEAR_,CMS_EXO24033_flxy_2__YEAR_
CMS_EXO24033_d2__YEAR_    rateParam   D2__YEAR_   background    ((@0+@1)/(@2+@3)*(@0+@1)*@4/@5*(1-@6)) CMS_EXO24033_b1__YEAR_,CMS_EXO24033_d1__YEAR_,CMS_EXO24033_b0__YEAR_,CMS_EXO24033_d0__YEAR_,CMS_EXO24033_f_2__YEAR_,CMS_EXO24033_f_1__YEAR_,CMS_EXO24033_flxy_2__YEAR_
CMS_EXO24033_a2__YEAR_    rateParam   A2__YEAR_   background    ((@0+@1)/(@2+@3)*(@0+@1)/(@2+@3)*(@4+@5)*@6/@7*@8) CMS_EXO24033_b1__YEAR_,CMS_EXO24033_d1__YEAR_,CMS_EXO24033_b0__YEAR_,CMS_EXO24033_d0__YEAR_,CMS_EXO24033_a0__YEAR_,CMS_EXO24033_c0__YEAR_,CMS_EXO24033_f_2__YEAR_,CMS_EXO24033_f_1__YEAR_,CMS_EXO24033_flxy_2__YEAR_
CMS_EXO24033_c2__YEAR_    rateParam   C2__YEAR_   background    ((@0+@1)/(@2+@3)*(@0+@1)/(@2+@3)*(@4+@5)*@6/@7*(1-@8)) CMS_EXO24033_b1__YEAR_,CMS_EXO24033_d1__YEAR_,CMS_EXO24033_b0__YEAR_,CMS_EXO24033_d0__YEAR_,CMS_EXO24033_a0__YEAR_,CMS_EXO24033_c0__YEAR_,CMS_EXO24033_f_2__YEAR_,CMS_EXO24033_f_1__YEAR_,CMS_EXO24033_flxy_2__YEAR_
CMS_EXO24033_b3__YEAR_    rateParam   B3__YEAR_   background    ((@0+@1)/(@2+@3)*(@0+@1)/(@2+@3)*(@0+@1)*@4/@5*@6/@5*@7) CMS_EXO24033_b1__YEAR_,CMS_EXO24033_d1__YEAR_,CMS_EXO24033_b0__YEAR_,CMS_EXO24033_d0__YEAR_,CMS_EXO24033_f_3__YEAR_,CMS_EXO24033_f_1__YEAR_,CMS_EXO24033_f_2__YEAR_,CMS_EXO24033_flxy_3__YEAR_
CMS_EXO24033_d3__YEAR_    rateParam   D3__YEAR_   background    ((@0+@1)/(@2+@3)*(@0+@1)/(@2+@3)*(@0+@1)*@4/@5*@6/@5*(1-@7)) CMS_EXO24033_b1__YEAR_,CMS_EXO24033_d1__YEAR_,CMS_EXO24033_b0__YEAR_,CMS_EXO24033_d0__YEAR_,CMS_EXO24033_f_3__YEAR_,CMS_EXO24033_f_1__YEAR_,CMS_EXO24033_f_2__YEAR_,CMS_EXO24033_flxy_3__YEAR_
CMS_EXO24033_a3__YEAR_    rateParam   A3__YEAR_   background    ((@0+@1)/(@2+@3)*(@0+@1)/(@2+@3)*(@0+@1)/(@2+@3)*(@4+@5)*@6/@7*@8/@7*@9) CMS_EXO24033_b1__YEAR_,CMS_EXO24033_d1__YEAR_,CMS_EXO24033_b0__YEAR_,CMS_EXO24033_d0__YEAR_,CMS_EXO24033_a0__YEAR_,CMS_EXO24033_c0__YEAR_,CMS_EXO24033_f_3__YEAR_,CMS_EXO24033_f_1__YEAR_,CMS_EXO24033_f_2__YEAR_,CMS_EXO24033_flxy_3__YEAR_
CMS_EXO24033_c3__YEAR_    rateParam   C3__YEAR_   background    ((@0+@1)/(@2+@3)*(@0+@1)/(@2+@3)*(@0+@1)/(@2+@3)*(@4+@5)*@6/@7*@8/@7*(1-@9)) CMS_EXO24033_b1__YEAR_,CMS_EXO24033_d1__YEAR_,CMS_EXO24033_b0__YEAR_,CMS_EXO24033_d0__YEAR_,CMS_EXO24033_a0__YEAR_,CMS_EXO24033_c0__YEAR_,CMS_EXO24033_f_3__YEAR_,CMS_EXO24033_f_1__YEAR_,CMS_EXO24033_f_2__YEAR_,CMS_EXO24033_flxy_3__YEAR_
'''.replace('_YEAR_',args.year)
yield_label = ['_B1YIELD_','_D1YIELD_','_A0YIELD_','_B0YIELD_','_C0YIELD_','_D0YIELD_']
yield_label_idx = [5,7,8,9,10,11]
for i in range(len(yield_label)):
  abcd = abcd.replace(yield_label[i],getYield(d_bkg['weighted'][yield_label_idx[i]+4]))

f_label = ['_F1_','_F2_','_F3_','_F1ERR_','_F2ERR_','_F3ERR_','_FLXY_1_','_FLXY_2_','_FLXY_3_','_FLXY1ERR_','_FLXY2ERR_','_FLXY3ERR_']
tfs = getTFs(args.year)
for fl in f_label:
  abcd = abcd.replace(fl,str(tfs[fl]))

rate = ''
sig_stat_uncert = ''
sig_syst_uncert = ''
syst_sources = ["trigger","vtxreco","jes","jer","uncEn","tauveto","pu", "l1", "intlumi","qcdscale","pdf"]
syst_sources_nice = ["CMS_EXO24033_METtrigger","CMS_EXO24033_vtxreco","CMS_scale_j","CMS_res_j","CMS_EXO24033_scale_met_unclustered_energy","CMS_eff_t","CMS_pileup","CMS_l1_ecal_prefiring","lumi_13TeV_1718","QCDscale_BSMsignal","CMS_EXO24033_PDF"]
#syst_sources = ["vtxtkreco_Corr", "ML", "fake_MET", "MET_JetRes", "MET_JetEn", "MET_UnclusterEn", "trigger", "trigger_ele", "pu", "l1", "intlumi"]
for i in range(len(channels)):
  rate += '\t0.0'
  rate += '\t'+'1.0'
template_new = template.replace('_NCHANNELS_',str(len(channels)))
template_new = template_new.replace('_NUNCERT_',str(n_uncerts_bkg+6))
template_new = template_new.replace('_CHANNELNAME_',str('\t'.join(channels)))
template_new = template_new.replace('_CHANNELNAMERATE_',channelnamerate)
template_new = template_new.replace('_PROCESSNAMERATE_',processnamerate)
template_new = template_new.replace('_PROCESSIDXRATE_',processidxrate)
template_new = template_new.replace('_PROCESSRATE_',rate)
template_new = template_new.replace('_STATUNCERTBKG_',bkg_stat_uncert)
template_new = template_new.replace('_SYSTUNCERT_',syst_uncert)
template_new = template_new.replace('_ABCD_',abcd)
template_new = template_new.replace('_OBSERVATION_','\t'.join(map(lambda x:"{:.2f}".format(x),d_bkg['weighted'])))
#if useData:
#  template_new = template_new.replace('_OBSERVATION_','\t'.join(map(lambda x:"{:.2f}".format(x),d_data['raw'])))
#else:
#  template_new = template_new.replace('_OBSERVATION_','\t'.join(map(lambda x:"{:.2f}".format(x),d_bkg['weighted'])))
f_datacard = open(os.path.join(args.output,'bkgonly_datacard_{}.txt'.format(args.year)),'w')
f_datacard.write(template_new)
f_datacard.close()


