import os
import json
import shutil

with open('/users/alikaan.gueven/AOD_to_nanoAOD/Material/CMSSW_10_6_30/src/SoftDisplacedVertices/Samples/json/Data_IsoMu2017.json', 'r') as JSON:
    json_dict = json.load(JSON)

# /scratch-cbe/users/alikaan.gueven/ML_KAAN/


for k,v in json_dict['CustomNanoAOD']['dir'].items():
    dest = f'/scratch-cbe/users/alikaan.gueven/ML_KAAN/20260112/{k}'
    print(k, '→', dest)
    os.makedirs(dest, exist_ok=True)
    shutil.copytree(v, dest, dirs_exist_ok=True)
    