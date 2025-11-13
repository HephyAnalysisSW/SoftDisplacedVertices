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
  s = {
    #'2017': 0.514,
    #'2018': 0.514,
  }

  return s[str(year)]

def getmapvetosyst(model,ctau,year):
  func = {
      2017:{
        'stop':{
          'A': "0.94*TMath::Log10(x)-0.23",
          'B': "1.36*TMath::Log10(x)-1.20",
          'C': "0",
          'D': "0",
          },
        'C1N2':{
          'A': "1.31*TMath::Log10(x)+0.14",
          'B': "1.67*TMath::Log10(x)-1.05",
          'C': "0",
          'D': "0",
          },
        },
      2018:{
        'stop':{
          'A': "1.01*TMath::Log10(x)-0.54",
          'B': "1.19*TMath::Log10(x)-0.85",
          'C': "0",
          'D': "0",
          },
        'C1N2':{
          'A': "0.61*TMath::Log10(x)+1.27",
          'B': "1.49*TMath::Log10(x)-0.38",
          'C': "0",
          'D': "0",
          },
        }
      }
  res = {}
  for r in ['A','B','C','D']:
    flog = ROOT.TF1("flog",func[year][model][r],0,max(ctau*2,1000))
    syst_func = flog.Eval(ctau)*0.01
    syst = max(0.01,syst_func)
    res[r] = syst
  return res

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

def getSystUncert(dm, year, model):
  '''
  This function returns a dictionary that includes systematic cources
  '''
  csv_path = f'sig_syst_csv_{model}.csv'
  df = pd.read_csv(csv_path, index_col=0)
  #source_dm_dependent = ["vtxreco", "MET_JetRes", "MET_JetEn", "MET_UnclusterEn"]
  source_dm_dependent = []
  #source_dm_independent = ["trigger","vtxreco","jetmet","tkreco","pu", "l1", "intlumi"]
  source_dm_independent = ["trigger","vtxreco","jes","jer","uncEn","tauveto","pu", "l1", "intlumi","lumi1718","qcdscale","pdf"]
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

def getNumSigEvents(filepath, regions, model, mLLP, dm, ctau, BR, year, SF, HEMpath=None, HEMfrac=None):
  if (HEMpath is None) or (HEMfrac is None):
    return getNumEventsCtau(filepath, regions, model, mLLP, dm, ctau, BR, year, SF)
  noHEM = getNumEventsCtau(filepath, regions, model, mLLP, dm, ctau, BR, year, SF)
  HEM = getNumEventsCtau(HEMpath, regions, model, mLLP, dm, ctau, BR, year, SF)
  res = noHEM
  for i in range(len(regions)):
    res['weighted'][i] = noHEM['weighted'][i]*(1-HEMfrac) + HEM['weighted'][i]*HEMfrac
    res['raw'][i] = int(noHEM['raw'][i]*(1-HEMfrac) + HEM['raw'][i]*HEMfrac)
  return res

def getNumSigEvents_old(fn, regions, SF, HEMpath=None, HEMfrac=None):
  if (HEMpath is None) or (HEMfrac is None):
    return getNumEventsPKL(fn, regions, SF, useData=False)
  noHEM = getNumEventsPKL(fn, regions, SF, useData=False)
  HEM = getNumEventsPKL(HEMpath, regions, SF, useData=False)
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

def getNumEventsPKL(fn, regions, SF=1, useData=True, blind=True):
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
  # Get data from pkl file
  with open(fn,"rb") as f:
    data = pkl.load(f)

  for r in regions:
    r = r.replace("_evt","")
    nevt_raw = len(data[r]['evt_weight'])
    nevt = np.sum(data[r]['evt_weight'])

    if nevt<=0:
      nevt = 0.000001
    if useData and blind and (r in blinding_regions):
      d['raw'].append(0)
      d['weighted'].append(0)
      d['stat_uncert'].append(0.00)
    else:
      d['raw'].append(int(nevt_raw))
      d['weighted'].append(nevt*SF)
      d['stat_uncert'].append(0.00)

  return d

def getwidth(m,dm):
    # this calculated the 4-body partial decay width 
    # m is the LLP mass and dm is the mass splitting
    return (9*28*(1.98*1e-14)*((dm)/30)**8*(400/m))

def getctau(m,dm):
    # this calculates the mean proper length of the LLP
    # m is the LLP mass and dm is the mass splitting
    return 1.973269788e-13/getwidth(m,dm)

def getctauBR(m,dm,br):
    # this calculates the mean proper length of the LLP
    # m is the LLP mass and dm is the mass splitting
    width_4body = getwidth(m,dm)
    width_total = width_4body/br
    return 1.973269788e-13/width_total

def getctauweight(ct,origin,target):
  clipct = np.clip(ct,a_min=0,a_max=origin)
  #eq_origin = (1/origin)*np.exp(-clipct*10/origin)
  #eq_target = (1/target)*np.exp(-clipct*10/target)
  #ratio = eq_target/eq_origin
  ratio = (origin/target)*np.exp(clipct*10*((1/origin)-(1/target)))
  return ratio

def getBRweight(decaymode,origin=0.5,target=0.5):
  w4 = target/origin
  w2 = (1-target)/(1-origin)
  w = w4*(decaymode==1)+w2*(decaymode==2)
  return w

def ctaustr(ct):
  if ct>1:
    return str(ct).replace('.0','')
  else:
    return str(ct).replace('.','p')

def getNumEventsCtau(filepath, regions, model, mLLP, dm, ctau, BR, year, SF):
  d = {
    'raw': [0]*len(regions),
    'weighted': [0]*len(regions),
    'stat_uncert': [0]*len(regions),
  }

  # Determine which files to use for reweighting
  print("Reweighting for ctau {}".format(ctau))
  file_list = []
  ctau_file = []
  ctau_C1N2 = [0.2,0.5,1,2,5,10,20,50,100,200]
  dmtoctau = {
      'stop':{
        12: [20,200],
        15: [2,20],
        20: [0.2,2],
        25: [0.2],
        },
      'C1N2':{
        12: [0.2,2,20,200],
        15: [0.2,2,20,200],
        20: [0.2,2,20,200],
        25: [0.2,2,20,200],
        }
      }
  ctau_list = dmtoctau[model][dm]
  ctau_use = []
  #ctau_list = np.array([0.2,2,20,200])    # units in mm
  idx_pos = np.searchsorted(ctau_list, ctau, side='right')
  if idx_pos==0:
    ctau_use.append(ctau_list[idx_pos])
  elif idx_pos>=len(ctau_list):
    ctau_use.append(ctau_list[idx_pos-1])
  else:
    #ctau_use.append(ctau_list[idx_pos-1])
    ctau_use.append(ctau_list[idx_pos])
  for ict in ctau_use:
    fntmp = os.path.join(filepath,"{}_M{}_{}_ct{}_{}_hist.pkl".format(model,mLLP,mLLP-dm,ctaustr(ict),year))
    if os.path.exists(fntmp):
      file_list.append(fntmp)
      ctau_file.append(ict)
    else:
      print("File not available: {}".format(fntmp))

  nfiles = len(file_list)
  if nfiles==0:
    print("No files available for reweighting!")
  else:
    print("Reweighting using the following files:")
    print(file_list)

  # Get the number of events using the files
  for ifn,ict in zip(file_list,ctau_file):
    # Get data from pkl file
    with open(ifn,"rb") as f:
      data = pkl.load(f)

    for ir,r in enumerate(regions):
      r = r.replace("_evt","")
      # Calculate ctau weights
      #ct_weights = getctauweight(data[r]['LLP_ctau'],ict,ctau)
      if model=='stop':
        BRweights0 = getBRweight(data[r]['LLP_decaymode0'],target=BR)
        BRweights1 = getBRweight(data[r]['LLP_decaymode1'],target=BR)
        ct_weights0 = getctauweight(data[r]['LLP_ctau0'],ict,ctau)
        ct_weights1 = getctauweight(data[r]['LLP_ctau1'],ict,ctau)
        ct_weights_tot = ct_weights0*ct_weights1
        ct_weights_tot = np.clip(ct_weights_tot,a_min=0,a_max=100)
        ct_weights = ct_weights_tot*BRweights0*BRweights1
      elif model=='C1N2':
        ct_weights0 = getctauweight(data[r]['LLP_ctau0'],ict,ctau)
        ct_weights0 = np.clip(ct_weights0,a_min=0,a_max=100)
        ct_weights = ct_weights0
      else:
        raise Exception("Model {} not supported!".format(model))
      #ct_weights = np.prod(ct_weights,axis=1)

      nevt_raw = np.sum(ct_weights!=0)
      nevt = np.sum(data[r]['evt_weight']*ct_weights)

      d['raw'][ir] += nevt_raw
      d['weighted'][ir] += nevt

  for ir in range(len(regions)):
    d['weighted'][ir] /= nfiles
    d['weighted'][ir] *= SF
  
  return d


def getYield(nevt):
  err = math.sqrt(nevt)
  lo_bound = int(round(max(0, nevt - 5*err)))
  hi_bound = int(round(nevt + 5*err))
  #return "{} [{},{}]".format(nevt, lo_bound, hi_bound)
  return "{}".format(nevt)


template = '''
# Signal sample: _SIGNAL_
# Ctau: _CTAU_
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

model = "stop"
#model = "C1N2"
filepathMC = '/eos/vbc/group/cms/ang.li/Histos_datacard_mapveto_2g2regions_noPU/'
filepathData = '/eos/vbc/group/cms/ang.li/Histos_datacard_mapveto_2g2regions_noPU/'
#filepathSig = '/eos/vbc/group/cms/ang.li/Histos_datacard_centralsignal/'
#filepathSigHEM = '/eos/vbc/group/cms/ang.li/Histos_datacard_centralsignal_HEM/'
#filepathSig = '/scratch-cbe/users/ang.li/SoftDV/Histos/Histos_datacard_centralsignal_mcmap_bugfix/'
#filepathSigHEM = '/scratch-cbe/users/ang.li/SoftDV/Histos/Histos_datacard_centralsignal_mcmap_bugfix_HEM/'
filepathSig = '/scratch-cbe/users/ang.li/SoftDV/Histos/Histos_datacard_centralsignal_datamap_bugfix/'
filepathSigHEM = '/scratch-cbe/users/ang.li/SoftDV/Histos/Histos_datacard_centralsignal_datamap_bugfix_HEM/'

#filepathSig = '/scratch-cbe/users/ang.li/SoftDV/Histos/Histos_c1n2_lowdm/'
#filepathSigHEM = '/scratch-cbe/users/ang.li/SoftDV/Histos/Histos_c1n2_lowdm/'

if model=='stop':
  mLLP = [400,500,600,700,800,900,1000,1100,1200,1300,1400]
  BRs = [0.1,0.5,1]
  dms = [25,20,15,12]
elif model=='C1N2':
  mLLP = [200,300,400,500,600]
  BRs = [1]
  #ctaus = [0.2,2,20,200]
  ctaus = [0.2,0.5,1,2,5,10,20,50,100,200]
  dms = [25,20,15,12]

BRorCtaus = BRs if model=='stop' else ctaus

#blinding_regions = ['SR_g2tk_evt','SR_g2tk_CRlowMET_evt','SR_g2tk_CRlowLxy_evt','SR_g2tk_CRlowLxylowMET_evt','SR_2tk_evt','SR_2tk_CRlowMET_evt','SR_2tk_CRlowLxy_evt','SR_2tk_CRlowLxylowMET_evt','VR1_evt','VR1_CRlowLxy_evt']
blinding_regions = []

bkg = 'background_{}_hist.root'.format(args.year)
data = 'met{}_hist.root'.format(args.year)
if useData:
  d_bkg = getNumEvents(filepathData+data,dirs,SF=1,useData=True)
else:
  d_bkg = getNumEvents(filepathMC+bkg,dirs,SF=1,useData=False)
n_uncerts_bkg = 0
bkg_stat_uncert = ''
#for i in range(len(channels)):
#  uncert_i = 1.0
#  if not d_bkg['weighted'][i]==0:
#    uncert_i += d_bkg['stat_uncert'][i]/d_bkg['weighted'][i]
#  bkg_stat_uncert += 'background_stat_{0}\tlnN'.format(channels[i]) \
#                    +'\t-'*(i*len(processes)) \
#                    +'\t-\t{:.3g}'.format(uncert_i) \
#                    +'\t-'*((len(channels)-i-1)*len(processes))+'\n'
#  n_uncerts_bkg += 1
#bkg_stat_uncert += 'syst_uncert\tlnN' + '\t2.0'*(len(channels)*len(processes))
#n_uncerts_bkg += 1

syst_uncert = ''

#ABCD uncertainty
#bkg_uncert = getABCDSyst(args.year)
#if bkg_uncert is not None:
#  syst_uncert += 'bkg_syst\tlnN' \
#                +'\t-\t-\t-\t{:.5g}\t-\t-\t-\t-'.format(bkg_uncert+1) \
#                +'\t-\t-\t-\t{:.5g}\t-\t-\t-\t-'.format(bkg_uncert+1) \
#                +'\t-\t-\t-\t-\t-\t-\t-\t-'*2+'\n' 
#  n_uncerts_bkg += 1

#ABCD uncertainty
#not using it now because it is not necessary
#syst_uncert += 'ABCD_syst\tlnN' \
#              +'\t-\t{:.5g}'.format(getABCDSyst(args.year)+1) \
#              +'\t-'*((len(channels)-1)*len(processes))+'\n'
#n_uncerts_bkg += 1

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

for m in mLLP:
  for dm in dms:
    for ibc in BRorCtaus:
      if model=='stop':
        ctau = getctauBR(m,dm,ibc)
        BR = ibc
      else:
        ctau = ibc
        BR = 1
      BRCtau_str = '{}{}'.format("BR" if model=='stop' else 'ct',ibc)
      signal = '{}_M{}_{}_{}_{}'.format(model,m,m-dm,BRCtau_str,args.year).replace('.','p')
      syst = getSystUncert(dm,args.year,model)
      sf = 1
      if args.HEM:
        d_sig = getNumSigEvents(filepathSig, dirs, model, m, dm, ctau, BR, args.year, sf, HEMpath=filepathSigHEM, HEMfrac=0.6477)
      else:
        d_sig = getNumSigEvents(filepathSig, dirs, model, m, dm, ctau, BR, args.year, sf, HEMpath=None, HEMfrac=None)

      n_uncerts_sig = 0
      rate = ''
      sig_stat_uncert = ''
      sig_syst_uncert = ''
      syst_sources = ["trigger","vtxreco","jes","jer","uncEn","pu", "l1", "intlumi","lumi1718","qcdscale","pdf"]
      syst_sources_nice = ["CMS_EXO24033_METtrigger","CMS_EXO24033_vtxreco","CMS_scale_j","CMS_res_j","CMS_EXO24033_scale_met_unclustered_energy","CMS_pileup","CMS_l1_ecal_prefiring","lumi_"+str(args.year),"lumi_13TeV_1718","QCDscale_BSMsignal","CMS_EXO24033_PDF"]
      #syst_sources = ["vtxtkreco_Corr", "ML", "fake_MET", "MET_JetRes", "MET_JetEn", "MET_UnclusterEn", "trigger", "trigger_ele", "pu", "l1", "intlumi"]
      for i in range(len(channels)):
        rate += '\t{:.5g}'.format(d_sig['weighted'][i])
        rate += '\t'+'1.0'
        uncert_i = 0.0
        if not d_sig['raw'][i]==0:
          uncert_i = (d_sig['weighted'][i]/d_sig['raw'][i])
        sig_stat_uncert += 'stat_signal_{}\tgmN\t{:d}'.format(channels[i], d_sig['raw'][i]) \
                          +'\t-'*(i*len(processes)) \
                          +'\t{:.5g}'.format(uncert_i)+'\t-'*(len(processes)-1) \
                          +'\t-'*((len(channels)-i-1)*len(processes))+'\n'
        n_uncerts_sig += 1
      for iisource in range(len(syst_sources)): 
        isource = syst_sources[iisource]
        isource_nice = syst_sources_nice[iisource]
        if isource in syst:
          if isource=="vtxtkreco_Corr":
            syst_value = syst["vtxreco"]+syst["trackreco"]
          else:
            syst_value = syst[isource]
          sig_syst_uncert += '{}\tlnN'.format(isource_nice) \
                            +('\t{:.5g}'.format(1+syst_value)+'\t-'*(len(processes)-1))*len(channels) +'\n'
          n_uncerts_sig += 1
        else:
          assert (isource+"A" in syst) and (isource+"C" in syst)
          syst_valueA = syst[isource+"A"]
          syst_valueC = syst[isource+"C"]
          sig_syst_uncert += '{}\tlnN'.format(isource_nice) \
                            +(('\t{:.5g}'.format(1+syst_valueA)+'\t-'*(len(processes)-1))*2+('\t{:.5g}'.format(1+syst_valueC)+'\t-'*(len(processes)-1))*2)*int(len(channels)/4) +'\n'
          n_uncerts_sig += 1

      # mapveto
      mapvetosyst = getmapvetosyst(model,ctau,int(args.year))
      sig_syst_uncert += 'CMS_EXO24033_material_map\tlnN' \
          +('\t{:.5g}'.format(1+mapvetosyst['A'])+'\t-'*(len(processes)-1)+'\t{:.5g}'.format(1+mapvetosyst['B'])+'\t-'*(len(processes)-1)+'\t{:.5g}'.format(1+mapvetosyst['C'])+'\t-'*(len(processes)-1)+'\t{:.5g}'.format(1+mapvetosyst['D'])+'\t-'*(len(processes)-1))*int(len(channels)/4) +'\n'
      n_uncerts_sig += 1

      #sig_syst_uncert += 'signal_syst_PDF\tlnN' \
      #                  +('\t{:.5g}'.format(1+getPDFUncert(mg,dm,ctau,int(args.year)))+'\t-'*(len(processes)-1))*len(channels) +'\n'
      #n_uncerts_sig += 1

      template_new = template.replace('_SIGNAL_',signal)
      template_new = template.replace('_CTAU_',str(ctau))
      template_new = template_new.replace('_NCHANNELS_',str(len(channels)))
      template_new = template_new.replace('_NUNCERT_',str(n_uncerts_bkg+n_uncerts_sig+6))
      template_new = template_new.replace('_CHANNELNAME_',str('\t'.join(channels)))
      template_new = template_new.replace('_CHANNELNAMERATE_',channelnamerate)
      template_new = template_new.replace('_PROCESSNAMERATE_',processnamerate)
      template_new = template_new.replace('_PROCESSIDXRATE_',processidxrate)
      template_new = template_new.replace('_PROCESSRATE_',rate)
      template_new = template_new.replace('_STATUNCERTSIG_',sig_stat_uncert)
      template_new = template_new.replace('_STATUNCERTBKG_',bkg_stat_uncert)
      template_new = template_new.replace('_SYSTUNCERT_',syst_uncert)
      template_new = template_new.replace('_SYSTUNCERTSIG_',sig_syst_uncert)
      template_new = template_new.replace('_ABCD_',abcd)
      template_new = template_new.replace('_OBSERVATION_','\t'.join(map(lambda x:"{:.2f}".format(x),d_bkg['weighted'])))
      #if useData:
      #  template_new = template_new.replace('_OBSERVATION_','\t'.join(map(lambda x:"{:.2f}".format(x),d_data['raw'])))
      #else:
      #  template_new = template_new.replace('_OBSERVATION_','\t'.join(map(lambda x:"{:.2f}".format(x),d_bkg['weighted'])))
      f_datacard = open(os.path.join(args.output,signal.replace("_hist.pkl",'')+'_datacard.txt'),'w')
      f_datacard.write(template_new)
      f_datacard.close()


