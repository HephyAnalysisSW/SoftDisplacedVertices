"""
Compares MiniAOD datasets vs MiniAOD files
---------------------------------------------

Steps:
1. Load the JSON file containing dataset information.
2. For each sample name, retrieve the MiniAOD datasets.
3. Use the DAS client to query the run and lumi information for each MiniAOD dataset.
4. Convert the lumi information to LumiList.

5. For each sample name, retrieve the MiniAOD directories.
6. Use FWLite to query the run and lumi information for each MiniAOD file.
7. Convert the lumi information to to LumiList.
8. Subtract the lumi information of physical from the MiniAOD lumi information of dataset.
9. Log the results in a dictionary.

"""

import os
import subprocess
import json
import time
from DASAPI import format_runlumiquery
from get_RunLumiJSON import check_duplicates
from FWCore.PythonUtilities.LumiList import LumiList
import get_RunLumiJSON

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

sampleNames = list(d['AOD']['datasets'].keys())


logDict = {}
sampleNames = ['wjetstolnu4jets_ee_2022', 'zto2nu4jetsht0100_ee_2022', 'zto2nu4jetsht0200_ee_2022', 'zto2nu4jetsht0400_ee_2022', 'zto2nu4jetsht0800_ee_2022', 'zto2nu4jetsht1500_ee_2022', 'zto2nu4jetsht2500_ee_2022', 'qcd4jetsht0040_ee_2022', 'qcd4jetsht0070_ee_2022', 'qcd4jetsht0100_ee_2022', 'qcd4jetsht0200_ee_2022', 'qcd4jetsht0400_ee_2022', 'qcd4jetsht0600_ee_2022', 'qcd4jetsht0800_ee_2022', 'qcd4jetsht1000_ee_2022', 'qcd4jetsht1200_ee_2022', 'qcd4jetsht1500_ee_2022', 'qcd4jetsht2000_ee_2022', 'ttto4q_ee_2022', 'ttto2l2nu_ee_2022', 'tttolnu2q_ee_2022']
# sampleNames = ['qcd4jetsht1200_2022']
for sampleName in sampleNames:
    print(sampleName)
    print('-'*80)
    dataset_MiniAOD = d['CustomMiniAOD']['datasets'][sampleName]
    if isinstance(dataset_MiniAOD, str):
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
    
    lumis_MiniAOD = LumiList(runsAndLumis=merged_lumiDict_MiniAOD)
    lumisToProcess = lumis_MiniAOD

    dir_MiniAOD = d['CustomMiniAOD']['dir'][sampleName]
    if isinstance(dir_MiniAOD, str):
        dir_MiniAOD=[dir_MiniAOD]
    dir_patterns = []
    for dir_ in dir_MiniAOD:
        pattern = os.path.join(dir_, "**/*.root")
        dir_patterns.append(pattern)
        lumiDict_NanoAOD = get_RunLumiJSON.main(dir_patterns, nWorkers=18)
        lumis_NanoAOD = LumiList(compactList=lumiDict_NanoAOD)
        lumisToProcess -= lumis_NanoAOD
    logDict[sampleName] = lumisToProcess.compactList
    
    if lumisToProcess:
        print(lumisToProcess)
    else:
        print("All processed well.")

outJSON_PATH = os.path.join(SDV, "CustomMiniAOD/testK/checks/jsons/" + "check_sdv_task2.json")
with open(outJSON_PATH, 'w') as f:
    json.dump(logDict, f)
