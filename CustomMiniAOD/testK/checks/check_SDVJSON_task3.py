import ROOT
import numpy as np
from FWCore.PythonUtilities.LumiList import LumiList


import os
import subprocess
import json
import time
from DASAPI import format_runlumiquery
from get_RunLumiJSON import check_duplicates
from FWCore.PythonUtilities.LumiList import LumiList


def run_N_attempts(command, max_trials=5, timeoutSec=10, sleepSec=3):
    for attempt in range(1, max_trials + 1):
        # Execute the command while capturing output as text.
        try:
            result = subprocess.run(command,
                                    capture_output=True,
                                    text=True,
                                    timeout=timeoutSec  # seconds
                                    )
            print("Success!")
            break
        except subprocess.TimeoutExpired:
            print(f"Attempt {attempt} timed out.")
            if attempt < max_trials:
                time.sleep(sleepSec)  # optional: wait a bit before retrying
            else:
                print("All retries failed.")
                return None
    return result


CMSSW_BASE = os.environ['CMSSW_BASE']
SDV = os.path.join(CMSSW_BASE, 'src/SoftDisplacedVertices')

json2023 = os.path.join(SDV, "Samples/json/MC_Run3Summer23.json")
with open(json2023) as f:
    d = json.load(f)

sampleNames = list(d['AOD']['datasets'].keys())
logDict = {}

for sampleName in sampleNames:
    print(sampleName)
    print('-'*80)
    dataset_MiniAOD = d['CustomMiniAOD']['datasets'][sampleName]
    if isinstance(dataset_MiniAOD, str):
        dataset_MiniAOD=[dataset_MiniAOD]

    dir_NanoAOD = d['CustomNanoAOD']['dir'][sampleName]
    if isinstance(dir_NanoAOD, str):
        dir_NanoAOD=[dir_NanoAOD]

    merged_lumiDict_MiniAOD = {}
    for dataset_ in dataset_MiniAOD:
        arg = f"-query=run,lumi dataset={dataset_} instance=prod/phys03"
        command = ["dasgoclient", arg]
        
        result = run_N_attempts(command, max_trials=5, timeoutSec=10, sleepSec=3)
        lumiDict_MiniAOD = format_runlumiquery(result.stdout, format="runsAndLumis")
        for key, value in lumiDict_MiniAOD.items():
            if key not in merged_lumiDict_MiniAOD:
                merged_lumiDict_MiniAOD[key] = value
            else:
                merged_lumiDict_MiniAOD[key].extend(value)
    lumis_MiniAOD = LumiList(runsAndLumis=merged_lumiDict_MiniAOD)
    lumisToProcess = lumis_MiniAOD
    for dir_ in dir_NanoAOD:
        # Create a TChain for the "LuminosityBlocks" tree
        chain = ROOT.TChain("LuminosityBlocks")

        # Walk through all subdirectories and add ROOT files to the chain
        for root_dir, subdirs, files in os.walk(dir_):
            for file in files:
                if file.endswith(".root"):
                    filepath = os.path.join(root_dir, file)
                    chain.Add(filepath)
        tree = chain
        rdf  = ROOT.RDataFrame(tree)
        data = rdf.AsNumpy(["run", "luminosityBlock"])

        run_array       = data["run"]
        lumiblock_array = data["luminosityBlock"]

        # Group lumisections by run
        runs_dict = {}
        for run, lumi in zip(run_array, lumiblock_array):
            run =  int(run)   # Ensure the run is an integer
            lumi = int(lumi) # Ensure the lumi is an integer
            runs_dict.setdefault(run, []).append(lumi)

        lumis_NanoAOD = LumiList(runsAndLumis=runs_dict)
        chain.Reset()


    lumisToProcess -= lumis_NanoAOD
    logDict[sampleName] = lumisToProcess.compactList
    
    if lumisToProcess:
        print(lumisToProcess)
    else:
        print("All processed well.")

outJSON_PATH = os.path.join(SDV, "CustomMiniAOD/testK/checks/jsons/" + "check_sdvtask3.json")
with open(outJSON_PATH, 'w') as f:
    json.dump(logDict, f)






FILE_PATH = "/eos/vbc/experiments/cms/store/user/aguven/WtoLNu-4Jets_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23CustomNanoAODv12-130X_mcRun3_2023_realistic_v14-v1/250326_131001/0000/NanoAOD_1.root"

