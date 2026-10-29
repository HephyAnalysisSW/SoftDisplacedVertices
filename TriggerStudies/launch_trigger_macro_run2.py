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
    "2017b": "muon2017b",
    "2017c": "muon2017c",
    "2017d": "muon2017d",
    "2017e": "muon2017e",
    "2017f": "muon2017f",
    "2018a": "muon2018a",
    "2018b": "muon2018b",
    "2018c": "muon2018c",
    "2018d": "muon2018d",
}


mc = {
    "0100_2017": "wjetstolnuht0100_2017",
    "0200_2017": "wjetstolnuht0200_2017",
    "0400_2017": "wjetstolnuht0400_2017",
    "0600_2017": "wjetstolnuht0600_2017",
    "0800_2017": "wjetstolnuht0800_2017",
    "1200_2017": "wjetstolnuht1200_2017",
    "2500_2017": "wjetstolnuht2500_2017",
    "0100_2018": "wjetstolnuht0100_2018",
    "0200_2018": "wjetstolnuht0200_2018",
    "0400_2018": "wjetstolnuht0400_2018",
    "0600_2018": "wjetstolnuht0600_2018",
    "0800_2018": "wjetstolnuht0800_2018",
    "1200_2018": "wjetstolnuht1200_2018",
    "2500_2018": "wjetstolnuht2500_2018",
}

#selections = ["IsoMu24","IsoMu24_no_iso","IsoMu27","IsoMu27_no_iso",]
selections = ["IsoMu27_no_iso"]

'''
for sel in selections:
    for era in data.keys():
        sample = data[era]
        print(sel, era, sample)
        cmd = f"python3 trigger_efficiency_debug_v3.py --inputs /scratch/lisa.benato/SDV/trigger_muon_histo_{sel}_run2_v3/{sample}/ --output /scratch/lisa.benato/SDV/trigger_efficiency_run2_{sel}_v3/{sample}/ --era {era} --lumi 1"
        print(cmd)
        os.system(cmd)
        print("\n")


for sel in selections:
    for era in mc.keys():
        sample = mc[era]
        print(sel, era, sample)
        cmd = f"python3 trigger_efficiency_debug_v3.py --inputs /scratch/lisa.benato/SDV/trigger_muon_histo_{sel}_run2_v3/{sample}/ --output /scratch/lisa.benato/SDV/trigger_efficiency_run2_{sel}_v3/{sample}/ --era {era} --lumi 1 --mc True"
        print(cmd)
        os.system(cmd)
        print("\n")

'''
        
#python3 trigger_efficiency_debug.py --inputs /scratch/lisa.benato/SDV/trigger_muon_histo_IsoMu24_run2/wjetstolnu4jets_2023pre/ --output /scratch/lisa.benato/SDV/trigger_efficiency_run2_IsoMu24/wjetstolnu4jets_2023pre/ --era 2023_pre --lumi 1 --mc True
sh_era = ["2017","2018"]

for sel in selections:
    for era in sh_era:
        cmd2 = f"python3 merge_trigger_efficiency.py --inputs /scratch/lisa.benato/SDV/trigger_efficiency_run2_{sel}_v3/ --outputs /scratch/lisa.benato/SDV/trigger_efficiency_run2_{sel}_v3/merged/ --era {era}  --lumi 1 --var nPV"#nomu
        print(cmd2)
        os.system(cmd2)
        print("\n")
        cmd2 = f"python3 merge_trigger_efficiency.py --inputs /scratch/lisa.benato/SDV/trigger_efficiency_run2_{sel}_v3/ --outputs /scratch/lisa.benato/SDV/trigger_efficiency_run2_{sel}_v3/merged/ --era {era}  --lumi 1 --var nomu"
        print(cmd2)
        os.system(cmd2)
        print("\n")
