from subprocess import run, PIPE
import SoftDisplacedVertices.Samples.Samples as ss
import re
import json
import os

import inspect

def print_info():
    # Get the caller's local variables
    caller_locals = inspect.currentframe().f_back.f_locals

    # Define which variables to print and how to label them
    keys = {
        's_type':  's_type',
        'json_db': 'json',
        'tier':    'tier',
        'year':    'year',
        'outDir':  'outDir',
        'config':  'config'
    }
    print()
    for key, label in keys.items():
        if key in caller_locals:
            # For 'json_db' and 'tier', assume you want to use the key from 's_type'
            if key in ['json_db', 'tier'] and 's_type' in caller_locals:
                value = caller_locals[key][caller_locals['s_type']]
            else:
                value = caller_locals[key]
            print(f'INFO:    {label}: {value}')
    print('-' * 80)
    print()


samples_to_plot = {
    # 'sig' : [sample.name for sample in ss.???],
    'bkg' : [sample.name for sample in ss.all_bkg_2023_bpix],
    'data': [sample.name for sample in ss.met_2023_postbpix]
}

tier = {'sig'  : 'CustomNanoAOD',
        'bkg'  : 'CustomNanoAOD',
        'data' : 'CustomNanoAOD'
}

json_db = {'sig'  : 'MC_Run3Summer23.json',
           'bkg'  : 'MC_Run3Summer23_20250409.json',
           'data' : 'Data_MET2023_20250415.json'
}

year = 2023
autoplotter_path = "$CMSSW_BASE/src/SoftDisplacedVertices/Plotter/autoplotter.py"
config =           "$CMSSW_BASE/src/SoftDisplacedVertices/Plotter/configs/2023_check_6.yaml"
outDir_base = "/scratch-cbe/users/alikaan.gueven/AN_plots/"
work_subdir = "checks_2023"
unique_dir  = "2023v2018_v6_bpix"

work_dir = os.path.join(outDir_base, work_subdir)


outBaseDir = os.path.join(work_dir,str(unique_dir))
for s_type in samples_to_plot.keys():
    job_dict = {}
    outDir = os.path.join(outBaseDir, s_type)
    os.makedirs(outDir, exist_ok=True)
    print_info()

    for sample in samples_to_plot[s_type]:
        if s_type != 'data':
            command = f'submit_to_cpu_medium.sh "python3 -u {autoplotter_path}  --sample {sample} --output {outDir} --config {config} --lumi 9897 --json {json_db[s_type]} --datalabel {tier[s_type]} --year {year}"'
        else:
            command = f'submit_to_cpu_medium.sh "python3 -u {autoplotter_path}  --sample {sample} --output {outDir} --config {config} --lumi -1 --json {json_db[s_type]} --datalabel {tier[s_type]} --year {year} --data"'

        result = run(f'sbatch {command}', shell=True, capture_output = True, text = True)
        job_id = re.search("\d+", result.stdout).group()    # Get the number with '\d+'
        info_dict = {'command': f'sbatch {command}',        # Save command [important for resubmitting]
                     'jobid':   job_id}                     # Save job_id  [identify the status with sacct]
        job_dict[sample] = info_dict                        # Add to dict
        print(result.stdout[:-1])
    
    out_json_path = os.path.join(outDir, 'job_ids2023.json')
    print(f"\nWriting to {out_json_path}...\n")
    with open(out_json_path, 'w') as f:
        json.dump(job_dict, f, indent=2)

print('\nFinished. Exiting...')