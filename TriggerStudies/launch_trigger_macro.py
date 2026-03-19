#!/usr/bin/env python3

import ROOT
import argparse
import os
import sys
import array
import cmsstyle as CMS
import numpy as np
import json



data = {
    "2022prec": "muon2022prec",
    "2022pred": "muon2022pred",
    "2022poste" : "muon2022poste",
    "2022postf" : "muon2022postf",
    "2022postg" : "muon2022postg",
    "2023_0_prec" : "muon02023prec",
    "2023_1_prec" : "muon12023prec",
    "2023_0_postd" : "muon02023postd",
    "2023_1_postd" : "muon12023postd",
}


mc = {
    "2022pre": "wjetstolnu4jets_2022pre",
    "2022post": "wjetstolnu4jets_2022post",
    "2023pre": "wjetstolnu4jets_2023pre",
    "2023post": "wjetstolnu4jets_2023post",
}

#selections = ["IsoMu24","IsoMu24_no_iso","IsoMu27","IsoMu27_no_iso",]
selections = ["IsoMu27_no_iso","IsoMu24_no_iso"]
selections = ["IsoMu27_no_iso"]


for sel in selections:
    for era in data.keys():
        sample = data[era]
        print(sel, era, sample)
        cmd = f"python3 trigger_efficiency_debug.py --inputs /scratch/lisa.benato/SDV/trigger_muon_histo_{sel}_run3/{sample}/ --output /scratch/lisa.benato/SDV/trigger_efficiency_run3_{sel}/{sample}/ --era {era} --lumi 1"
        print(cmd)
        os.system(cmd)
        print("\n")

for sel in selections:
    for era in mc.keys():
        sample = mc[era]
        print(sel, era, sample)
        cmd = f"python3 trigger_efficiency_debug.py --inputs /scratch/lisa.benato/SDV/trigger_muon_histo_{sel}_run3/{sample}/ --output /scratch/lisa.benato/SDV/trigger_efficiency_run3_{sel}/{sample}/ --era {era} --lumi 1 --mc True"
        print(cmd)
        os.system(cmd)
        print("\n")


#python3 trigger_efficiency_debug.py --inputs /scratch/lisa.benato/SDV/trigger_muon_histo_IsoMu24_run3/wjetstolnu4jets_2023pre/ --output /scratch/lisa.benato/SDV/trigger_efficiency_run3_IsoMu24/wjetstolnu4jets_2023pre/ --era 2023_pre --lumi 1 --mc True
sh_era = ["2022pre","2022post","2023pre","2023post"]

#sh_era = ["2023pre"]

for sel in selections:
    for era in sh_era:
        cmd2 = f"python3 merge_trigger_efficiency.py --inputs /scratch/lisa.benato/SDV/trigger_efficiency_run3_{sel}/ --outputs /scratch/lisa.benato/SDV/trigger_efficiency_run3_{sel}/merged/ --era {era}  --lumi 1 --var nPV"#nomu
        print(cmd2)
        os.system(cmd2)
        print("\n")

        cmd2 = f"python3 merge_trigger_efficiency.py --inputs /scratch/lisa.benato/SDV/trigger_efficiency_run3_{sel}/ --outputs /scratch/lisa.benato/SDV/trigger_efficiency_run3_{sel}/merged/ --era {era}  --lumi 1 --var nomu"
        print(cmd2)
        os.system(cmd2)
        print("\n")

