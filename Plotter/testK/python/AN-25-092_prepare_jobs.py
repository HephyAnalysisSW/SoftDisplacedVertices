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
    s_type = caller_locals.get('s_type')
    for key, label in keys.items():
        if key in caller_locals:
            value = caller_locals[key]
            if isinstance(value, dict) and s_type in value:
                value = value[s_type]
            print(f'INFO:    {label}: {value}')
    print('-' * 80)
    print()

tier = "CustomNanoAOD"

samples_to_plot = {
    # 'sig_2017':            [sample.name for sample in ss.old_central_sig17],
    # 'sig_2018':            [sample.name for sample in ss.old_central_sig18],
    # 'sig_2022Pre':         [sample.name for sample in ss.old_central_sig18],
    # 'sig_2022Post':        [sample.name for sample in ss.old_central_sig18],
    # 'sig_2023Pre':         [sample.name for sample in ss.old_central_sig18],
    # 'sig_2023Post':        [sample.name for sample in ss.old_central_sig18],
    # 'sig_2024':            [sample.name for sample in ss.old_central_sig18],

    # 'sig_2017':           [sample.name for sample in ss.private_sig18],
    # 'sig_2018':           [sample.name for sample in ss.private_sig18],
    # 'sig_2022Pre':        [sample.name for sample in ss.private_sig18],
    # 'sig_2022Post':       [sample.name for sample in ss.private_sig18],
    # 'sig_2023Pre':        [sample.name for sample in ss.private_sig18],
    # 'sig_2023Post':       [sample.name for sample in ss.private_sig18],
    # 'sig_2024':           [sample.name for sample in ss.private_sig18],

    'bkg_2017':           [sample.name for sample in ss.all_bkg_2017],
    'bkg_2018':           [sample.name for sample in ss.all_bkg_2018],
    # 'bkg_2022Pre':        [sample.name for sample in ss.bkg_2022Pre],
    # 'bkg_2022Post':       [sample.name for sample in ss.bkg_2022Post],
    # 'bkg_2023Pre':        [sample.name for sample in ss.bkg_2023Pre],
    # 'bkg_2023Post':       [sample.name for sample in ss.bkg_2023Post],
    # 'bkg_2024':           [sample.name for sample in ss.all_bkg_2024],

    # 'data_2017':          [sample.name for sample in ss.met_2017],
    # 'data_2018':          [sample.name for sample in ss.met_2018],
    # 'data_2022Pre':       [sample.name for sample in ss.met_2022Pre],
    # 'data_2022Post':      [sample.name for sample in ss.met_2022Post],
    # 'data_2023Pre':       [sample.name for sample in ss.met_2023Pre],
    # 'data_2023Post':      [sample.name for sample in ss.met_2023Post],
    # 'data_2024':          [sample.name for sample in ss.met_2024],
}

json_db = {  
    # 'sig_2017':           'scratch_CustomNanoAOD_v3_centralprod.json',
    # 'sig_2018':           'scratch_CustomNanoAOD_v3_centralprod.json',
    # 'sig_2022Pre':        'scratch_CustomNanoAOD_v3_centralprod.json',
    # 'sig_2022Post':       'scratch_CustomNanoAOD_v3_centralprod.json',
    # 'sig_2023Pre':        'scratch_CustomNanoAOD_v3_centralprod.json',
    # 'sig_2023Post':       'scratch_CustomNanoAOD_v3_centralprod.json',
    # 'sig_2024':           'scratch_CustomNanoAOD_v3_centralprod.json',

    'sig_2017':           'scratch_MC.json',
    'sig_2018':           'scratch_MC.json',
    'sig_2022Pre':        'scratch_MC.json',
    'sig_2022Post':       'scratch_MC.json',
    'sig_2023Pre':        'scratch_MC.json',
    'sig_2023Post':       'scratch_MC.json',
    'sig_2024':           'scratch_MC.json',

    'bkg_2017':           'scratch_MC.json',
    'bkg_2018':           'scratch_MC.json',
    'bkg_2022Pre':        'scratch_MC.json',
    'bkg_2022Post':       'scratch_MC.json',
    'bkg_2023Pre':        'scratch_MC.json',
    'bkg_2023Post':       'scratch_MC.json',
    'bkg_2024':           'scratch_MC.json',

    'data_2017':          'scratch_data.json',
    'data_2018':          'scratch_data.json',
    'data_2022Pre':       'scratch_data.json',
    'data_2022Post':      'scratch_data.json',
    'data_2023Pre':       'scratch_data.json',
    'data_2023Post':      'scratch_data.json',
    'data_2024':          'scratch_data.json',

}

lumi = {
    'sig_2017':           42070,
    'sig_2018':           59560,
    'sig_2022Pre':        7990,
    'sig_2022Post':       26680,
    'sig_2023Pre':        17960,
    'sig_2023Post':       9680,
    'sig_2024':           109820,

    'bkg_2017':           42070,
    'bkg_2018':           59560,
    'bkg_2022Pre':        7990,
    'bkg_2022Post':       26680,
    'bkg_2023Pre':        17960,
    'bkg_2023Post':       9680,
    'bkg_2024':           109820,
}

year = {
    # 'sig_2017':           '2017',
    'sig_2017':           '2018',
    'sig_2018':           '2018',
    'sig_2022Pre':        '2018',
    'sig_2022Post':       '2018',
    'sig_2023Pre':        '2018',
    'sig_2023Post':       '2018',
    'sig_2024':           '2018',

    'bkg_2017':           '2017',
    'bkg_2018':           '2018',
    'bkg_2022Pre':        '2022Pre',
    'bkg_2022Post':       '2022Post',
    'bkg_2023Pre':        '2023Pre',
    'bkg_2023Post':       '2023Post',
    'bkg_2024':           '2024',

    'data_2017':          '2017',
    'data_2018':          '2018',
    'data_2022Pre':       '2022Pre',
    'data_2022Post':      '2022Post',
    'data_2023Pre':       '2023Pre',
    'data_2023Post':      '2023Post',
    'data_2024':          '2024',
}

config = {
    # 'sig17':            '$CMSSW_BASE/src/SoftDisplacedVertices/Plotter/configs/effcheck_Run2_newmapveto_17.yaml',
    # 'sig18':            '$CMSSW_BASE/src/SoftDisplacedVertices/Plotter/configs/effcheck_Run2_newmapveto_18.yaml',
    
    'sig_2017':            '$CMSSW_BASE/src/SoftDisplacedVertices/Plotter/configs/AN-25-092_MLinputs_Run2.yaml',
    'sig_2018':            '$CMSSW_BASE/src/SoftDisplacedVertices/Plotter/configs/AN-25-092_MLinputs_Run2.yaml',
    'sig_2022Pre':         '$CMSSW_BASE/src/SoftDisplacedVertices/Plotter/configs/AN-25-092_limitcalc_Run2.yaml',
    'sig_2022Post':        '$CMSSW_BASE/src/SoftDisplacedVertices/Plotter/configs/AN-25-092_limitcalc_Run2.yaml',
    'sig_2023Pre':         '$CMSSW_BASE/src/SoftDisplacedVertices/Plotter/configs/AN-25-092_limitcalc_Run2.yaml',
    'sig_2023Post':        '$CMSSW_BASE/src/SoftDisplacedVertices/Plotter/configs/AN-25-092_limitcalc_Run2.yaml',
    'sig_2024':            '$CMSSW_BASE/src/SoftDisplacedVertices/Plotter/configs/AN-25-092_limitcalc_Run2.yaml',

    'bkg_2017':            '$CMSSW_BASE/src/SoftDisplacedVertices/Plotter/configs/AN-25-092_limitcalc_Run3.yaml', # '$CMSSW_BASE/src/SoftDisplacedVertices/Plotter/configs/AN-25-092_ML_plots_Dpm_isomu_Run2.yaml',
    'bkg_2018':            '$CMSSW_BASE/src/SoftDisplacedVertices/Plotter/configs/AN-25-092_limitcalc_Run3.yaml', # '$CMSSW_BASE/src/SoftDisplacedVertices/Plotter/configs/AN-25-092_ML_plots_Dpm_isomu_Run2.yaml',
    'bkg_2022Pre':         '$CMSSW_BASE/src/SoftDisplacedVertices/Plotter/configs/AN-25-092_limitcalc_Run3.yaml',
    'bkg_2022Post':        '$CMSSW_BASE/src/SoftDisplacedVertices/Plotter/configs/AN-25-092_limitcalc_Run3.yaml',
    'bkg_2023Pre':         '$CMSSW_BASE/src/SoftDisplacedVertices/Plotter/configs/AN-25-092_limitcalc_Run3.yaml',
    'bkg_2023Post':        '$CMSSW_BASE/src/SoftDisplacedVertices/Plotter/configs/AN-25-092_limitcalc_Run3.yaml',
    'bkg_2024':            '$CMSSW_BASE/src/SoftDisplacedVertices/Plotter/configs/AN-25-092_limitcalc_Run3.yaml',

    # 'data_2017':           '$CMSSW_BASE/src/SoftDisplacedVertices/Plotter/configs/AN-25-092_limitcalc_Run2.yaml',
    # 'data_2018':           '$CMSSW_BASE/src/SoftDisplacedVertices/Plotter/configs/AN-25-092_limitcalc_Run2.yaml',
    # 'data_2022Pre':       '$CMSSW_BASE/src/SoftDisplacedVertices/Plotter/configs/AN-25-092_limitcalc_Run3.yaml',
    # 'data_2022Post':      '$CMSSW_BASE/src/SoftDisplacedVertices/Plotter/configs/AN-25-092_limitcalc_Run3.yaml',
    # 'data_2023Pre':       '$CMSSW_BASE/src/SoftDisplacedVertices/Plotter/configs/AN-25-092_limitcalc_Run3.yaml',
    # 'data_2023Post':      '$CMSSW_BASE/src/SoftDisplacedVertices/Plotter/configs/AN-25-092_limitcalc_Run3.yaml',
    # 'data_2024':           '$CMSSW_BASE/src/SoftDisplacedVertices/Plotter/configs/AN-25-092_limitcalc_Run3.yaml',
}

autoplotter_path = "$CMSSW_BASE/src/SoftDisplacedVertices/Plotter/autoplotter.py"
outDir_base = Path("/scratch-cbe/users/alikaan.gueven/AN_plots/")
work_subdir = "ParT_hists"
unique_dir  = "AN-25-092_ML_plots_whatever_whatever" # "AN-25-092_ML_plots_Dpm_isomu_Run2_v3"
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

        if tier not in sample_obj.nevents:
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
