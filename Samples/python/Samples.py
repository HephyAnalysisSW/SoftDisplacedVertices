#!/usr/bin/env python

import json
from SoftDisplacedVertices.Samples.Sample import *

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

muon_2017 = [
    Sample("muon2017b", xsec=-1),
    Sample("muon2017c", xsec=-1),
    Sample("muon2017d", xsec=-1),
    Sample("muon2017e", xsec=-1),
    Sample("muon2017f", xsec=-1),
        ]

met_2017 = [
    Sample("met2017b", xsec=-1),
    Sample("met2017c", xsec=-1),
    Sample("met2017d", xsec=-1),
    Sample("met2017e", xsec=-1),
    Sample("met2017f", xsec=-1),
    ]

wlnu_2017 = [
    Sample("wjetstolnuht0100_2017",xsec=1530.0),
    Sample("wjetstolnuht0200_2017", xsec=405.96),
    Sample("wjetstolnuht0400_2017", xsec=54.75),
    Sample("wjetstolnuht0600_2017", xsec=13.27),
    Sample("wjetstolnuht0800_2017", xsec=5.97),
    Sample("wjetstolnuht1200_2017",xsec=1.40),
    Sample("wjetstolnuht2500_2017",xsec=0.03255),
    ]

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
  Sample("ttbar_2017", xsec=833.9),
  Sample("st_tch_tbar_2017", xsec=80.0),
  Sample("st_tch_t_2017", xsec=134.2),
  Sample("st_tW_tbar_2017", xsec=39.68),
  Sample("st_tW_t_2017", xsec=39.91),
]

muon_2018 = [
    Sample("muon2018a", xsec=-1),
    Sample("muon2018b", xsec=-1),
    Sample("muon2018c", xsec=-1),
    Sample("muon2018d", xsec=-1),
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
  Sample("ttbar_2018", xsec=833.9),
  Sample("st_tch_tbar_2018", xsec=80.0),
  Sample("st_tch_t_2018", xsec=134.2),
  Sample("st_tW_tbar_2018", xsec=39.68),
  Sample("st_tW_t_2018", xsec=39.91),
]

met_2022Pre = [
        Sample("jetmet_2022c", xsec=-1),
        Sample("jetmet_2022d", xsec=-1),
        ]

muon_2022Pre = [
    Sample("muon2022prec", xsec=-1),
    Sample("muon2022pred", xsec=-1),
        ]

wlnu_2022Pre = [
    Sample("wjetstolnu4jets_2022pre",xsec=55390.0),
    ]

znunu_2022Pre = [
    Sample("zto2nu4jetsht0100_2022pre",xsec=273.7),
    Sample("zto2nu4jetsht0200_2022pre",xsec=75.96),
    Sample("zto2nu4jetsht0400_2022pre",xsec=13.19),
    Sample("zto2nu4jetsht0800_2022pre",xsec=1.364),
    Sample("zto2nu4jetsht1500_2022pre",xsec=0.09865),
    Sample("zto2nu4jetsht2500_2022pre",xsec=0.006699),
        ]

qcd_2022Pre = [
    Sample("qcd4jetsht0040_2022pre",xsec=311400000),
    Sample("qcd4jetsht0070_2022pre",xsec=58500000),
    Sample("qcd4jetsht0100_2022pre",xsec=25400000),
    Sample("qcd4jetsht0200_2022pre",xsec=1961000),
    Sample("qcd4jetsht0400_2022pre",xsec=95620),
    Sample("qcd4jetsht0600_2022pre",xsec=13540),
    Sample("qcd4jetsht0800_2022pre",xsec=3033),
    Sample("qcd4jetsht1000_2022pre",xsec=883.7),
    Sample("qcd4jetsht1200_2022pre",xsec=383.5),
    Sample("qcd4jetsht1500_2022pre",xsec=125.2),
    Sample("qcd4jetsht2000_2022pre",xsec=26.49),
        ]

top_2022Pre = [
    Sample("ttto4q_2022pre",xsec=422.1),
    Sample("ttto2l2nu_2022pre",xsec=404.6),
    Sample("tttolnu2q_2022pre",xsec=96.978),
        ]



met_2022Post = [
        Sample("jetmet_2022e", xsec=-1),
        Sample("jetmet_2022f", xsec=-1),
        Sample("jetmet_2022g", xsec=-1),
        ]

muon_2022Post = [
    Sample("muon2022poste", xsec=-1),
    Sample("muon2022postf", xsec=-1),
    Sample("muon2022postg", xsec=-1),
        ]

wlnu_2022Post = [
    Sample("wjetstolnu4jets_2022post",xsec=55390.0),
    ]

znunu_2022Post = [
    Sample("zto2nu4jetsht0100_2022post",xsec=273.7),
    Sample("zto2nu4jetsht0200_2022post",xsec=75.96),
    Sample("zto2nu4jetsht0400_2022post",xsec=13.19),
    Sample("zto2nu4jetsht0800_2022post",xsec=1.364),
    Sample("zto2nu4jetsht1500_2022post",xsec=0.09865),
    Sample("zto2nu4jetsht2500_2022post",xsec=0.006699),
        ]

qcd_2022Post = [
    Sample("qcd4jetsht0040_2022post",xsec=311400000),
    Sample("qcd4jetsht0070_2022post",xsec=58500000),
    Sample("qcd4jetsht0100_2022post",xsec=25400000),
    Sample("qcd4jetsht0200_2022post",xsec=1961000),
    Sample("qcd4jetsht0400_2022post",xsec=95620),
    Sample("qcd4jetsht0600_2022post",xsec=13540),
    Sample("qcd4jetsht0800_2022post",xsec=3033),
    Sample("qcd4jetsht1000_2022post",xsec=883.7),
    Sample("qcd4jetsht1200_2022post",xsec=383.5),
    Sample("qcd4jetsht1500_2022post",xsec=125.2),
    Sample("qcd4jetsht2000_2022post",xsec=26.49),
        ]

top_2022Post = [
    Sample("ttto4q_2022post",xsec=422.1),
    Sample("ttto2l2nu_2022post",xsec=404.6),
    Sample("tttolnu2q_2022post",xsec=96.978),
        ]

met_2023Pre = [
        Sample("jetmet0_2023c1", xsec=-1),
        Sample("jetmet0_2023c2", xsec=-1),
        Sample("jetmet0_2023c3", xsec=-1),
        Sample("jetmet0_2023c4", xsec=-1),
        Sample("jetmet1_2023c1", xsec=-1),
        Sample("jetmet1_2023c2", xsec=-1),
        Sample("jetmet1_2023c3", xsec=-1),
        Sample("jetmet1_2023c4", xsec=-1),
        ]

muon_2023Pre = [
    Sample("muon02023prec", xsec=-1),
    Sample("muon12023prec", xsec=-1),
        ]

wlnu_2023Pre = [
    Sample("wjetstolnu4jets_2023pre",xsec=55390.0),
    ]

znunu_2023Pre = [
    Sample("zto2nu4jetsht0100_2023pre",xsec=273.7),
    Sample("zto2nu4jetsht0200_2023pre",xsec=75.96),
    Sample("zto2nu4jetsht0400_2023pre",xsec=13.19),
    Sample("zto2nu4jetsht0800_2023pre",xsec=1.364),
    Sample("zto2nu4jetsht1500_2023pre",xsec=0.09865),
    Sample("zto2nu4jetsht2500_2023pre",xsec=0.006699),
        ]

qcd_2023Pre = [
    Sample("qcd4jetsht0040_2023pre",xsec=311400000),
    Sample("qcd4jetsht0070_2023pre",xsec=58500000),
    Sample("qcd4jetsht0100_2023pre",xsec=25400000),
    Sample("qcd4jetsht0200_2023pre",xsec=1961000),
    Sample("qcd4jetsht0400_2023pre",xsec=95620),
    Sample("qcd4jetsht0600_2023pre",xsec=13540),
    Sample("qcd4jetsht0800_2023pre",xsec=3033),
    Sample("qcd4jetsht1000_2023pre",xsec=883.7),
    Sample("qcd4jetsht1200_2023pre",xsec=383.5),
    Sample("qcd4jetsht1500_2023pre",xsec=125.2),
    Sample("qcd4jetsht2000_2023pre",xsec=26.49),
        ]

top_2023Pre = [
    Sample("ttto4q_2023pre",xsec=422.1),
    Sample("ttto2l2nu_2023pre",xsec=404.6),
    Sample("tttolnu2q_2023pre",xsec=96.978),
        ]

met_2023Post = [
        Sample("jetmet0_2023d1", xsec=-1),
        Sample("jetmet0_2023d2", xsec=-1),
        Sample("jetmet1_2023d1", xsec=-1),
        Sample("jetmet1_2023d2", xsec=-1),
        ]

muon_2023Post = [
    Sample("muon02023postd", xsec=-1),
    Sample("muon12023postd", xsec=-1),
        ]

wlnu_2023Post = [
    Sample("wjetstolnu4jets_2023post",xsec=55390.0),
    ]

znunu_2023Post = [
    Sample("zto2nu4jetsht0100_2023post",xsec=273.7),
    Sample("zto2nu4jetsht0200_2023post",xsec=75.96),
    Sample("zto2nu4jetsht0400_2023post",xsec=13.19),
    Sample("zto2nu4jetsht0800_2023post",xsec=1.364),
    Sample("zto2nu4jetsht1500_2023post",xsec=0.09865),
    Sample("zto2nu4jetsht2500_2023post",xsec=0.006699),
        ]

qcd_2023Post = [
    Sample("qcd4jetsht0040_2023post",xsec=311400000),
    Sample("qcd4jetsht0070_2023post",xsec=58500000),
    Sample("qcd4jetsht0100_2023post",xsec=25400000),
    Sample("qcd4jetsht0200_2023post",xsec=1961000),
    Sample("qcd4jetsht0400_2023post",xsec=95620),
    Sample("qcd4jetsht0600_2023post",xsec=13540),
    Sample("qcd4jetsht0800_2023post",xsec=3033),
    Sample("qcd4jetsht1000_2023post",xsec=883.7),
    Sample("qcd4jetsht1200_2023post",xsec=383.5),
    Sample("qcd4jetsht1500_2023post",xsec=125.2),
    Sample("qcd4jetsht2000_2023post",xsec=26.49),
        ]

top_2023Post = [
    Sample("ttto4q_2023post",xsec=422.1),
    Sample("ttto2l2nu_2023post",xsec=404.6),
    Sample("tttolnu2q_2023post",xsec=96.978),
        ]

# Samples 2024
# ------------------------------------------------------------------

wlnu_2024  = [Sample("wjetstolnu4jetsb1j_2024", xsec=9141),
              Sample("wjetstolnu4jetsb2j_2024", xsec=2931),
              Sample("wjetstolnu4jetsb3j_2024", xsec=864.6),
              Sample("wjetstolnu4jetsb4j_2024", xsec=417.8)]
znunu_2024 = [Sample("zto2nu4jetsht0100_2024", xsec=272.8),
              Sample("zto2nu4jetsht0200_2024", xsec=75.66),
              Sample("zto2nu4jetsht0400_2024", xsec=13.08),
              Sample("zto2nu4jetsht0800_2024", xsec=1.362),
              Sample("zto2nu4jetsht1500_2024", xsec=0.09793),
              Sample("zto2nu4jetsht2500_2024", xsec=0.006665)
              ]
qcd_2024 =   [Sample("qcd4jetsht0040_2024", xsec=312300000),
              Sample("qcd4jetsht0070_2024", xsec=58470000),
              Sample("qcd4jetsht0100_2024", xsec=25310000),
              Sample("qcd4jetsht0200_2024", xsec=1960000),
              Sample("qcd4jetsht0400_2024", xsec=97400),
              Sample("qcd4jetsht0600_2024", xsec=13560),
              Sample("qcd4jetsht0800_2024", xsec=3010),
              Sample("qcd4jetsht1000_2024", xsec=890.3),
              Sample("qcd4jetsht1200_2024", xsec=384.8),
              Sample("qcd4jetsht1500_2024", xsec=127.3),
              Sample("qcd4jetsht2000_2024", xsec=26.26),
              ]
top_2024 =   [Sample("ttto4q_2024"   , xsec=422.1),
              Sample("ttto2l2nu_2024", xsec=404.6),
              Sample("tttolnu2q_2024", xsec=96.978)
             ]

met_2024 = [
        Sample("jetmet0_2024c", xsec=-1),
        Sample("jetmet0_2024d", xsec=-1),
        Sample("jetmet0_2024e", xsec=-1),
        Sample("jetmet0_2024f", xsec=-1),
        Sample("jetmet0_2024g", xsec=-1),
        Sample("jetmet0_2024h", xsec=-1),
        Sample("jetmet0_2024i1", xsec=-1),
        Sample("jetmet0_2024i2", xsec=-1),
        Sample("jetmet1_2024c", xsec=-1),
        Sample("jetmet1_2024d", xsec=-1),
        Sample("jetmet1_2024e", xsec=-1),
        Sample("jetmet1_2024f", xsec=-1),
        Sample("jetmet1_2024g", xsec=-1),
        Sample("jetmet1_2024h", xsec=-1),
        Sample("jetmet1_2024i1", xsec=-1),
        Sample("jetmet1_2024i2", xsec=-1),
        ]

muon_2024 = [
    Sample("mu0_2024c", xsec=-1),
    Sample("mu0_2024d", xsec=-1),
    Sample("mu0_2024e", xsec=-1),
    Sample("mu0_2024f", xsec=-1),
    Sample("mu0_2024g", xsec=-1),
    Sample("mu0_2024h", xsec=-1),
    Sample("mu0_2024i1", xsec=-1),
    Sample("mu0_2024i2", xsec=-1),
    Sample("mu1_2024c", xsec=-1),
    Sample("mu1_2024d", xsec=-1),
    Sample("mu1_2024e", xsec=-1),
    Sample("mu1_2024f", xsec=-1),
    Sample("mu1_2024g", xsec=-1),
    Sample("mu1_2024h", xsec=-1),
    Sample("mu1_2024i1", xsec=-1),
    Sample("mu1_2024i2", xsec=-1),
        ]

# Signal 
stop_2017 = [
    Sample("stop_M400_375_ct0p2_2017", xsec=2.15),
    Sample("stop_M400_380_ct0p2_2017", xsec=2.15),
    Sample("stop_M400_380_ct2_2017", xsec=2.15),
    Sample("stop_M400_385_ct20_2017", xsec=2.15),
    Sample("stop_M400_385_ct2_2017", xsec=2.15),
    Sample("stop_M400_388_ct200_2017", xsec=2.15),
    Sample("stop_M400_388_ct20_2017", xsec=2.15),
    Sample("stop_M500_475_ct0p2_2017", xsec=0.609),
    Sample("stop_M500_480_ct0p2_2017", xsec=0.609),
    Sample("stop_M500_480_ct2_2017", xsec=0.609),
    Sample("stop_M500_485_ct20_2017", xsec=0.609),
    Sample("stop_M500_485_ct2_2017", xsec=0.609),
    Sample("stop_M500_488_ct200_2017", xsec=0.609),
    Sample("stop_M500_488_ct20_2017", xsec=0.609),
    Sample("stop_M600_575_ct0p2_2017", xsec=0.205),
    Sample("stop_M600_580_ct0p2_2017", xsec=0.205),
    Sample("stop_M600_580_ct2_2017", xsec=0.205),
    Sample("stop_M600_585_ct20_2017", xsec=0.205),
    Sample("stop_M600_585_ct2_2017", xsec=0.205),
    Sample("stop_M600_588_ct200_2017", xsec=0.205),
    Sample("stop_M600_588_ct20_2017", xsec=0.205),
    Sample("stop_M700_675_ct0p2_2017", xsec=0.0783),
    Sample("stop_M700_680_ct0p2_2017", xsec=0.0783),
    Sample("stop_M700_680_ct2_2017", xsec=0.0783),
    Sample("stop_M700_685_ct20_2017", xsec=0.0783),
    Sample("stop_M700_685_ct2_2017", xsec=0.0783),
    Sample("stop_M700_688_ct200_2017", xsec=0.0783),
    Sample("stop_M700_688_ct20_2017", xsec=0.0783),
    Sample("stop_M800_775_ct0p2_2017", xsec=0.0326),
    Sample("stop_M800_780_ct0p2_2017", xsec=0.0326),
    Sample("stop_M800_780_ct2_2017", xsec=0.0326),
    Sample("stop_M800_785_ct20_2017", xsec=0.0326),
    Sample("stop_M800_785_ct2_2017", xsec=0.0326),
    Sample("stop_M800_788_ct200_2017", xsec=0.0326),
    Sample("stop_M800_788_ct20_2017", xsec=0.0326),
    Sample("stop_M900_875_ct0p2_2017", xsec=0.0145),
    Sample("stop_M900_880_ct0p2_2017", xsec=0.0145),
    Sample("stop_M900_880_ct2_2017", xsec=0.0145),
    Sample("stop_M900_885_ct20_2017", xsec=0.0145),
    Sample("stop_M900_885_ct2_2017", xsec=0.0145),
    Sample("stop_M900_888_ct200_2017", xsec=0.0145),
    Sample("stop_M900_888_ct20_2017", xsec=0.0145),
    Sample("stop_M1000_975_ct0p2_2017", xsec=0.00683),
    Sample("stop_M1000_980_ct0p2_2017", xsec=0.00683),
    Sample("stop_M1000_980_ct2_2017", xsec=0.00683),
    Sample("stop_M1000_985_ct20_2017", xsec=0.00683),
    Sample("stop_M1000_985_ct2_2017", xsec=0.00683),
    Sample("stop_M1000_988_ct200_2017", xsec=0.00683),
    Sample("stop_M1000_988_ct20_2017", xsec=0.00683),
    Sample("stop_M1100_1075_ct0p2_2017", xsec=0.00335),
    Sample("stop_M1100_1080_ct0p2_2017", xsec=0.00335),
    Sample("stop_M1100_1080_ct2_2017", xsec=0.00335),
    Sample("stop_M1100_1085_ct20_2017", xsec=0.00335),
    Sample("stop_M1100_1085_ct2_2017", xsec=0.00335),
    Sample("stop_M1100_1088_ct200_2017", xsec=0.00335),
    Sample("stop_M1100_1088_ct20_2017", xsec=0.00335),
    Sample("stop_M1200_1175_ct0p2_2017", xsec=0.0017),
    Sample("stop_M1200_1180_ct0p2_2017", xsec=0.0017),
    Sample("stop_M1200_1180_ct2_2017", xsec=0.0017),
    Sample("stop_M1200_1185_ct20_2017", xsec=0.0017),
    Sample("stop_M1200_1185_ct2_2017", xsec=0.0017),
    Sample("stop_M1200_1188_ct200_2017", xsec=0.0017),
    Sample("stop_M1200_1188_ct20_2017", xsec=0.0017),
    Sample("stop_M1300_1275_ct0p2_2017", xsec=0.000887),
    Sample("stop_M1300_1280_ct0p2_2017", xsec=0.000887),
    Sample("stop_M1300_1280_ct2_2017", xsec=0.000887),
    Sample("stop_M1300_1285_ct20_2017", xsec=0.000887),
    Sample("stop_M1300_1285_ct2_2017", xsec=0.000887),
    Sample("stop_M1300_1288_ct200_2017", xsec=0.000887),
    Sample("stop_M1300_1288_ct20_2017", xsec=0.000887),
    Sample("stop_M1400_1375_ct0p2_2017", xsec=0.000473),
    Sample("stop_M1400_1380_ct0p2_2017", xsec=0.000473),
    Sample("stop_M1400_1380_ct2_2017", xsec=0.000473),
    Sample("stop_M1400_1385_ct20_2017", xsec=0.000473),
    Sample("stop_M1400_1385_ct2_2017", xsec=0.000473),
    Sample("stop_M1400_1388_ct200_2017", xsec=0.000473),
    Sample("stop_M1400_1388_ct20_2017", xsec=0.000473),
    ]

c1n2_2017 = [
    Sample("C1N2_M200_175_ct0p2_2017", xsec=1.807),
    Sample("C1N2_M200_175_ct200_2017", xsec=1.807),
    Sample("C1N2_M200_175_ct20_2017", xsec=1.807),
    Sample("C1N2_M200_175_ct2_2017", xsec=1.807),
    Sample("C1N2_M200_180_ct0p2_2017", xsec=1.807),
    Sample("C1N2_M200_180_ct200_2017", xsec=1.807),
    Sample("C1N2_M200_180_ct20_2017", xsec=1.807),
    Sample("C1N2_M200_180_ct2_2017", xsec=1.807),
    Sample("C1N2_M200_185_ct0p2_2017", xsec=1.807),
    Sample("C1N2_M200_185_ct200_2017", xsec=1.807),
    Sample("C1N2_M200_185_ct20_2017", xsec=1.807),
    Sample("C1N2_M200_185_ct2_2017", xsec=1.807),
    Sample("C1N2_M200_188_ct0p2_2017", xsec=1.807),
    Sample("C1N2_M200_188_ct200_2017", xsec=1.807),
    Sample("C1N2_M200_188_ct20_2017", xsec=1.807),
    Sample("C1N2_M200_188_ct2_2017", xsec=1.807),
    Sample("C1N2_M300_275_ct0p2_2017", xsec=0.3869),
    Sample("C1N2_M300_275_ct200_2017", xsec=0.3869),
    Sample("C1N2_M300_275_ct20_2017", xsec=0.3869),
    Sample("C1N2_M300_275_ct2_2017", xsec=0.3869),
    Sample("C1N2_M300_280_ct0p2_2017", xsec=0.3869),
    Sample("C1N2_M300_280_ct200_2017", xsec=0.3869),
    Sample("C1N2_M300_280_ct20_2017", xsec=0.3869),
    Sample("C1N2_M300_280_ct2_2017", xsec=0.3869),
    Sample("C1N2_M300_285_ct0p2_2017", xsec=0.3869),
    Sample("C1N2_M300_285_ct200_2017", xsec=0.3869),
    Sample("C1N2_M300_285_ct20_2017", xsec=0.3869),
    Sample("C1N2_M300_285_ct2_2017", xsec=0.3869),
    Sample("C1N2_M300_288_ct0p2_2017", xsec=0.3869),
    Sample("C1N2_M300_288_ct200_2017", xsec=0.3869),
    Sample("C1N2_M300_288_ct20_2017", xsec=0.3869),
    Sample("C1N2_M300_288_ct2_2017", xsec=0.3869),
    Sample("C1N2_M400_375_ct0p2_2017", xsec=0.121),
    Sample("C1N2_M400_375_ct200_2017", xsec=0.121),
    Sample("C1N2_M400_375_ct20_2017", xsec=0.121),
    Sample("C1N2_M400_375_ct2_2017", xsec=0.121),
    Sample("C1N2_M400_380_ct0p2_2017", xsec=0.121),
    Sample("C1N2_M400_380_ct200_2017", xsec=0.121),
    Sample("C1N2_M400_380_ct20_2017", xsec=0.121),
    Sample("C1N2_M400_380_ct2_2017", xsec=0.121),
    Sample("C1N2_M400_385_ct0p2_2017", xsec=0.121),
    Sample("C1N2_M400_385_ct200_2017", xsec=0.121),
    Sample("C1N2_M400_385_ct20_2017", xsec=0.121),
    Sample("C1N2_M400_385_ct2_2017", xsec=0.121),
    Sample("C1N2_M400_388_ct0p2_2017", xsec=0.121),
    Sample("C1N2_M400_388_ct200_2017", xsec=0.121),
    Sample("C1N2_M400_388_ct20_2017", xsec=0.121),
    Sample("C1N2_M400_388_ct2_2017", xsec=0.121),
    Sample("C1N2_M500_475_ct0p2_2017", xsec=0.04635),
    Sample("C1N2_M500_475_ct200_2017", xsec=0.04635),
    Sample("C1N2_M500_475_ct20_2017", xsec=0.04635),
    Sample("C1N2_M500_475_ct2_2017", xsec=0.04635),
    Sample("C1N2_M500_480_ct0p2_2017", xsec=0.04635),
    Sample("C1N2_M500_480_ct200_2017", xsec=0.04635),
    Sample("C1N2_M500_480_ct20_2017", xsec=0.04635),
    Sample("C1N2_M500_480_ct2_2017", xsec=0.04635),
    Sample("C1N2_M500_485_ct0p2_2017", xsec=0.04635),
    Sample("C1N2_M500_485_ct200_2017", xsec=0.04635),
    Sample("C1N2_M500_485_ct20_2017", xsec=0.04635),
    Sample("C1N2_M500_485_ct2_2017", xsec=0.04635),
    Sample("C1N2_M500_488_ct0p2_2017", xsec=0.04635),
    Sample("C1N2_M500_488_ct200_2017", xsec=0.04635),
    Sample("C1N2_M500_488_ct20_2017", xsec=0.04635),
    Sample("C1N2_M500_488_ct2_2017", xsec=0.04635),
    Sample("C1N2_M600_575_ct0p2_2017", xsec=0.02014),
    Sample("C1N2_M600_575_ct200_2017", xsec=0.02014),
    Sample("C1N2_M600_575_ct20_2017", xsec=0.02014),
    Sample("C1N2_M600_575_ct2_2017", xsec=0.02014),
    Sample("C1N2_M600_580_ct0p2_2017", xsec=0.02014),
    Sample("C1N2_M600_580_ct200_2017", xsec=0.02014),
    Sample("C1N2_M600_580_ct20_2017", xsec=0.02014),
    Sample("C1N2_M600_580_ct2_2017", xsec=0.02014),
    Sample("C1N2_M600_585_ct0p2_2017", xsec=0.02014),
    Sample("C1N2_M600_585_ct200_2017", xsec=0.02014),
    Sample("C1N2_M600_585_ct20_2017", xsec=0.02014),
    Sample("C1N2_M600_585_ct2_2017", xsec=0.02014),
    Sample("C1N2_M600_588_ct0p2_2017", xsec=0.02014),
    Sample("C1N2_M600_588_ct200_2017", xsec=0.02014),
    Sample("C1N2_M600_588_ct20_2017", xsec=0.02014),
    Sample("C1N2_M600_588_ct2_2017", xsec=0.02014),
    ]

stop_2018 = [
    Sample("stop_M400_375_ct0p2_2018", xsec=2.15),
    Sample("stop_M400_380_ct0p2_2018", xsec=2.15),
    Sample("stop_M400_380_ct2_2018", xsec=2.15),
    Sample("stop_M400_385_ct20_2018", xsec=2.15),
    Sample("stop_M400_385_ct2_2018", xsec=2.15),
    Sample("stop_M400_388_ct200_2018", xsec=2.15),
    Sample("stop_M400_388_ct20_2018", xsec=2.15),
    Sample("stop_M500_475_ct0p2_2018", xsec=0.609),
    Sample("stop_M500_480_ct0p2_2018", xsec=0.609),
    Sample("stop_M500_480_ct2_2018", xsec=0.609),
    Sample("stop_M500_485_ct20_2018", xsec=0.609),
    Sample("stop_M500_485_ct2_2018", xsec=0.609),
    Sample("stop_M500_488_ct200_2018", xsec=0.609),
    Sample("stop_M500_488_ct20_2018", xsec=0.609),
    Sample("stop_M600_575_ct0p2_2018", xsec=0.205),
    Sample("stop_M600_580_ct0p2_2018", xsec=0.205),
    Sample("stop_M600_580_ct2_2018", xsec=0.205),
    Sample("stop_M600_585_ct20_2018", xsec=0.205),
    Sample("stop_M600_585_ct2_2018", xsec=0.205),
    Sample("stop_M600_588_ct200_2018", xsec=0.205),
    Sample("stop_M600_588_ct20_2018", xsec=0.205),
    Sample("stop_M700_675_ct0p2_2018", xsec=0.0783),
    Sample("stop_M700_680_ct0p2_2018", xsec=0.0783),
    Sample("stop_M700_680_ct2_2018", xsec=0.0783),
    Sample("stop_M700_685_ct20_2018", xsec=0.0783),
    Sample("stop_M700_685_ct2_2018", xsec=0.0783),
    Sample("stop_M700_688_ct200_2018", xsec=0.0783),
    Sample("stop_M700_688_ct20_2018", xsec=0.0783),
    Sample("stop_M800_775_ct0p2_2018", xsec=0.0326),
    Sample("stop_M800_780_ct0p2_2018", xsec=0.0326),
    Sample("stop_M800_780_ct2_2018", xsec=0.0326),
    Sample("stop_M800_785_ct20_2018", xsec=0.0326),
    Sample("stop_M800_785_ct2_2018", xsec=0.0326),
    Sample("stop_M800_788_ct200_2018", xsec=0.0326),
    Sample("stop_M800_788_ct20_2018", xsec=0.0326),
    Sample("stop_M900_875_ct0p2_2018", xsec=0.0145),
    Sample("stop_M900_880_ct0p2_2018", xsec=0.0145),
    Sample("stop_M900_880_ct2_2018", xsec=0.0145),
    Sample("stop_M900_885_ct20_2018", xsec=0.0145),
    Sample("stop_M900_885_ct2_2018", xsec=0.0145),
    Sample("stop_M900_888_ct200_2018", xsec=0.0145),
    Sample("stop_M900_888_ct20_2018", xsec=0.0145),
    Sample("stop_M1000_975_ct0p2_2018", xsec=0.00683),
    Sample("stop_M1000_980_ct0p2_2018", xsec=0.00683),
    Sample("stop_M1000_980_ct2_2018", xsec=0.00683),
    Sample("stop_M1000_985_ct20_2018", xsec=0.00683),
    Sample("stop_M1000_985_ct2_2018", xsec=0.00683),
    Sample("stop_M1000_988_ct200_2018", xsec=0.00683),
    Sample("stop_M1000_988_ct20_2018", xsec=0.00683),
    Sample("stop_M1100_1075_ct0p2_2018", xsec=0.00335),
    Sample("stop_M1100_1080_ct0p2_2018", xsec=0.00335),
    Sample("stop_M1100_1080_ct2_2018", xsec=0.00335),
    Sample("stop_M1100_1085_ct20_2018", xsec=0.00335),
    Sample("stop_M1100_1085_ct2_2018", xsec=0.00335),
    Sample("stop_M1100_1088_ct200_2018", xsec=0.00335),
    Sample("stop_M1100_1088_ct20_2018", xsec=0.00335),
    Sample("stop_M1200_1175_ct0p2_2018", xsec=0.0017),
    Sample("stop_M1200_1180_ct0p2_2018", xsec=0.0017),
    Sample("stop_M1200_1180_ct2_2018", xsec=0.0017),
    Sample("stop_M1200_1185_ct20_2018", xsec=0.0017),
    Sample("stop_M1200_1185_ct2_2018", xsec=0.0017),
    Sample("stop_M1200_1188_ct200_2018", xsec=0.0017),
    Sample("stop_M1200_1188_ct20_2018", xsec=0.0017),
    Sample("stop_M1300_1275_ct0p2_2018", xsec=0.000887),
    Sample("stop_M1300_1280_ct0p2_2018", xsec=0.000887),
    Sample("stop_M1300_1280_ct2_2018", xsec=0.000887),
    Sample("stop_M1300_1285_ct20_2018", xsec=0.000887),
    Sample("stop_M1300_1285_ct2_2018", xsec=0.000887),
    Sample("stop_M1300_1288_ct200_2018", xsec=0.000887),
    Sample("stop_M1300_1288_ct20_2018", xsec=0.000887),
    Sample("stop_M1400_1375_ct0p2_2018", xsec=0.000473),
    Sample("stop_M1400_1380_ct0p2_2018", xsec=0.000473),
    Sample("stop_M1400_1380_ct2_2018", xsec=0.000473),
    Sample("stop_M1400_1385_ct20_2018", xsec=0.000473),
    Sample("stop_M1400_1385_ct2_2018", xsec=0.000473),
    Sample("stop_M1400_1388_ct200_2018", xsec=0.000473),
    Sample("stop_M1400_1388_ct20_2018", xsec=0.000473),
    ]

c1n2_2018 = [
    Sample("C1N2_M200_175_ct0p2_2018", xsec=1.807),
    Sample("C1N2_M200_175_ct200_2018", xsec=1.807),
    Sample("C1N2_M200_175_ct20_2018", xsec=1.807),
    Sample("C1N2_M200_175_ct2_2018", xsec=1.807),
    Sample("C1N2_M200_180_ct0p2_2018", xsec=1.807),
    Sample("C1N2_M200_180_ct200_2018", xsec=1.807),
    Sample("C1N2_M200_180_ct20_2018", xsec=1.807),
    Sample("C1N2_M200_180_ct2_2018", xsec=1.807),
    Sample("C1N2_M200_185_ct0p2_2018", xsec=1.807),
    Sample("C1N2_M200_185_ct200_2018", xsec=1.807),
    Sample("C1N2_M200_185_ct20_2018", xsec=1.807),
    Sample("C1N2_M200_185_ct2_2018", xsec=1.807),
    Sample("C1N2_M200_188_ct0p2_2018", xsec=1.807),
    Sample("C1N2_M200_188_ct200_2018", xsec=1.807),
    Sample("C1N2_M200_188_ct20_2018", xsec=1.807),
    Sample("C1N2_M200_188_ct2_2018", xsec=1.807),
    Sample("C1N2_M300_275_ct0p2_2018", xsec=0.3869),
    Sample("C1N2_M300_275_ct200_2018", xsec=0.3869),
    Sample("C1N2_M300_275_ct20_2018", xsec=0.3869),
    Sample("C1N2_M300_275_ct2_2018", xsec=0.3869),
    Sample("C1N2_M300_280_ct0p2_2018", xsec=0.3869),
    Sample("C1N2_M300_280_ct200_2018", xsec=0.3869),
    Sample("C1N2_M300_280_ct20_2018", xsec=0.3869),
    Sample("C1N2_M300_280_ct2_2018", xsec=0.3869),
    Sample("C1N2_M300_285_ct0p2_2018", xsec=0.3869),
    Sample("C1N2_M300_285_ct200_2018", xsec=0.3869),
    Sample("C1N2_M300_285_ct20_2018", xsec=0.3869),
    Sample("C1N2_M300_285_ct2_2018", xsec=0.3869),
    Sample("C1N2_M300_288_ct0p2_2018", xsec=0.3869),
    Sample("C1N2_M300_288_ct200_2018", xsec=0.3869),
    Sample("C1N2_M300_288_ct20_2018", xsec=0.3869),
    Sample("C1N2_M300_288_ct2_2018", xsec=0.3869),
    Sample("C1N2_M400_375_ct0p2_2018", xsec=0.121),
    Sample("C1N2_M400_375_ct200_2018", xsec=0.121),
    Sample("C1N2_M400_375_ct20_2018", xsec=0.121),
    Sample("C1N2_M400_375_ct2_2018", xsec=0.121),
    Sample("C1N2_M400_380_ct0p2_2018", xsec=0.121),
    Sample("C1N2_M400_380_ct200_2018", xsec=0.121),
    Sample("C1N2_M400_380_ct20_2018", xsec=0.121),
    Sample("C1N2_M400_380_ct2_2018", xsec=0.121),
    Sample("C1N2_M400_385_ct0p2_2018", xsec=0.121),
    Sample("C1N2_M400_385_ct200_2018", xsec=0.121),
    Sample("C1N2_M400_385_ct20_2018", xsec=0.121),
    Sample("C1N2_M400_385_ct2_2018", xsec=0.121),
    Sample("C1N2_M400_388_ct0p2_2018", xsec=0.121),
    Sample("C1N2_M400_388_ct200_2018", xsec=0.121),
    Sample("C1N2_M400_388_ct20_2018", xsec=0.121),
    Sample("C1N2_M400_388_ct2_2018", xsec=0.121),
    Sample("C1N2_M500_475_ct0p2_2018", xsec=0.04635),
    Sample("C1N2_M500_475_ct200_2018", xsec=0.04635),
    Sample("C1N2_M500_475_ct20_2018", xsec=0.04635),
    Sample("C1N2_M500_475_ct2_2018", xsec=0.04635),
    Sample("C1N2_M500_480_ct0p2_2018", xsec=0.04635),
    Sample("C1N2_M500_480_ct200_2018", xsec=0.04635),
    Sample("C1N2_M500_480_ct20_2018", xsec=0.04635),
    Sample("C1N2_M500_480_ct2_2018", xsec=0.04635),
    Sample("C1N2_M500_485_ct0p2_2018", xsec=0.04635),
    Sample("C1N2_M500_485_ct200_2018", xsec=0.04635),
    Sample("C1N2_M500_485_ct20_2018", xsec=0.04635),
    Sample("C1N2_M500_485_ct2_2018", xsec=0.04635),
    Sample("C1N2_M500_488_ct0p2_2018", xsec=0.04635),
    Sample("C1N2_M500_488_ct200_2018", xsec=0.04635),
    Sample("C1N2_M500_488_ct20_2018", xsec=0.04635),
    Sample("C1N2_M500_488_ct2_2018", xsec=0.04635),
    Sample("C1N2_M600_575_ct0p2_2018", xsec=0.02014),
    Sample("C1N2_M600_575_ct200_2018", xsec=0.02014),
    Sample("C1N2_M600_575_ct20_2018", xsec=0.02014),
    Sample("C1N2_M600_575_ct2_2018", xsec=0.02014),
    Sample("C1N2_M600_580_ct0p2_2018", xsec=0.02014),
    Sample("C1N2_M600_580_ct200_2018", xsec=0.02014),
    Sample("C1N2_M600_580_ct20_2018", xsec=0.02014),
    Sample("C1N2_M600_580_ct2_2018", xsec=0.02014),
    Sample("C1N2_M600_585_ct0p2_2018", xsec=0.02014),
    Sample("C1N2_M600_585_ct200_2018", xsec=0.02014),
    Sample("C1N2_M600_585_ct20_2018", xsec=0.02014),
    Sample("C1N2_M600_585_ct2_2018", xsec=0.02014),
    Sample("C1N2_M600_588_ct0p2_2018", xsec=0.02014),
    Sample("C1N2_M600_588_ct200_2018", xsec=0.02014),
    Sample("C1N2_M600_588_ct20_2018", xsec=0.02014),
    Sample("C1N2_M600_588_ct2_2018", xsec=0.02014),
    ]

old_central_sig17 = [*stop_2017, *c1n2_2017]
old_central_sig18 = [*stop_2018, *c1n2_2018]

private_sig18 = [
  Sample("C1N2ML_M200_175_ct2_2018",     xsec=1.807),
  Sample("C1N2ML_M200_175_ct20_2018",    xsec=1.807),
  Sample("C1N2ML_M200_175_ct200_2018" ,  xsec=1.807),
  Sample("C1N2ML_M200_185_ct2_2018",     xsec=1.807),
  Sample("C1N2ML_M200_185_ct20_2018",    xsec=1.807),
  Sample("C1N2ML_M200_185_ct200_2018" ,  xsec=1.807),
  Sample("C1N2ML_M200_190_ct2_2018",     xsec=1.807),
  Sample("C1N2ML_M200_190_ct20_2018",    xsec=1.807),
  Sample("C1N2ML_M200_190_ct200_2018" ,  xsec=1.807),
  Sample("C1N2ML_M200_195_ct2_2018",     xsec=1.807),
  Sample("C1N2ML_M200_195_ct20_2018",    xsec=1.807),
  Sample("C1N2ML_M200_195_ct200_2018" ,  xsec=1.807),
  Sample("C1N2ML_M500_475_ct2_2018",     xsec=0.046),
  Sample("C1N2ML_M500_475_ct20_2018",    xsec=0.046),
  Sample("C1N2ML_M500_475_ct200_2018" ,  xsec=0.046),
  Sample("C1N2ML_M500_485_ct2_2018",     xsec=0.046),
  Sample("C1N2ML_M500_485_ct20_2018",    xsec=0.046),
  Sample("C1N2ML_M500_485_ct200_2018" ,  xsec=0.046),
  Sample("C1N2ML_M500_490_ct2_2018",     xsec=0.046),
  Sample("C1N2ML_M500_490_ct20_2018",    xsec=0.046),
  Sample("C1N2ML_M500_490_ct200_2018" ,  xsec=0.046),
  Sample("C1N2ML_M500_495_ct2_2018",     xsec=0.046),
  Sample("C1N2ML_M500_495_ct20_2018",    xsec=0.046),
  Sample("C1N2ML_M500_495_ct200_2018" ,  xsec=0.046),
  Sample("stopML_M1000_975_ct0p2_2018",  xsec=0.007395),
  Sample("stopML_M1000_975_ct2_2018",    xsec=0.007395),
  Sample("stopML_M1000_975_ct20_2018" ,  xsec=0.007395),
  Sample("stopML_M1000_975_ct200_2018",  xsec=0.007395),
  Sample("stopML_M1000_980_ct0p2_2018",  xsec=0.007395),
  Sample("stopML_M1000_980_ct2_2018",    xsec=0.007395),
  Sample("stopML_M1000_980_ct20_2018" ,  xsec=0.007395),
  Sample("stopML_M1000_980_ct200_2018",  xsec=0.007395),
  Sample("stopML_M1000_985_ct0p2_2018",  xsec=0.007395),
  Sample("stopML_M1000_985_ct2_2018",    xsec=0.007395),
  Sample("stopML_M1000_985_ct20_2018" ,  xsec=0.007395),
  Sample("stopML_M1000_985_ct200_2018",  xsec=0.007395),
  Sample("stopML_M1000_988_ct0p2_2018",  xsec=0.007395),
  Sample("stopML_M1000_988_ct2_2018",    xsec=0.007395),
  Sample("stopML_M1000_988_ct20_2018" ,  xsec=0.007395),
  Sample("stopML_M1000_988_ct200_2018",  xsec=0.007395),
  Sample("stopML_M1200_1175_ct0p2_2018", xsec=0.001876),
  Sample("stopML_M1200_1175_ct2_2018" ,  xsec=0.001876),
  Sample("stopML_M1200_1175_ct20_2018",  xsec=0.001876),
  Sample("stopML_M1200_1175_ct200_2018", xsec=0.001876),
  Sample("stopML_M1200_1180_ct0p2_2018", xsec=0.001876),
  Sample("stopML_M1200_1180_ct2_2018" ,  xsec=0.001876),
  Sample("stopML_M1200_1180_ct20_2018",  xsec=0.001876),
  Sample("stopML_M1200_1180_ct200_2018", xsec=0.001876),
  Sample("stopML_M1200_1185_ct0p2_2018", xsec=0.001876),
  Sample("stopML_M1200_1185_ct2_2018" ,  xsec=0.001876),
  Sample("stopML_M1200_1185_ct20_2018",  xsec=0.001876),
  Sample("stopML_M1200_1185_ct200_2018", xsec=0.001876),
  Sample("stopML_M1200_1188_ct0p2_2018", xsec=0.001876),
  Sample("stopML_M1200_1188_ct2_2018" ,  xsec=0.001876),
  Sample("stopML_M1200_1188_ct20_2018",  xsec=0.001876),
  Sample("stopML_M1200_1188_ct200_2018", xsec=0.001876),
]

c1n2_reweight = [
Sample("C1N2_M200_188_ct0p5_2017", xsec=1.807),
Sample("C1N2_M200_188_ct1_2017", xsec=1.807),
Sample("C1N2_M200_188_ct5_2017", xsec=1.807),
Sample("C1N2_M200_188_ct10_2017", xsec=1.807),
Sample("C1N2_M200_188_ct50_2017", xsec=1.807),
Sample("C1N2_M200_188_ct100_2017", xsec=1.807),
Sample("C1N2_M200_185_ct0p5_2017", xsec=1.807),
Sample("C1N2_M200_185_ct1_2017", xsec=1.807),
Sample("C1N2_M200_185_ct5_2017", xsec=1.807),
Sample("C1N2_M200_185_ct10_2017", xsec=1.807),
Sample("C1N2_M200_185_ct50_2017", xsec=1.807),
Sample("C1N2_M200_185_ct100_2017", xsec=1.807),
Sample("C1N2_M200_180_ct0p5_2017", xsec=1.807),
Sample("C1N2_M200_180_ct1_2017", xsec=1.807),
Sample("C1N2_M200_180_ct5_2017", xsec=1.807),
Sample("C1N2_M200_180_ct10_2017", xsec=1.807),
Sample("C1N2_M200_180_ct50_2017", xsec=1.807),
Sample("C1N2_M200_180_ct100_2017", xsec=1.807),
Sample("C1N2_M200_175_ct0p5_2017", xsec=1.807),
Sample("C1N2_M200_175_ct1_2017", xsec=1.807),
Sample("C1N2_M200_175_ct5_2017", xsec=1.807),
Sample("C1N2_M200_175_ct10_2017", xsec=1.807),
Sample("C1N2_M200_175_ct50_2017", xsec=1.807),
Sample("C1N2_M200_175_ct100_2017", xsec=1.807),
Sample("C1N2_M300_288_ct0p5_2017", xsec=0.3869),
Sample("C1N2_M300_288_ct1_2017", xsec=0.3869),
Sample("C1N2_M300_288_ct5_2017", xsec=0.3869),
Sample("C1N2_M300_288_ct10_2017", xsec=0.3869),
Sample("C1N2_M300_288_ct50_2017", xsec=0.3869),
Sample("C1N2_M300_288_ct100_2017", xsec=0.3869),
Sample("C1N2_M300_285_ct0p5_2017", xsec=0.3869),
Sample("C1N2_M300_285_ct1_2017", xsec=0.3869),
Sample("C1N2_M300_285_ct5_2017", xsec=0.3869),
Sample("C1N2_M300_285_ct10_2017", xsec=0.3869),
Sample("C1N2_M300_285_ct50_2017", xsec=0.3869),
Sample("C1N2_M300_285_ct100_2017", xsec=0.3869),
Sample("C1N2_M300_280_ct0p5_2017", xsec=0.3869),
Sample("C1N2_M300_280_ct1_2017", xsec=0.3869),
Sample("C1N2_M300_280_ct5_2017", xsec=0.3869),
Sample("C1N2_M300_280_ct10_2017", xsec=0.3869),
Sample("C1N2_M300_280_ct50_2017", xsec=0.3869),
Sample("C1N2_M300_280_ct100_2017", xsec=0.3869),
Sample("C1N2_M300_275_ct0p5_2017", xsec=0.3869),
Sample("C1N2_M300_275_ct1_2017", xsec=0.3869),
Sample("C1N2_M300_275_ct5_2017", xsec=0.3869),
Sample("C1N2_M300_275_ct10_2017", xsec=0.3869),
Sample("C1N2_M300_275_ct50_2017", xsec=0.3869),
Sample("C1N2_M300_275_ct100_2017", xsec=0.3869),
Sample("C1N2_M400_388_ct0p5_2017", xsec=0.121),
Sample("C1N2_M400_388_ct1_2017", xsec=0.121),
Sample("C1N2_M400_388_ct5_2017", xsec=0.121),
Sample("C1N2_M400_388_ct10_2017", xsec=0.121),
Sample("C1N2_M400_388_ct50_2017", xsec=0.121),
Sample("C1N2_M400_388_ct100_2017", xsec=0.121),
Sample("C1N2_M400_385_ct0p5_2017", xsec=0.121),
Sample("C1N2_M400_385_ct1_2017", xsec=0.121),
Sample("C1N2_M400_385_ct5_2017", xsec=0.121),
Sample("C1N2_M400_385_ct10_2017", xsec=0.121),
Sample("C1N2_M400_385_ct50_2017", xsec=0.121),
Sample("C1N2_M400_385_ct100_2017", xsec=0.121),
Sample("C1N2_M400_380_ct0p5_2017", xsec=0.121),
Sample("C1N2_M400_380_ct1_2017", xsec=0.121),
Sample("C1N2_M400_380_ct5_2017", xsec=0.121),
Sample("C1N2_M400_380_ct10_2017", xsec=0.121),
Sample("C1N2_M400_380_ct50_2017", xsec=0.121),
Sample("C1N2_M400_380_ct100_2017", xsec=0.121),
Sample("C1N2_M400_375_ct0p5_2017", xsec=0.121),
Sample("C1N2_M400_375_ct1_2017", xsec=0.121),
Sample("C1N2_M400_375_ct5_2017", xsec=0.121),
Sample("C1N2_M400_375_ct10_2017", xsec=0.121),
Sample("C1N2_M400_375_ct50_2017", xsec=0.121),
Sample("C1N2_M400_375_ct100_2017", xsec=0.121),
Sample("C1N2_M500_488_ct0p5_2017", xsec=0.04635),
Sample("C1N2_M500_488_ct1_2017", xsec=0.04635),
Sample("C1N2_M500_488_ct5_2017", xsec=0.04635),
Sample("C1N2_M500_488_ct10_2017", xsec=0.04635),
Sample("C1N2_M500_488_ct50_2017", xsec=0.04635),
Sample("C1N2_M500_488_ct100_2017", xsec=0.04635),
Sample("C1N2_M500_485_ct0p5_2017", xsec=0.04635),
Sample("C1N2_M500_485_ct1_2017", xsec=0.04635),
Sample("C1N2_M500_485_ct5_2017", xsec=0.04635),
Sample("C1N2_M500_485_ct10_2017", xsec=0.04635),
Sample("C1N2_M500_485_ct50_2017", xsec=0.04635),
Sample("C1N2_M500_485_ct100_2017", xsec=0.04635),
Sample("C1N2_M500_480_ct0p5_2017", xsec=0.04635),
Sample("C1N2_M500_480_ct1_2017", xsec=0.04635),
Sample("C1N2_M500_480_ct5_2017", xsec=0.04635),
Sample("C1N2_M500_480_ct10_2017", xsec=0.04635),
Sample("C1N2_M500_480_ct50_2017", xsec=0.04635),
Sample("C1N2_M500_480_ct100_2017", xsec=0.04635),
Sample("C1N2_M500_475_ct0p5_2017", xsec=0.04635),
Sample("C1N2_M500_475_ct1_2017", xsec=0.04635),
Sample("C1N2_M500_475_ct5_2017", xsec=0.04635),
Sample("C1N2_M500_475_ct10_2017", xsec=0.04635),
Sample("C1N2_M500_475_ct50_2017", xsec=0.04635),
Sample("C1N2_M500_475_ct100_2017", xsec=0.04635),
Sample("C1N2_M600_588_ct0p5_2017", xsec=0.02014),
Sample("C1N2_M600_588_ct1_2017", xsec=0.02014),
Sample("C1N2_M600_588_ct5_2017", xsec=0.02014),
Sample("C1N2_M600_588_ct10_2017", xsec=0.02014),
Sample("C1N2_M600_588_ct50_2017", xsec=0.02014),
Sample("C1N2_M600_588_ct100_2017", xsec=0.02014),
Sample("C1N2_M600_585_ct0p5_2017", xsec=0.02014),
Sample("C1N2_M600_585_ct1_2017", xsec=0.02014),
Sample("C1N2_M600_585_ct5_2017", xsec=0.02014),
Sample("C1N2_M600_585_ct10_2017", xsec=0.02014),
Sample("C1N2_M600_585_ct50_2017", xsec=0.02014),
Sample("C1N2_M600_585_ct100_2017", xsec=0.02014),
Sample("C1N2_M600_580_ct0p5_2017", xsec=0.02014),
Sample("C1N2_M600_580_ct1_2017", xsec=0.02014),
Sample("C1N2_M600_580_ct5_2017", xsec=0.02014),
Sample("C1N2_M600_580_ct10_2017", xsec=0.02014),
Sample("C1N2_M600_580_ct50_2017", xsec=0.02014),
Sample("C1N2_M600_580_ct100_2017", xsec=0.02014),
Sample("C1N2_M600_575_ct0p5_2017", xsec=0.02014),
Sample("C1N2_M600_575_ct1_2017", xsec=0.02014),
Sample("C1N2_M600_575_ct5_2017", xsec=0.02014),
Sample("C1N2_M600_575_ct10_2017", xsec=0.02014),
Sample("C1N2_M600_575_ct50_2017", xsec=0.02014),
Sample("C1N2_M600_575_ct100_2017", xsec=0.02014),
Sample("C1N2_M200_188_ct0p5_2018", xsec=1.807),
Sample("C1N2_M200_188_ct1_2018", xsec=1.807),
Sample("C1N2_M200_188_ct5_2018", xsec=1.807),
Sample("C1N2_M200_188_ct10_2018", xsec=1.807),
Sample("C1N2_M200_188_ct50_2018", xsec=1.807),
Sample("C1N2_M200_188_ct100_2018", xsec=1.807),
Sample("C1N2_M200_185_ct0p5_2018", xsec=1.807),
Sample("C1N2_M200_185_ct1_2018", xsec=1.807),
Sample("C1N2_M200_185_ct5_2018", xsec=1.807),
Sample("C1N2_M200_185_ct10_2018", xsec=1.807),
Sample("C1N2_M200_185_ct50_2018", xsec=1.807),
Sample("C1N2_M200_185_ct100_2018", xsec=1.807),
Sample("C1N2_M200_180_ct0p5_2018", xsec=1.807),
Sample("C1N2_M200_180_ct1_2018", xsec=1.807),
Sample("C1N2_M200_180_ct5_2018", xsec=1.807),
Sample("C1N2_M200_180_ct10_2018", xsec=1.807),
Sample("C1N2_M200_180_ct50_2018", xsec=1.807),
Sample("C1N2_M200_180_ct100_2018", xsec=1.807),
Sample("C1N2_M200_175_ct0p5_2018", xsec=1.807),
Sample("C1N2_M200_175_ct1_2018", xsec=1.807),
Sample("C1N2_M200_175_ct5_2018", xsec=1.807),
Sample("C1N2_M200_175_ct10_2018", xsec=1.807),
Sample("C1N2_M200_175_ct50_2018", xsec=1.807),
Sample("C1N2_M200_175_ct100_2018", xsec=1.807),
Sample("C1N2_M300_288_ct0p5_2018", xsec=0.3869),
Sample("C1N2_M300_288_ct1_2018", xsec=0.3869),
Sample("C1N2_M300_288_ct5_2018", xsec=0.3869),
Sample("C1N2_M300_288_ct10_2018", xsec=0.3869),
Sample("C1N2_M300_288_ct50_2018", xsec=0.3869),
Sample("C1N2_M300_288_ct100_2018", xsec=0.3869),
Sample("C1N2_M300_285_ct0p5_2018", xsec=0.3869),
Sample("C1N2_M300_285_ct1_2018", xsec=0.3869),
Sample("C1N2_M300_285_ct5_2018", xsec=0.3869),
Sample("C1N2_M300_285_ct10_2018", xsec=0.3869),
Sample("C1N2_M300_285_ct50_2018", xsec=0.3869),
Sample("C1N2_M300_285_ct100_2018", xsec=0.3869),
Sample("C1N2_M300_280_ct0p5_2018", xsec=0.3869),
Sample("C1N2_M300_280_ct1_2018", xsec=0.3869),
Sample("C1N2_M300_280_ct5_2018", xsec=0.3869),
Sample("C1N2_M300_280_ct10_2018", xsec=0.3869),
Sample("C1N2_M300_280_ct50_2018", xsec=0.3869),
Sample("C1N2_M300_280_ct100_2018", xsec=0.3869),
Sample("C1N2_M300_275_ct0p5_2018", xsec=0.3869),
Sample("C1N2_M300_275_ct1_2018", xsec=0.3869),
Sample("C1N2_M300_275_ct5_2018", xsec=0.3869),
Sample("C1N2_M300_275_ct10_2018", xsec=0.3869),
Sample("C1N2_M300_275_ct50_2018", xsec=0.3869),
Sample("C1N2_M300_275_ct100_2018", xsec=0.3869),
Sample("C1N2_M400_388_ct0p5_2018", xsec=0.121),
Sample("C1N2_M400_388_ct1_2018", xsec=0.121),
Sample("C1N2_M400_388_ct5_2018", xsec=0.121),
Sample("C1N2_M400_388_ct10_2018", xsec=0.121),
Sample("C1N2_M400_388_ct50_2018", xsec=0.121),
Sample("C1N2_M400_388_ct100_2018", xsec=0.121),
Sample("C1N2_M400_385_ct0p5_2018", xsec=0.121),
Sample("C1N2_M400_385_ct1_2018", xsec=0.121),
Sample("C1N2_M400_385_ct5_2018", xsec=0.121),
Sample("C1N2_M400_385_ct10_2018", xsec=0.121),
Sample("C1N2_M400_385_ct50_2018", xsec=0.121),
Sample("C1N2_M400_385_ct100_2018", xsec=0.121),
Sample("C1N2_M400_380_ct0p5_2018", xsec=0.121),
Sample("C1N2_M400_380_ct1_2018", xsec=0.121),
Sample("C1N2_M400_380_ct5_2018", xsec=0.121),
Sample("C1N2_M400_380_ct10_2018", xsec=0.121),
Sample("C1N2_M400_380_ct50_2018", xsec=0.121),
Sample("C1N2_M400_380_ct100_2018", xsec=0.121),
Sample("C1N2_M400_375_ct0p5_2018", xsec=0.121),
Sample("C1N2_M400_375_ct1_2018", xsec=0.121),
Sample("C1N2_M400_375_ct5_2018", xsec=0.121),
Sample("C1N2_M400_375_ct10_2018", xsec=0.121),
Sample("C1N2_M400_375_ct50_2018", xsec=0.121),
Sample("C1N2_M400_375_ct100_2018", xsec=0.121),
Sample("C1N2_M500_488_ct0p5_2018", xsec=0.04635),
Sample("C1N2_M500_488_ct1_2018", xsec=0.04635),
Sample("C1N2_M500_488_ct5_2018", xsec=0.04635),
Sample("C1N2_M500_488_ct10_2018", xsec=0.04635),
Sample("C1N2_M500_488_ct50_2018", xsec=0.04635),
Sample("C1N2_M500_488_ct100_2018", xsec=0.04635),
Sample("C1N2_M500_485_ct0p5_2018", xsec=0.04635),
Sample("C1N2_M500_485_ct1_2018", xsec=0.04635),
Sample("C1N2_M500_485_ct5_2018", xsec=0.04635),
Sample("C1N2_M500_485_ct10_2018", xsec=0.04635),
Sample("C1N2_M500_485_ct50_2018", xsec=0.04635),
Sample("C1N2_M500_485_ct100_2018", xsec=0.04635),
Sample("C1N2_M500_480_ct0p5_2018", xsec=0.04635),
Sample("C1N2_M500_480_ct1_2018", xsec=0.04635),
Sample("C1N2_M500_480_ct5_2018", xsec=0.04635),
Sample("C1N2_M500_480_ct10_2018", xsec=0.04635),
Sample("C1N2_M500_480_ct50_2018", xsec=0.04635),
Sample("C1N2_M500_480_ct100_2018", xsec=0.04635),
Sample("C1N2_M500_475_ct0p5_2018", xsec=0.04635),
Sample("C1N2_M500_475_ct1_2018", xsec=0.04635),
Sample("C1N2_M500_475_ct5_2018", xsec=0.04635),
Sample("C1N2_M500_475_ct10_2018", xsec=0.04635),
Sample("C1N2_M500_475_ct50_2018", xsec=0.04635),
Sample("C1N2_M500_475_ct100_2018", xsec=0.04635),
Sample("C1N2_M600_588_ct0p5_2018", xsec=0.02014),
Sample("C1N2_M600_588_ct1_2018", xsec=0.02014),
Sample("C1N2_M600_588_ct5_2018", xsec=0.02014),
Sample("C1N2_M600_588_ct10_2018", xsec=0.02014),
Sample("C1N2_M600_588_ct50_2018", xsec=0.02014),
Sample("C1N2_M600_588_ct100_2018", xsec=0.02014),
Sample("C1N2_M600_585_ct0p5_2018", xsec=0.02014),
Sample("C1N2_M600_585_ct1_2018", xsec=0.02014),
Sample("C1N2_M600_585_ct5_2018", xsec=0.02014),
Sample("C1N2_M600_585_ct10_2018", xsec=0.02014),
Sample("C1N2_M600_585_ct50_2018", xsec=0.02014),
Sample("C1N2_M600_585_ct100_2018", xsec=0.02014),
Sample("C1N2_M600_580_ct0p5_2018", xsec=0.02014),
Sample("C1N2_M600_580_ct1_2018", xsec=0.02014),
Sample("C1N2_M600_580_ct5_2018", xsec=0.02014),
Sample("C1N2_M600_580_ct10_2018", xsec=0.02014),
Sample("C1N2_M600_580_ct50_2018", xsec=0.02014),
Sample("C1N2_M600_580_ct100_2018", xsec=0.02014),
Sample("C1N2_M600_575_ct0p5_2018", xsec=0.02014),
Sample("C1N2_M600_575_ct1_2018", xsec=0.02014),
Sample("C1N2_M600_575_ct5_2018", xsec=0.02014),
Sample("C1N2_M600_575_ct10_2018", xsec=0.02014),
Sample("C1N2_M600_575_ct50_2018", xsec=0.02014),
Sample("C1N2_M600_575_ct100_2018", xsec=0.02014),
]

stop_MLtraining_2018 = [
    Sample("stopML_M400_388_ct0p2_2018", xsec=1e-03),
    Sample("stopML_M400_388_ct2_2018", xsec=1e-03),
    Sample("stopML_M400_388_ct20_2018", xsec=1e-03),
    Sample("stopML_M400_388_ct200_2018", xsec=1e-03),
    Sample("stopML_M400_385_ct0p2_2018", xsec=1e-03),
    Sample("stopML_M400_385_ct2_2018", xsec=1e-03),
    Sample("stopML_M400_385_ct20_2018", xsec=1e-03),
    Sample("stopML_M400_385_ct200_2018", xsec=1e-03),
    Sample("stopML_M400_380_ct0p2_2018", xsec=1e-03),
    Sample("stopML_M400_380_ct2_2018", xsec=1e-03),
    Sample("stopML_M400_380_ct20_2018", xsec=1e-03),
    Sample("stopML_M400_380_ct200_2018", xsec=1e-03),
    Sample("stopML_M400_375_ct0p2_2018", xsec=1e-03),
    Sample("stopML_M400_375_ct2_2018", xsec=1e-03),
    Sample("stopML_M400_375_ct20_2018", xsec=1e-03),
    Sample("stopML_M400_375_ct200_2018", xsec=1e-03),
    Sample("stopML_M800_788_ct0p2_2018", xsec=1e-03),
    Sample("stopML_M800_788_ct2_2018", xsec=1e-03),
    Sample("stopML_M800_788_ct20_2018", xsec=1e-03),
    Sample("stopML_M800_788_ct200_2018", xsec=1e-03),
    Sample("stopML_M800_785_ct0p2_2018", xsec=1e-03),
    Sample("stopML_M800_785_ct2_2018", xsec=1e-03),
    Sample("stopML_M800_785_ct20_2018", xsec=1e-03),
    Sample("stopML_M800_785_ct200_2018", xsec=1e-03),
    Sample("stopML_M800_780_ct0p2_2018", xsec=1e-03),
    Sample("stopML_M800_780_ct2_2018", xsec=1e-03),
    Sample("stopML_M800_780_ct20_2018", xsec=1e-03),
    Sample("stopML_M800_780_ct200_2018", xsec=1e-03),
    Sample("stopML_M800_775_ct0p2_2018", xsec=1e-03),
    Sample("stopML_M800_775_ct2_2018", xsec=1e-03),
    Sample("stopML_M800_775_ct20_2018", xsec=1e-03),
    Sample("stopML_M800_775_ct200_2018", xsec=1e-03),
    Sample("stopML_M1200_1188_ct0p2_2018", xsec=1e-03),
    Sample("stopML_M1200_1188_ct2_2018", xsec=1e-03),
    Sample("stopML_M1200_1188_ct20_2018", xsec=1e-03),
    Sample("stopML_M1200_1188_ct200_2018", xsec=1e-03),
    Sample("stopML_M1200_1185_ct0p2_2018", xsec=1e-03),
    Sample("stopML_M1200_1185_ct2_2018", xsec=1e-03),
    Sample("stopML_M1200_1185_ct20_2018", xsec=1e-03),
    Sample("stopML_M1200_1185_ct200_2018", xsec=1e-03),
    Sample("stopML_M1200_1180_ct0p2_2018", xsec=1e-03),
    Sample("stopML_M1200_1180_ct2_2018", xsec=1e-03),
    Sample("stopML_M1200_1180_ct20_2018", xsec=1e-03),
    Sample("stopML_M1200_1180_ct200_2018", xsec=1e-03),
    Sample("stopML_M1200_1175_ct0p2_2018", xsec=1e-03),
    Sample("stopML_M1200_1175_ct2_2018", xsec=1e-03),
    Sample("stopML_M1200_1175_ct20_2018", xsec=1e-03),
    Sample("stopML_M1200_1175_ct200_2018", xsec=1e-03),
    Sample("stopML_M600_588_ct0p2_2018", xsec=1e-03),
    Sample("stopML_M600_588_ct2_2018", xsec=1e-03),
    Sample("stopML_M600_588_ct20_2018", xsec=1e-03),
    Sample("stopML_M600_588_ct200_2018", xsec=1e-03),
    Sample("stopML_M600_585_ct0p2_2018", xsec=1e-03),
    Sample("stopML_M600_585_ct2_2018", xsec=1e-03),
    Sample("stopML_M600_585_ct20_2018", xsec=1e-03),
    Sample("stopML_M600_585_ct200_2018", xsec=1e-03),
    Sample("stopML_M600_580_ct0p2_2018", xsec=1e-03),
    Sample("stopML_M600_580_ct2_2018", xsec=1e-03),
    Sample("stopML_M600_580_ct20_2018", xsec=1e-03),
    Sample("stopML_M600_580_ct200_2018", xsec=1e-03),
    Sample("stopML_M600_575_ct0p2_2018", xsec=1e-03),
    Sample("stopML_M600_575_ct2_2018", xsec=1e-03),
    Sample("stopML_M600_575_ct20_2018", xsec=1e-03),
    Sample("stopML_M600_575_ct200_2018", xsec=1e-03),
    Sample("stopML_M1000_988_ct0p2_2018", xsec=1e-03),
    Sample("stopML_M1000_988_ct2_2018", xsec=1e-03),
    Sample("stopML_M1000_988_ct20_2018", xsec=1e-03),
    Sample("stopML_M1000_988_ct200_2018", xsec=1e-03),
    Sample("stopML_M1000_985_ct0p2_2018", xsec=1e-03),
    Sample("stopML_M1000_985_ct2_2018", xsec=1e-03),
    Sample("stopML_M1000_985_ct20_2018", xsec=1e-03),
    Sample("stopML_M1000_985_ct200_2018", xsec=1e-03),
    Sample("stopML_M1000_980_ct0p2_2018", xsec=1e-03),
    Sample("stopML_M1000_980_ct2_2018", xsec=1e-03),
    Sample("stopML_M1000_980_ct20_2018", xsec=1e-03),
    Sample("stopML_M1000_980_ct200_2018", xsec=1e-03),
    Sample("stopML_M1000_975_ct0p2_2018", xsec=1e-03),
    Sample("stopML_M1000_975_ct2_2018", xsec=1e-03),
    Sample("stopML_M1000_975_ct20_2018", xsec=1e-03),
    Sample("stopML_M1000_975_ct200_2018", xsec=1e-03),
    Sample("stopML_M1400_1388_ct0p2_2018", xsec=1e-03),
    Sample("stopML_M1400_1388_ct2_2018", xsec=1e-03),
    Sample("stopML_M1400_1388_ct20_2018", xsec=1e-03),
    Sample("stopML_M1400_1388_ct200_2018", xsec=1e-03),
    Sample("stopML_M1400_1385_ct0p2_2018", xsec=1e-03),
    Sample("stopML_M1400_1385_ct2_2018", xsec=1e-03),
    Sample("stopML_M1400_1385_ct20_2018", xsec=1e-03),
    Sample("stopML_M1400_1385_ct200_2018", xsec=1e-03),
    Sample("stopML_M1400_1380_ct0p2_2018", xsec=1e-03),
    Sample("stopML_M1400_1380_ct2_2018", xsec=1e-03),
    Sample("stopML_M1400_1380_ct20_2018", xsec=1e-03),
    Sample("stopML_M1400_1380_ct200_2018", xsec=1e-03),
    Sample("stopML_M1400_1375_ct0p2_2018", xsec=1e-03),
    Sample("stopML_M1400_1375_ct2_2018", xsec=1e-03),
    Sample("stopML_M1400_1375_ct20_2018", xsec=1e-03),
    Sample("stopML_M1400_1375_ct200_2018", xsec=1e-03),
    Sample("stopML_M600_595_ct0p2_2018", xsec=1e-03),
    Sample("stopML_M600_595_ct2_2018", xsec=1e-03),
    Sample("stopML_M600_595_ct20_2018", xsec=1e-03),
    Sample("stopML_M600_595_ct200_2018", xsec=1e-03),
    Sample("stopML_M1000_995_ct0p2_2018", xsec=1e-03),
    Sample("stopML_M1000_995_ct2_2018", xsec=1e-03),
    Sample("stopML_M1000_995_ct20_2018", xsec=1e-03),
    Sample("stopML_M1000_995_ct200_2018", xsec=1e-03),
    ]
c1n2_lowdm_2018 = [
    Sample("C1N2_M200_190_ct20_2018", xsec=1.807),
    Sample("C1N2_M200_191_ct20_2018", xsec=1.807),
    Sample("C1N2_M200_192_ct20_2018", xsec=1.807),
    Sample("C1N2_M200_193_ct20_2018", xsec=1.807),
    Sample("C1N2_M200_194_ct20_2018", xsec=1.807),
    Sample("C1N2_M200_195_ct20_2018", xsec=1.807),
    ]
MLstudy_2018 = [
    Sample("stopMLstudy_M1000_988_ct0p2_2018", xsec=0.00683),
    Sample("stopMLstudy_M1000_988_ct20_2018", xsec=0.00683),
    Sample("stopMLstudy_M1000_995_ct0p2_2018", xsec=0.00683),
    Sample("stopMLstudy_M1000_995_ct20_2018", xsec=0.00683),
    Sample("C1N2MLstudy_M400_388_ct0p2_2018", xsec=0.121),
    Sample("C1N2MLstudy_M400_388_ct20_2018", xsec=0.121),
    Sample("C1N2MLstudy_M400_395_ct0p2_2018", xsec=0.121),
    Sample("C1N2MLstudy_M400_395_ct20_2018", xsec=0.121),
    ]

C1N2_MLtraining_2018 = [
        Sample("C1N2ML_M200_195_ct2_2018", xsec=1e-03),
        Sample("C1N2ML_M200_195_ct20_2018", xsec=1e-03),
        Sample("C1N2ML_M200_195_ct200_2018", xsec=1e-03),
        Sample("C1N2ML_M200_190_ct2_2018", xsec=1e-03),
        Sample("C1N2ML_M200_190_ct20_2018", xsec=1e-03),
        Sample("C1N2ML_M200_190_ct200_2018", xsec=1e-03),
        Sample("C1N2ML_M200_185_ct2_2018", xsec=1e-03),
        Sample("C1N2ML_M200_185_ct20_2018", xsec=1e-03),
        Sample("C1N2ML_M200_185_ct200_2018", xsec=1e-03),
        Sample("C1N2ML_M200_175_ct2_2018", xsec=1e-03),
        Sample("C1N2ML_M200_175_ct20_2018", xsec=1e-03),
        Sample("C1N2ML_M200_175_ct200_2018", xsec=1e-03),
        Sample("C1N2ML_M500_495_ct2_2018", xsec=1e-03),
        Sample("C1N2ML_M500_495_ct20_2018", xsec=1e-03),
        Sample("C1N2ML_M500_495_ct200_2018", xsec=1e-03),
        Sample("C1N2ML_M500_490_ct2_2018", xsec=1e-03),
        Sample("C1N2ML_M500_490_ct20_2018", xsec=1e-03),
        Sample("C1N2ML_M500_490_ct200_2018", xsec=1e-03),
        Sample("C1N2ML_M500_485_ct2_2018", xsec=1e-03),
        Sample("C1N2ML_M500_485_ct20_2018", xsec=1e-03),
        Sample("C1N2ML_M500_485_ct200_2018", xsec=1e-03),
        Sample("C1N2ML_M500_475_ct2_2018", xsec=1e-03),
        Sample("C1N2ML_M500_475_ct20_2018", xsec=1e-03),
        Sample("C1N2ML_M500_475_ct200_2018", xsec=1e-03),
        Sample("C1N2ML_M800_795_ct2_2018", xsec=1e-03),
        Sample("C1N2ML_M800_795_ct20_2018", xsec=1e-03),
        Sample("C1N2ML_M800_795_ct200_2018", xsec=1e-03),
        Sample("C1N2ML_M800_790_ct2_2018", xsec=1e-03),
        Sample("C1N2ML_M800_790_ct20_2018", xsec=1e-03),
        Sample("C1N2ML_M800_790_ct200_2018", xsec=1e-03),
        Sample("C1N2ML_M800_785_ct2_2018", xsec=1e-03),
        Sample("C1N2ML_M800_785_ct20_2018", xsec=1e-03),
        Sample("C1N2ML_M800_785_ct200_2018", xsec=1e-03),
        Sample("C1N2ML_M800_775_ct2_2018", xsec=1e-03),
        Sample("C1N2ML_M800_775_ct20_2018", xsec=1e-03),
        Sample("C1N2ML_M800_775_ct200_2018", xsec=1e-03),
        ]

# 2024
c1n2_2024 = [
    Sample("C1N2_M400_398_ct0p2_2024", xsec=0.121),
    Sample("C1N2_M400_398_ct2_2024", xsec=0.121),
    Sample("C1N2_M400_398_ct20_2024", xsec=0.121),
    Sample("C1N2_M400_398_ct200_2024", xsec=0.121),
    Sample("C1N2_M400_395_ct0p2_2024", xsec=0.121),
    Sample("C1N2_M400_395_ct2_2024", xsec=0.121),
    Sample("C1N2_M400_395_ct20_2024", xsec=0.121),
    Sample("C1N2_M400_395_ct200_2024", xsec=0.121),
    Sample("C1N2_M400_388_ct0p2_2024", xsec=0.121),
    Sample("C1N2_M400_388_ct2_2024", xsec=0.121),
    Sample("C1N2_M400_388_ct20_2024", xsec=0.121),
    Sample("C1N2_M400_388_ct200_2024", xsec=0.121),
    ]

stop_2024 = [
    Sample("stop_M1000_988_ct200_2024", xsec=0.00683),
    Sample("stop_M1000_988_ct20_2024", xsec=0.00683),
    Sample("stop_M1000_988_ct2_2024", xsec=0.00683),
    Sample("stop_M1000_988_ct0p2_2024", xsec=0.00683),
        ]


all_samples = [
    muon_2017,
    met_2017,
    wlnu_2017,
    znunu_2017,
    qcd_2017,
    top_2017,
    stop_2017,
    c1n2_2017,
    muon_2018,
    met_2018,
    znunu_2018,
    wlnu_2018,
    qcd_2018,
    stop_2018,
    # c1n2_2018,
    top_2018,
    # c1n2_reweight,
    # c1n2_lowdm_2018,
    # stop_MLtraining_2018,
    # C1N2_MLtraining_2018,
    # MLstudy_2018,
    private_sig18,
    old_central_sig17,
    old_central_sig18,
    c1n2_2024,
    stop_2024,
    met_2022Pre,
    muon_2022Pre,
    wlnu_2022Pre,
    znunu_2022Pre,
    qcd_2022Pre,
    top_2022Pre,
    met_2022Post,
    muon_2022Post,
    wlnu_2022Post,
    znunu_2022Post,
    qcd_2022Post,
    top_2022Post,
    met_2023Pre,
    muon_2023Pre,
    wlnu_2023Pre,
    znunu_2023Pre,
    qcd_2023Pre,
    top_2023Pre,
    met_2023Post,
    muon_2023Post,
    wlnu_2023Post,
    znunu_2023Post,
    qcd_2023Post,
    top_2023Post,
    met_2024,
    wlnu_2024,
    znunu_2024,
    qcd_2024,
    top_2024,
    muon_2024
]

all_signals = [
    stop_2017,
    c1n2_2017,
    stop_2018,
    #c1n2_2018,
    #c1n2_reweight,
    #c1n2_lowdm_2018,
    #stop_MLtraining_2018,
    #C1N2_MLtraining_2018,
    #MLstudy_2018,
    c1n2_2024,
    stop_2024,
    old_central_sig17,
    old_central_sig18,
    private_sig18,
]

all_bkg_2017 = [
  *znunu_2017,
  *wlnu_2017,
  *qcd_2017,
  *top_2017
]

all_bkg_2018 = [
  *znunu_2018,
  *wlnu_2018,
  *qcd_2018,
  *top_2018
]

bkg_2022Pre = [
   *wlnu_2022Pre,
   *znunu_2022Pre,
   *qcd_2022Pre,
   *top_2022Pre
]

bkg_2022Post = [
   *wlnu_2022Post,
   *znunu_2022Post,
   *qcd_2022Post,
   *top_2022Post
]

bkg_2023Pre = [
   *wlnu_2023Pre,
   *znunu_2023Pre,
   *qcd_2023Pre,
   *top_2023Pre
]

bkg_2023Post = [
   *wlnu_2023Post,
   *znunu_2023Post,
   *qcd_2023Post,
   *top_2023Post
]

all_bkg_2024 = [
  *wlnu_2024,
  *znunu_2024,
  *qcd_2024,
  *top_2024
]

for samples in all_samples:
  for s in samples:
    exec("{} = s".format(s.name))

for samples in all_signals:
  for s in samples:
    _set_signal_stuff(s)

