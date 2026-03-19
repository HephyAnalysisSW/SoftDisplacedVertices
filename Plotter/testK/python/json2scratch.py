import os
import json
import shutil

with open('/groups/hephy/cms/alikaan.gueven/ParT/runs/vtx_PART-1111/jsons/Data_Run3_jetmet_official.json', 'r') as JSON:
    json_dict = json.load(JSON)

# /scratch-cbe/users/alikaan.gueven/ML_KAAN/


for k,v in json_dict['CustomNanoAOD']['dir'].items():
    dest = f'/scratch-cbe/users/alikaan.gueven/ML_KAAN/20260112/IVF_2022_data/{k}'
    print(k, '→', dest)
    os.makedirs(dest, exist_ok=True)
    shutil.copytree(v, dest, dirs_exist_ok=True)
    