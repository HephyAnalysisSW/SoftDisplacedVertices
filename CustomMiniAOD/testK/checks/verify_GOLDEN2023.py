#!/usr/bin/env python3
import os
import json
import subprocess
from FWCore.PythonUtilities.LumiList import LumiList

CMSSW_BASE = os.environ['CMSSW_BASE']
SDV = os.path.join(CMSSW_BASE, 'src/SoftDisplacedVertices')
# GOLDEN_JSON = "https://cms-service-dqmdc.web.cern.ch/CAF/certification/Collisions23/Cert_Collisions2023_366442_370790_Golden.json"
# to_process = LumiList(url=GOLDEN_JSON)

to_process0 = [
    "jsons/Run2023B0_lumisToProcess.json",
    "jsons/Run2023C0_lumisToProcess.json",
    "jsons/Run2023D0_lumisToProcess.json",
]

to_process1 = [
    "jsons/Run2023B1_lumisToProcess.json",
    "jsons/Run2023C1_lumisToProcess.json",
    "jsons/Run2023D1_lumisToProcess.json",]


processed0 = LumiList(filename=os.path.join(SDV, "CustomMiniAOD/testK/checks/jsons/aggregatedLumis0.json"))
processed1 = LumiList(filename=os.path.join(SDV, "CustomMiniAOD/testK/checks/jsons/aggregatedLumis1.json"))

for p in to_process0:
    print(p)
    print(LumiList(filename=p) - processed0)
    print()

for p in to_process1:
    print(p)
    print(LumiList(filename=p) - processed1)
    print()
