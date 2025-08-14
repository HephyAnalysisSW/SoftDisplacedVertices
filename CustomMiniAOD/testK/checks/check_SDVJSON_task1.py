"""
Compares MiniAOD datasets vs NanoAOD datasets
---------------------------------------------

Steps:
1. Load the JSON file containing dataset information.
2. For each sample name, retrieve the MiniAOD datasets.
3. Use the DAS client to query the run and lumi information for each MiniAOD dataset.
4. Merge the lumi information to LumiList.

5. For each sample name, retrieve the NanoAOD datasets.
6. Use the DAS client to query the run and lumi information for each NanoAOD dataset.
7. Convert the NanoAOD lumi information to to LumiList.
8. Subtract the NanoAOD lumi information from the MiniAOD lumi information.
9. Log the results in a dictionary.

"""

import os
import subprocess
import json
import time
from DASAPI import format_runlumiquery
from get_RunLumiJSON import check_duplicates
from FWCore.PythonUtilities.LumiList import LumiList

def run_N_attempts(command, max_trials=5, timeoutSec=20, sleepSec=5):
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

json2022 = os.path.join(SDV, "Samples/json/MC_Run3Summer22.json")

with open(json2022) as f:
    d = json.load(f)

sampleNames = d['AOD']['datasets']


logDict = {}


for sampleName in sampleNames:                  # ttto2l2nu_bpix_2023, tttolnu2q_bpix_2023 ...
    print(sampleName)
    print('-'*80)
    dataset_MiniAOD = d['CustomMiniAOD']['datasets'][sampleName]

    if isinstance(dataset_MiniAOD, str):        # otherwise is a list anyways
        dataset_MiniAOD=[dataset_MiniAOD]

    merged_lumiDict_MiniAOD = {}    
    for dataset_ in dataset_MiniAOD:
        arg = f"-query=run,lumi dataset={dataset_} instance=prod/phys03"
        command = ["dasgoclient", arg]
        
        result = run_N_attempts(command)
        
        lumiDict_MiniAOD = format_runlumiquery(result.stdout, format="runsAndLumis")
        for key, value in lumiDict_MiniAOD.items():
            if key not in merged_lumiDict_MiniAOD:
                merged_lumiDict_MiniAOD[key] = value
            else:
                merged_lumiDict_MiniAOD[key].extend(value)
        
    check_duplicates(merged_lumiDict_MiniAOD)
    lumis_MiniAOD = LumiList(runsAndLumis=merged_lumiDict_MiniAOD)
    lumisToProcess = lumis_MiniAOD

    dataset_NanoAOD = d['CustomNanoAOD']['datasets'][sampleName]
    arg = f"-query=run,lumi dataset={dataset_NanoAOD} instance=prod/phys03"
    command = ["dasgoclient", arg]
    result = run_N_attempts(command)
    lumiDict_NanoAOD = format_runlumiquery(result.stdout, format="runsAndLumis")
    check_duplicates(lumiDict_NanoAOD)
    lumis_NanoAOD = LumiList(runsAndLumis=lumiDict_NanoAOD)
    lumisToProcess -= lumis_NanoAOD
    logDict[sampleName] = lumisToProcess.compactList
    
    if lumisToProcess:
        print(lumisToProcess)
    else:
        print("All processed well.")

outJSON_PATH = os.path.join(SDV, "CustomMiniAOD/testK/checks/jsons/" + "check_sdv.json")
with open(outJSON_PATH, 'w') as f:
    json.dump(logDict, f)
