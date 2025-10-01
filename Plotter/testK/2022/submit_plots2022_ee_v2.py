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
    'bkg' : [sample.name for sample in ss.all_bkg_2022_ee],
    'data': [sample.name for sample in ss.met_2022_ee]
}

tier = {'sig'  : 'CustomNanoAOD',
        'bkg'  : 'CustomNanoAOD',
        'data' : 'CustomNanoAOD'
}

json_db = {# 'sig'  : '',
           'bkg'  : 'MC_Run3Summer22_20250621.json',
           'data' : 'Data_MET2022_20250620.json'
}

year = "2022EE"
autoplotter_path = "$CMSSW_BASE/src/SoftDisplacedVertices/Plotter/autoplotter.py"
config =           "$CMSSW_BASE/src/SoftDisplacedVertices/Plotter/configs/2022_checks/2022_check_1.yaml"
outDir_base = "/scratch-cbe/users/alikaan.gueven/AN_plots/"
work_subdir = "checks_2022"
unique_dir  = "check_1_ee"
files_per_job = 5


work_dir = os.path.join(outDir_base, work_subdir)
outBaseDir = os.path.join(work_dir,str(unique_dir))
testKDir = "/users/alikaan.gueven/AOD_to_nanoAOD/CMSSW_13_0_16/src/SoftDisplacedVertices/Plotter/testK"


for s_type in samples_to_plot.keys():
    job_dict = {}
    outDir = os.path.join(outBaseDir, s_type)
    fileListDir = os.path.join(outDir, 'fileList')
    os.makedirs(outDir, exist_ok=True)
    os.makedirs(fileListDir, exist_ok=True)
    print_info()

    for sample in samples_to_plot[s_type]:
        # all about getting file_paths to text file.
        # ------------------------------------------------------------
        sample_obj = getattr(ss, sample)
        ss.loadData([sample_obj], os.path.join(f'{os.environ["CMSSW_BASE"]}/src/SoftDisplacedVertices/Samples/json', json_db[s_type]), tier[s_type])
        files = sample_obj.getFileList(tier[s_type], '')
        len_files = len(files)
        chunks = [files[i:i+files_per_job] for i in range(0, len(files), files_per_job)]
        for i, chunk in enumerate(chunks):
            fileList_path = os.path.join(fileListDir, f"{sample}_{i}.txt")
            with open(fileList_path, "w", encoding="utf-8") as f:
                f.write("\n".join(chunk) + "\n")
        # ------------------------------------------------------------
            if s_type != 'data':
                command = f'{testKDir}/submit_to_cpu_short.sh "python3 -u {autoplotter_path}  --sample {sample} --filelist {fileList_path} --postfix {i} --output {outDir} --config {config} --lumi 26671.7 --json {json_db[s_type]} --datalabel {tier[s_type]} --year {year}"'
            else:
                command = f'{testKDir}/submit_to_cpu_short.sh "python3 -u {autoplotter_path}  --sample {sample} --filelist {fileList_path} --postfix {i} --output {outDir} --config {config} --lumi -1 --json {json_db[s_type]} --datalabel {tier[s_type]} --year {year} --data"'

            result = run(f'sbatch {command}', shell=True, capture_output = True, text = True)
            job_id = re.search("\d+", result.stdout).group()    # Get the number with '\d+'
            info_dict = {'command': f'sbatch {command}',        # Save command [important for resubmitting]
                        'jobid':   job_id}                     # Save job_id  [identify the status with sacct]
            job_dict[f'{sample}_{i}'] = info_dict                        # Add to dict
            print(result.stdout[:-1])
    
    out_json_path = os.path.join(outDir, 'job_ids2022EE.json')
    print(f"\nWriting to {out_json_path}...\n")
    with open(out_json_path, 'w') as f:
        json.dump(job_dict, f, indent=2)

print('\nFinished. Exiting...')