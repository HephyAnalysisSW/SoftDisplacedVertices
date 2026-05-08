from subprocess import run, PIPE

import SoftDisplacedVertices.Samples.Samples as ss
import re
import json
import os
import shutil
from pathlib import Path

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
            value = caller_locals[key]
            s_type = caller_locals.get('s_type')
            if isinstance(value, dict) and s_type in value:
                value = value[s_type]
            print(f'INFO:    {label}: {value}')
    print('-' * 80)
    print()

def has_file_source(sample_obj, label):
    # When the same samples are reused. e.g. using same sig18 for sig18 and sig17,
    # setNEvents in Sample.py throws an assertion error, because it expects that the
    # directories are defined only once.
    return (
        label in sample_obj.dirs
        or label in sample_obj.eosdirs
        or label in sample_obj.dataset
    )

tier = 'CustomNanoAOD'

samples_to_plot = {
    # 'sig17':            [sample.name for sample in ss.private_sig18],
    # 'sig18':            [sample.name for sample in ss.private_sig18],
    # 'sig22_pre':        [sample.name for sample in ss.private_sig18],
    # 'sig22_post':       [sample.name for sample in ss.private_sig18],
    # 'sig23_pre':        [sample.name for sample in ss.private_sig18],
    # 'sig23_post':       [sample.name for sample in ss.private_sig18],
    # 'sig24':            [sample.name for sample in ss.private_sig18],
    # 'bkg17':            [sample.name for sample in ss.all_bkg_2017],
    # 'bkg18':            [sample.name for sample in ss.all_bkg_2018],
    # 'bkg22_pre':        [sample.name for sample in ss.bkg_2022Pre],
    # 'bkg22_post':       [sample.name for sample in ss.bkg_2022Post],
    # 'bkg23_pre':        [sample.name for sample in ss.bkg_2023Pre],
    # 'bkg23_post':       [sample.name for sample in ss.bkg_2023Post],
    # 'bkg24':            [sample.name for sample in ss.all_bkg_2024],
    'data17':           [sample.name for sample in ss.met_2017],
    'data18':           [sample.name for sample in ss.met_2018],
    # 'data22_pre':       [sample.name for sample in ss.met_2022Pre],
    # 'data22_post':      [sample.name for sample in ss.met_2022Post],
    # 'data23_pre':       [sample.name for sample in ss.met_2023Pre],
    # 'data23_post':      [sample.name for sample in ss.met_2023Post],
    # 'data24':           [sample.name for sample in ss.met_2024],
}

json_db = {  
    'sig17':            'scratch_MC.json',
    'sig18':            'scratch_MC.json',
    'sig22_pre':        'scratch_MC.json',
    'sig22_post':       'scratch_MC.json',
    'sig23_pre':        'scratch_MC.json',
    'sig23_post':       'scratch_MC.json',
    'sig24':            'scratch_MC.json',
    'bkg17':            'scratch_MC.json',
    'bkg18':            'scratch_MC.json',
    'bkg22_pre':        'scratch_MC.json',
    'bkg22_post':       'scratch_MC.json',
    'bkg23_pre':        'scratch_MC.json',
    'bkg23_post':       'scratch_MC.json',
    'bkg24':            'scratch_MC.json',
    'data17':           'scratch_data.json',
    'data18':           'scratch_data.json',
    'data22_pre':       'scratch_data.json',
    'data22_post':      'scratch_data.json',
    'data23_pre':       'scratch_data.json',
    'data23_post':      'scratch_data.json',
    'data24':           'scratch_data.json',

}

lumi = {
    'sig17':            1000,
    'sig18':            1000,
    'sig22_pre':        1000,
    'sig22_post':       1000,
    'sig23_pre':        1000,
    'sig23_post':       1000,
    'sig24':            1000,

    'bkg17':            1000,
    'bkg18':            1000,
    'bkg22_pre':        1000,
    'bkg22_post':       1000,
    'bkg23_pre':        1000,
    'bkg23_post':       1000,
    'bkg24':            1000,
}

year = {
    'sig17':            '2018',
    'sig18':            '2018',
    'sig22_pre':        '2018',
    'sig22_post':       '2018',
    'sig23_pre':        '2018',
    'sig23_post':       '2018',
    'sig24':            '2018',

    'bkg17':            '2017',
    'bkg18':            '2018',
    'bkg22_pre':        '2022Pre',
    'bkg22_post':       '2022Post',
    'bkg23_pre':        '2023Pre',
    'bkg23_post':       '2023Post',
    'bkg24':            '2024',
    'data17':           '2017',
    'data18':           '2018',
    'data22_pre':       '2022Pre',
    'data22_post':      '2022Post',
    'data23_pre':       '2023Pre',
    'data23_post':      '2023Post',
    'data24':           '2024',
}

config = {
    'sig17':            '$CMSSW_BASE/src/SoftDisplacedVertices/Plotter/configs/limitcalc_Run2.yaml',
    'sig18':            '$CMSSW_BASE/src/SoftDisplacedVertices/Plotter/configs/limitcalc_Run2.yaml',
    'sig22_pre':        '$CMSSW_BASE/src/SoftDisplacedVertices/Plotter/configs/limitcalc_Run2.yaml',
    'sig22_post':       '$CMSSW_BASE/src/SoftDisplacedVertices/Plotter/configs/limitcalc_Run2.yaml',
    'sig23_pre':        '$CMSSW_BASE/src/SoftDisplacedVertices/Plotter/configs/limitcalc_Run2.yaml',
    'sig23_post':       '$CMSSW_BASE/src/SoftDisplacedVertices/Plotter/configs/limitcalc_Run2.yaml',
    'sig24':            '$CMSSW_BASE/src/SoftDisplacedVertices/Plotter/configs/limitcalc_Run2.yaml',

    'bkg17':            '$CMSSW_BASE/src/SoftDisplacedVertices/Plotter/configs/limitcalc_Run2.yaml',
    'bkg18':            '$CMSSW_BASE/src/SoftDisplacedVertices/Plotter/configs/limitcalc_Run2.yaml',
    'bkg22_pre':        '$CMSSW_BASE/src/SoftDisplacedVertices/Plotter/configs/limitcalc_Run3.yaml',
    'bkg22_post':       '$CMSSW_BASE/src/SoftDisplacedVertices/Plotter/configs/limitcalc_Run3.yaml',
    'bkg23_pre':        '$CMSSW_BASE/src/SoftDisplacedVertices/Plotter/configs/limitcalc_Run3.yaml',
    'bkg23_post':       '$CMSSW_BASE/src/SoftDisplacedVertices/Plotter/configs/limitcalc_Run3.yaml',
    'bkg24':            '$CMSSW_BASE/src/SoftDisplacedVertices/Plotter/configs/limitcalc_Run3.yaml',

    'data17':           '$CMSSW_BASE/src/SoftDisplacedVertices/Plotter/configs/limitcalc_Run2.yaml',
    'data18':           '$CMSSW_BASE/src/SoftDisplacedVertices/Plotter/configs/limitcalc_Run2.yaml',
    'data22_pre':       '$CMSSW_BASE/src/SoftDisplacedVertices/Plotter/configs/limitcalc_Run3.yaml',
    'data22_post':      '$CMSSW_BASE/src/SoftDisplacedVertices/Plotter/configs/limitcalc_Run3.yaml',
    'data23_pre':       '$CMSSW_BASE/src/SoftDisplacedVertices/Plotter/configs/limitcalc_Run3.yaml',
    'data23_post':      '$CMSSW_BASE/src/SoftDisplacedVertices/Plotter/configs/limitcalc_Run3.yaml',
    'data24':           '$CMSSW_BASE/src/SoftDisplacedVertices/Plotter/configs/limitcalc_Run3.yaml',
}

autoplotter_path = "$CMSSW_BASE/src/SoftDisplacedVertices/Plotter/autoplotter.py"
outDir_base = Path("/scratch-cbe/users/alikaan.gueven/AN_plots/")
work_subdir = "ParT_hists"
unique_dir  = "plotconfig_Run3_effcheck_v2"
files_per_job = 2

outBaseDir   = outDir_base / work_subdir / unique_dir

# remove existing outBaseDir
if os.path.isdir(outBaseDir):
    shutil.rmtree(outBaseDir)

# Global submit script
submit_script_path = os.path.join(outBaseDir, "submit_all.sh")
submit_lines = [
    "#!/bin/bash",
    "",
]

for s_type in samples_to_plot.keys():
    # Copy the config file to outBaseDir
    os.makedirs(outBaseDir / s_type, exist_ok=False)
    config_copy = outBaseDir / s_type / 'plot_config.yaml'

    shutil.copy(os.path.expandvars(config[s_type]),
                os.path.expandvars(config_copy))

    job_dict = {}
    outDir = outBaseDir / s_type
    fileListDir = outDir / 'fileList'

    os.makedirs(outDir,         exist_ok=True)
    os.makedirs(fileListDir,    exist_ok=True)
    print_info()

    for sample in samples_to_plot[s_type]:
        # all about getting file_paths to text file.
        # ------------------------------------------------------------
        sample_obj = getattr(ss, sample)
        if not has_file_source(sample_obj, tier):
            # Reuse the same sample if it is NEvents are already set.
            ss.loadData(
                [sample_obj],
                os.path.join(f'{os.environ["CMSSW_BASE"]}/src/SoftDisplacedVertices/Samples/json', json_db[s_type]),
                tier
            )
        
        files = sample_obj.getFileList(tier, '')
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
                    f"--datalabel {tier} "
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
                    f"--datalabel {tier} "
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
