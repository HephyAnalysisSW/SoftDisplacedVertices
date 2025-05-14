import os
import subprocess
import json
import time
from DASAPI import format_runlumiquery
from get_RunLumiJSON import check_duplicates
from FWCore.PythonUtilities.LumiList import LumiList
import get_RunLumiJSON

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
sampleNames = sampleNames
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
        
        result = run_N_attempts(command, max_trials=5, timeoutSec=10, sleepSec=3)
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
    dir_patters = []
    for dir_ in dir_MiniAOD:
        pattern = os.path.join(dir_, "**/*.root")
        dir_patters.append(pattern)
        lumiDict_NanoAOD = get_RunLumiJSON.main(dir_patters, nWorkers=18)
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
