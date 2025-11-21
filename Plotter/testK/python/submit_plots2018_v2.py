from subprocess import run, PIPE
import SoftDisplacedVertices.Samples.Samples as ss
import re
import json
import os
import shutil

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

tier = {'sig'  : 'CustomNanoAOD',
        'bkg'  : 'CustomNanoAOD',
        # 'data' : 'CustomNanoAOD'
}


# ANG's ML samples merged
# -----------------------------------------------------------------
samples_to_plot = {
    'sig' : [sample.name for sample in ss.sig_AngML],
    'bkg' : [sample.name for sample in ss.all_bkg_2018],
    # 'data': [sample.name for sample in ss.met_2018]
}
json_db = {'sig'  : 'MLNano_merged.json',
           'bkg'  : 'MLNano_merged.json',
           # 'data' : ''
}
files_per_job = 2
# ----------------------------------------------------------------


# samples_to_plot = {
#     'sig' : [sample.name for sample in ss.sig_benchmark],
#     'bkg' : [sample.name for sample in ss.all_bkg_2018],
#     # 'data': [sample.name for sample in ss.met_2018]
# }
# 
# json_db = {'sig'  : 'MC_RunIISummer20UL18_ParT.json',
#            'bkg'  : 'MC_RunIISummer20UL18_ParT.json',
#            # 'data' : 'Data_production_20240326.json'
# }

year = 2018
autoplotter_path = "$CMSSW_BASE/src/SoftDisplacedVertices/Plotter/autoplotter.py"
config =           "$CMSSW_BASE/src/SoftDisplacedVertices/Plotter/configs/2018/vtx_PART_859_epoch_87_test1_copy.yaml"
outDir_base = "/scratch-cbe/users/alikaan.gueven/AN_plots/"
work_subdir = "ParT_hists"
unique_dir  = "vtx_PART_859_epoch_87_test1_copy"
files_per_job = 2


work_dir   = os.path.join(outDir_base, work_subdir)
outBaseDir = os.path.join(work_dir,str(unique_dir))


# remove existing outBaseDir
if os.path.isdir(outBaseDir):
    shutil.rmtree(outBaseDir)

# Copy the config file to outBaseDir
os.makedirs(outBaseDir, exist_ok=False)
config_copy = os.path.join(outBaseDir, 'plot_config.yaml')

shutil.copy(os.path.expandvars(config),
            os.path.expandvars(config_copy))



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
                command = f'sh/submit_to_cpu_short.sh "python3 -u {autoplotter_path}  --sample {sample} --filelist {fileList_path} --postfix {i} --output {outDir} --config {config_copy} --lumi 59683 --json {json_db[s_type]} --datalabel {tier[s_type]} --year {year}"'
            else:
                command = f'sh/submit_to_cpu_short.sh "python3 -u {autoplotter_path}  --sample {sample} --filelist {fileList_path} --postfix {i} --output {outDir} --config {config_copy} --lumi -1 --json {json_db[s_type]} --datalabel {tier[s_type]} --year {year} --data"'

            result = run(f'sbatch {command}', shell=True, capture_output = True, text = True)
            job_id = re.search("\d+", result.stdout).group()    # Get the number with '\d+'
            info_dict = {'command': f'sbatch {command}',        # Save command [important for resubmitting]
                        'jobid':   job_id}                      # Save job_id  [identify the status with sacct]
            job_dict[f'{sample}_{i}'] = info_dict               # Add to dict
            print(result.stdout[:-1])
    
    out_json_path = os.path.join(outDir, 'job_ids2018.json')
    print(f"\nWriting to {out_json_path}...\n")
    with open(out_json_path, 'w') as f:
        json.dump(job_dict, f, indent=2)


print('\nFinished. Exiting...')