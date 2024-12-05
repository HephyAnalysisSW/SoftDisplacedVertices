from subprocess import run, PIPE
import SoftDisplacedVertices.Samples.Samples as ss
import re
import json
import os


samples_to_plot = {
    # 'sig' : [sample.name for sample in ss.all_sig_2018],
    # 'bkg' : [sample.name for sample in ss.all_bkg_2018],
    'data': [sample.name for sample in ss.met_2018]
}

tier = {'sig'  : 'CustomNanoAOD',
        'bkg'  : 'CustomNanoAOD',
        'data' : 'CustomNanoAOD'
}

json_db = {'sig'  : 'MC_RunIISummer20UL18.json',
           'bkg'  : 'MC_RunIISummer20UL18.json',
           'data' : 'Data_production_20240326.json'
}

year = 2018
autoplotter_path = "$CMSSW_BASE/src/SoftDisplacedVertices/Plotter/autoplotter.py"
config =           "$CMSSW_BASE/src/SoftDisplacedVertices/Plotter/configs/vtx_reco_data_2018.yaml"
outDir_base = "/scratch-cbe/users/alikaan.gueven/AN_plots/"
work_subdir = "vtx_reco/mc_data/"
unique_dir  = "20241204"

work_dir = os.path.join(outDir_base, work_subdir)

for s_type in samples_to_plot.keys():
    job_dict = {}
    outDir = os.path.join(os.path.join(work_dir, s_type), str(unique_dir))
    os.makedirs(outDir, exist_ok=True)

    print('INFO:    Sample type:',  s_type)
    print('INFO:    json:', json_db[s_type])
    print('INFO:    tier:',    tier[s_type])
    print('INFO:    year:',        year)
    print('INFO:    outDir:',      outDir)
    print('INFO:    config:',      config)
    print('-'*80)
    print()

    for sample in samples_to_plot[s_type]:
        if s_type != 'data':
            command = f'submit_to_cpu.sh "python3 {autoplotter_path}  --sample {sample} --output {outDir} --config {config} --lumi 59830 --json {json_db[s_type]} --datalabel {tier[s_type]} --year {year}"'
        else:
            command = f'submit_to_cpu.sh "python3 {autoplotter_path}  --sample {sample} --output {outDir} --config {config} --lumi -1 --json {json_db[s_type]} --datalabel {tier[s_type]} --year {year} --data"'

        result = run(f'sbatch {command}', shell=True, capture_output = True, text = True)
        job_id = re.search("\d+", result.stdout).group()    # Get the number with '\d+'
        info_dict = {'command': f'sbatch {command}',        # Save command [important for resubmitting]
                    'jobid':   job_id}                      # Save job_id  [identify the status with sacct]
        job_dict[sample] = info_dict                        # Add to dict
        print(result.stdout[:-1])
    
    out_json_path = os.path.join(outDir, 'job_ids.json')
    print(f"\nWriting to {out_json_path}...\n")
    with open(out_json_path, 'w') as f:
        json.dump(job_dict, f)

print('\nFinished. Exiting...')