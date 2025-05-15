#!/usr/bin/env python

import json
from SoftDisplacedVertices.Samples.Sample import *

def loadData(samples, json_path, label):
  with open(json_path,'r') as fj:
    d = json.load(fj)

  assert label in d

  for s in samples:
    if s.name in d[label]["dataset"]:
      s.setDataset(label=label,dataset=d[label]["dataset"][s.name],instance='phys03')
    elif s.name in d[label]["dir"]:
      s.setDirs(label=label,dirs=d[label]["dir"][s.name])
    else:
      print("Sample {} has no records!".format(b.name))

znunu_2018 = [
    Sample("zjetstonunuht0100_2018",xsec=280.35),
    Sample("zjetstonunuht0200_2018", xsec=77.67),
    Sample("zjetstonunuht0400_2018", xsec=10.73),
    Sample("zjetstonunuht0600_2018", xsec=2.559),
    Sample("zjetstonunuht0800_2018", xsec=1.1796),
    Sample("zjetstonunuht1200_2018",xsec=0.28833),
    Sample("zjetstonunuht2500_2018",xsec=0.006945),
    ]

wlnu_2018 = [
    Sample("wjetstolnuht0100_2018",xsec=1.255e+03),
    Sample("wjetstolnuht0200_2018", xsec=3.364e+02),
    Sample("wjetstolnuht0400_2018", xsec=4.526e+01),
    Sample("wjetstolnuht0600_2018", xsec=1.099e+01),
    Sample("wjetstolnuht0800_2018", xsec=4.924),
    Sample("wjetstolnuht1200_2018",xsec=1.157),
    Sample("wjetstolnuht2500_2018",xsec=2.623e-02),
    ]

stop_2018 = [
    Sample("stop_M600_588_ct200_2018", xsec=1e-03),
    Sample("stop_M600_585_ct20_2018", xsec=1e-03),
    Sample("stop_M600_580_ct2_2018", xsec=1e-03),
    Sample("stop_M600_575_ct0p2_2018", xsec=1e-03),
    Sample("stop_M1000_988_ct200_2018", xsec=1e-03),
    Sample("stop_M1000_985_ct20_2018", xsec=1e-03),
    Sample("stop_M1000_980_ct2_2018", xsec=1e-03),
    Sample("stop_M1000_975_ct0p2_2018", xsec=1e-03),
    ]

c1n2_2018 = [
    Sample("C1N2_M600_588_ct200_2018", xsec=1e-03),
    ]

all_samples = [
    znunu_2018,
    wlnu_2018,
    stop_2018,
    c1n2_2018,
]

for samples in all_samples:
  for s in samples:
    exec("{} = s".format(s.name))

