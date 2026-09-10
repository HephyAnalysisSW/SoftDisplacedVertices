import os
import json
import shutil

YOUR_JSON = '/users/alikaan.gueven/AOD_to_nanoAOD/Plotter_run3/CMSSW_15_0_5/src/SoftDisplacedVertices/Samples/json/eos_central_C1N2_Run3.json'
# e.g. '/users/alikaan.gueven/AOD_to_nanoAOD/Material/CMSSW_10_6_30/src/SoftDisplacedVertices/Samples/json/Data_IsoMu2017.json'

with open(YOUR_JSON, 'r') as JSON:
    json_dict = json.load(JSON)

# /scratch-cbe/users/alikaan.gueven/ML_KAAN/


for k,v in json_dict['CustomNanoAOD']['dir'].items():
    dest = f'/scratch-cbe/users/alikaan.gueven/ML_KAAN/20260112/c1n2_run3/{k}'
    print(k, '→', dest)
    os.makedirs(dest, exist_ok=True)
    shutil.copytree(v, dest, dirs_exist_ok=True, copy_function=shutil.copy)
    for root, _, files in os.walk(dest):
        os.utime(root, None)
        for filename in files:
            os.utime(os.path.join(root, filename), None)
    