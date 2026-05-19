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
            if key in ['json_db', 'tier'] and 's_type' in caller_locals:
                value = caller_locals[key][caller_locals['s_type']]
            else:
                value = caller_locals[key]
            print(f'INFO:    {label}: {value}')
    print('-' * 80)
    print()

tier = {
    'sig_18':    'CustomNanoAOD',
    'bkg_pre':   'CustomNanoAOD',
    'bkg_post':  'CustomNanoAOD',
    'data_pre':  'CustomNanoAOD',
    'data_post': 'CustomNanoAOD'
}

samples_to_plot = {
    # 'sig_18':    [sample.name for sample in ss.private_sig18],
    'bkg_pre':   [sample.name for sample in ss.bkg_2023Pre],
    'bkg_post':  [sample.name for sample in ss.bkg_2023Post],
    'data_pre':  [sample.name for sample in ss.met_2023Pre],
    'data_post': [sample.name for sample in ss.met_2023Post]
}

json_db = {
    'sig_18':    'scratch_sig18.json',
    'bkg_pre':   'scratch_MC23.json',
    'bkg_post':  'scratch_MC23.json',
    'data_pre':  'scratch_data23.json' ,
    'data_post': 'scratch_data23.json'
}

lumi = {
    'sig_18':    27640,
    'bkg_pre':   17960,
    'bkg_post':   9680,
}

year = {
    'sig_18':    '2018',
    'bkg_pre':   '2023Pre',
    'bkg_post':  '2023Post',
    'data_pre':  '2023Pre' ,
    'data_post': '2023Post'
}

autoplotter_path = "$CMSSW_BASE/src/SoftDisplacedVertices/Plotter/autoplotter.py"
config =           "$CMSSW_BASE/src/SoftDisplacedVertices/Plotter/configs/plotconfig_Run3_22_goodtk_first.yaml"
outDir_base = "/scratch-cbe/users/alikaan.gueven/AN_plots/"
work_subdir = "ParT_hists"
unique_dir  = "test23_after_fuckup"
files_per_job = 2

work_dir   = os.path.join(outDir_base, work_subdir)
outBaseDir = os.path.join(work_dir, str(unique_dir))

# remove existing outBaseDir
if os.path.isdir(outBaseDir):
    shutil.rmtree(outBaseDir)

# Copy the config file to outBaseDir
os.makedirs(outBaseDir, exist_ok=False)
config_copy = os.path.join(outBaseDir, 'plot_config.yaml')

shutil.copy(os.path.expandvars(config),
            os.path.expandvars(config_copy))

# Global submit script
submit_script_path = os.path.join(outBaseDir, "submit_all.sh")
submit_lines = [
    "#!/bin/bash",
    "",
]

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
        ss.loadData(
            [sample_obj],
            os.path.join(f'{os.environ["CMSSW_BASE"]}/src/SoftDisplacedVertices/Samples/json', json_db[s_type]),
            tier[s_type]
        )
        files = sample_obj.getFileList(tier[s_type], '')
        len_files = len(files)
        chunks = [files[i:i+files_per_job] for i in range(0, len(files), files_per_job)]

        for i, chunk in enumerate(chunks):
            fileList_path = os.path.join(fileListDir, f"{sample}_{i}.txt")
            with open(fileList_path, "w", encoding="utf-8") as f:
                f.write("\n".join(chunk) + "\n")

            if s_type[:4] != 'data':
                command = (
                    f"sbatch sh/submit_to_cpu_rapid.sh "
                    f"'python3 -u {autoplotter_path} "
                    f"--sample {sample} "
                    f"--filelist {fileList_path} "
                    f"--postfix {i} "
                    f"--output {outDir} "
                    f"--config {config_copy} "
                    f"--lumi {lumi[s_type]} "
                    f"--json {json_db[s_type]} "
                    f"--datalabel {tier[s_type]} "
                    f"--year {year[s_type]}'"
                )
            else:
                command = (
                    f"sbatch sh/submit_to_cpu_rapid.sh "
                    f"'python3 -u {autoplotter_path} "
                    f"--sample {sample} "
                    f"--filelist {fileList_path} "
                    f"--postfix {i} "
                    f"--output {outDir} "
                    f"--config {config_copy} "
                    f"--lumi -1 "
                    f"--json {json_db[s_type]} "
                    f"--datalabel {tier[s_type]} "
                    f"--year {year[s_type]} "
                    f"--data'"
                )

            submit_lines.append(command)

            info_dict = {
                'command': command,
                'jobid': None,
                'status': 'prepared'
            }
            job_dict[f'{sample}_{i}'] = info_dict
            print(f"Prepared: {sample}_{i}")

    out_json_path = os.path.join(outDir, 'job_ids.json')
    print(f"\nWriting to {out_json_path}...\n")
    with open(out_json_path, 'w') as f:
        json.dump(job_dict, f, indent=2)

# Write the bash script once
with open(submit_script_path, "w", encoding="utf-8") as f:
    f.write("\n".join(submit_lines) + "\n")

os.chmod(submit_script_path, 0o755)

print(f"\nWrote submission script to:\n{submit_script_path}")
print('\nFinished. Exiting...')