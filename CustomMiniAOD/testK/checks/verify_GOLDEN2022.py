#!/usr/bin/env python3
import os
import json
import subprocess
from FWCore.PythonUtilities.LumiList import LumiList

CMSSW_BASE = os.environ['CMSSW_BASE']
SDV = os.path.join(CMSSW_BASE, 'src/SoftDisplacedVertices')
GOLDEN_JSON = "https://cms-service-dqmdc.web.cern.ch/CAF/certification/Collisions23/Cert_Collisions2023_366442_370790_Golden.json"
to_process = LumiList(url=GOLDEN_JSON)

# to_process = [
#     "jsons/Run2023B0_lumisToProcess.json",
#     "jsons/Run2023C0_lumisToProcess.json",
#     "jsons/Run2023D0_lumisToProcess.json",
# ]



processed = LumiList(filename=os.path.join(SDV, "CustomMiniAOD/testK/checks/jsons/aggregatedLumis0.json"))

processed = [
    "jsons/Run2023B0_lumisToProcess.json",
    "jsons/Run2023C0_lumisToProcess.json",
    "jsons/Run2023D0_lumisToProcess.json",
]

print(to_process - processed)