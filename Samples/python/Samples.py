#!/usr/bin/env python

import json
from SoftDisplacedVertices.Samples.Sample import *

#stop_M600_580_ct2_2018
def _model(sample):
    s = sample if type(sample) == str else sample.name
    return s.split('_M')[0]

def _tau(sample):
    s = sample if type(sample) == str else sample.name
    x = s.index('ct')
    y = s.find('_',x+1)
    if y == -1:
        y = len(s)
    res = s[x+2:y].replace('p','.')
    return float(res)

def _mass(sample):
    s = sample if type(sample) == str else sample.name
    x = s.index('_M')
    y = s.find('_',x+1)
    if y == -1:
        y = len(s)
    return int(s[x+2:y])

def _massLSP(sample):
    '''
    For some SUSY models, there are two masses: mass of LLP and mass of LSP
    _mass figures out the mass of LLP and _massLSP figures out the mass of LSP
    This only works for splitSUSY currently
    '''
    s = sample if type(sample) == str else sample.name
    x = s.index('_M')
    x = s.find('_',x+1)
    y = s.find('_',x+1)
    if y == -1:
        y = len(s)
    return int(s[x+1:y])

def _set_signal_stuff(sample):
    sample.is_signal = True
    sample.model = _model(sample)
    sample.tau = _tau(sample)
    sample.mass = _mass(sample)
    sample.massLSP = _massLSP(sample)

def loadData(samples, json_path, label):
  with open(json_path,'r') as fj:
    d = json.load(fj)

  assert label in d

  for s in samples:
    setable = False
    if ("xs" in d) and (s.name in d['xs']):
      s.setxsec(d['xs'][s.name])
    if ('totalsumWeights' in d[label]) and (s.name in d[label]['totalsumWeights']):
      s.setNEvents(label,d[label]['totalsumWeights'][s.name])
    if ("dataset" in d[label]) and (s.name in d[label]["dataset"]):
      s.setDataset(label=label,dataset=d[label]["dataset"][s.name],instance='phys03')
      setable = True
    if ("dir" in d[label]) and (s.name in d[label]["dir"]):
      s.setDirs(label=label,dirs=d[label]["dir"][s.name])
      setable = True
    if ("logical_dir" in d[label]) and (s.name in d[label]["logical_dir"]):
      s.setEOSDirs(label=label,dirs=d[label]["logical_dir"][s.name])
      setable = True
    if not setable:
      print("Sample {} has no records!".format(s.name))

wlnu_2017 = [
    Sample("wjetstolnuht0100_2017",xsec=1530.0),
    Sample("wjetstolnuht0200_2017", xsec=405.96),
    Sample("wjetstolnuht0400_2017", xsec=54.75),
    Sample("wjetstolnuht0600_2017", xsec=13.27),
    Sample("wjetstolnuht0800_2017", xsec=5.97),
    Sample("wjetstolnuht1200_2017",xsec=1.40),
    Sample("wjetstolnuht2500_2017",xsec=0.03255),
    ]

wlnu_2017_100 = [Sample("wjetstolnuht0100_2017",xsec=1530.0)]

znunu_2017 = [
    Sample("zjetstonunuht0100_2017",xsec=344.83),
    Sample("zjetstonunuht0200_2017", xsec=95.53),
    Sample("zjetstonunuht0400_2017", xsec=13.20),
    Sample("zjetstonunuht0600_2017", xsec=3.148),
    Sample("zjetstonunuht0800_2017", xsec=1.451),
    Sample("zjetstonunuht1200_2017",xsec=0.355),
    Sample("zjetstonunuht2500_2017",xsec=0.00855),
    ]

qcd_2017 = [
  Sample("qcdht0050_2017", xsec=187700000.0),
  Sample("qcdht0100_2017", xsec=23640000.0),
  Sample("qcdht0200_2017", xsec=1555000.0),
  Sample("qcdht0300_2017", xsec=324500.0),
  Sample("qcdht0500_2017", xsec=30980.0),
  Sample("qcdht0700_2017", xsec=6444.0),
  Sample("qcdht1000_2017", xsec=1127.0),
  Sample("qcdht1500_2017", xsec=109.8),
  Sample("qcdht2000_2017", xsec=22.36)
]


top_2017 = [
  Sample("ttbar_2017",       xsec=833.9),
  Sample("st_tch_tbar_2017", xsec=80.00),
  Sample("st_tch_t_2017",    xsec=134.2),
  Sample("st_tW_tbar_2017",  xsec=39.68),
  Sample("st_tW_t_2017",     xsec=39.91)
]

stop_2017 = [
    Sample("stop_M600_588_ct200_2017", xsec=0.205),
    Sample("stop_M600_585_ct20_2017", xsec=0.205),
    Sample("stop_M600_580_ct2_2017", xsec=0.205),
    Sample("stop_M600_575_ct0p2_2017", xsec=0.205),
    Sample("stop_M1000_988_ct200_2017", xsec=0.00683),
    Sample("stop_M1000_985_ct20_2017", xsec=0.00683),
    Sample("stop_M1000_980_ct2_2017", xsec=0.00683),
    Sample("stop_M1000_975_ct0p2_2017", xsec=0.00683),
    Sample("stop_M1400_1388_ct200_2017", xsec=0.473E-03),
    Sample("stop_M1400_1385_ct20_2017", xsec=0.473E-03),
    Sample("stop_M1400_1380_ct2_2017", xsec=0.473E-03),
    Sample("stop_M1400_1375_ct0p2_2017", xsec=0.473E-03),
    ]

met_2018 = [
    Sample("met2018a", xsec=-1),
    Sample("met2018b", xsec=-1),
    Sample("met2018c", xsec=-1),
    Sample("met2018d", xsec=-1),
    Sample("met2018d_rest", xsec=-1),
    ]

znunu_2018 = [
    Sample("zjetstonunuht0100_2018",xsec=344.83),
    Sample("zjetstonunuht0200_2018", xsec=95.53),
    Sample("zjetstonunuht0400_2018", xsec=13.20),
    Sample("zjetstonunuht0600_2018", xsec=3.148),
    Sample("zjetstonunuht0800_2018", xsec=1.451),
    Sample("zjetstonunuht1200_2018",xsec=0.355),
    Sample("zjetstonunuht2500_2018",xsec=0.00855),
    ]

wlnu_2018 = [
    Sample("wjetstolnuht0100_2018",xsec=1530.0),
    Sample("wjetstolnuht0200_2018", xsec=405.96),
    Sample("wjetstolnuht0400_2018", xsec=54.75),
    Sample("wjetstolnuht0600_2018", xsec=13.27),
    Sample("wjetstolnuht0800_2018", xsec=5.97),
    Sample("wjetstolnuht1200_2018",xsec=1.40),
    Sample("wjetstolnuht2500_2018",xsec=0.03255),
    ]

qcd_2018 = [
  Sample("qcdht0050_2018", xsec=187700000.0),
  Sample("qcdht0100_2018", xsec=23640000.0),
  Sample("qcdht0200_2018", xsec=1555000.0),
  Sample("qcdht0300_2018", xsec=324500.0),
  Sample("qcdht0500_2018", xsec=30980.0),
  Sample("qcdht0700_2018", xsec=6444.0),
  Sample("qcdht1000_2018", xsec=1127.0),
  Sample("qcdht1500_2018", xsec=109.8),
  Sample("qcdht2000_2018", xsec=22.36)
]


top_2018 = [
  Sample("ttbar_2018",       xsec=833.9),
  Sample("st_tch_tbar_2018", xsec=80.00),
  Sample("st_tch_t_2018",    xsec=134.2),
  Sample("st_tW_tbar_2018",  xsec=39.68),
  Sample("st_tW_t_2018",     xsec=39.91)
]

stop_2018 = [
    Sample("stop_M600_588_ct200_2018", xsec=0.205),
    Sample("stop_M600_585_ct20_2018", xsec=0.205),
    Sample("stop_M600_580_ct2_2018", xsec=0.205),
    Sample("stop_M600_575_ct0p2_2018", xsec=0.205),
    Sample("stop_M1000_988_ct200_2018", xsec=0.00683),
    Sample("stop_M1000_985_ct20_2018", xsec=0.00683),
    Sample("stop_M1000_980_ct2_2018", xsec=0.00683),
    Sample("stop_M1000_975_ct0p2_2018", xsec=0.00683),
    Sample("stop_M1400_1388_ct200_2018", xsec=0.473E-03),
    Sample("stop_M1400_1385_ct20_2018", xsec=0.473E-03),
    Sample("stop_M1400_1380_ct2_2018", xsec=0.473E-03),
    Sample("stop_M1400_1375_ct0p2_2018", xsec=0.473E-03),
    ]



c1n2_2018 = [
    Sample("C1N2_M600_588_ct200_2018", xsec=20.1372e-03),
    Sample("C1N2_M600_585_ct20_2018", xsec=20.1372e-03),
    Sample("C1N2_M600_580_ct2_2018", xsec=20.1372e-03),
    Sample("C1N2_M600_575_ct0p2_2018", xsec=20.1372e-03),
    Sample("C1N2_M1000_988_ct200_2018", xsec=1.34352e-03),
    Sample("C1N2_M1000_985_ct20_2018", xsec=1.34352e-03),
    Sample("C1N2_M1000_980_ct2_2018", xsec=1.34352e-03),
    Sample("C1N2_M1000_975_ct0p2_2018", xsec=1.34352e-03),
    Sample("C1N2_M1400_1388_ct200_2018", xsec=0.131074e-03),
    Sample("C1N2_M1400_1385_ct20_2018", xsec=0.131074e-03),
    Sample("C1N2_M1400_1380_ct2_2018", xsec=0.131074e-03),
    Sample("C1N2_M1400_1375_ct0p2_2018", xsec=0.131074e-03),
    # Sample("C1N2_M1000_988_ct200_2018", xsec=1e-03),
    # Sample("C1N2_M1000_988_ct2_2018", xsec=1e-03),
    # Sample("C1N2_M1000_988_ct0p2_2018", xsec=1e-03),
    # Sample("C1N2_M1000_980_ct200_2018", xsec=1e-03),
    # Sample("C1N2_M1000_980_ct2_2018", xsec=1e-03),
    # Sample("C1N2_M1000_980_ct0p2_2018", xsec=1e-03),
    ]

all_bkg_2018 = [
  znunu_2018,
  wlnu_2018,
  qcd_2018,
]


all_sig_2018 = [
  stop_2018,
  c1n2_2018,
  stop_2017
]

all_samples = [
    wlnu_2017,
    znunu_2017,
    wlnu_2017,
    znunu_2017,
    met_2018,
    znunu_2018,
    wlnu_2018,
    qcd_2018,
    stop_2018,
    stop_2017,
    c1n2_2018,
    top_2018
]

tmp_2017 = [
  wlnu_2017,
  znunu_2017
]

all_signals = [
    stop_2018,
    stop_2017,
    c1n2_2018,
]

for samples in all_samples:
  for s in samples:
    exec("{} = s".format(s.name))

for samples in all_signals:
  for s in samples:
    _set_signal_stuff(s)

