from subprocess import run, PIPE
import re
import json
import os

samples = [
    "stop_M600_575_ct0p2_2018",
    "stop_M600_580_ct2_2018",
    "stop_M600_585_ct20_2018",
    "stop_M600_588_ct200_2018",

    "stop_M1000_975_ct0p2_2018",
    "stop_M1000_980_ct2_2018",
    "stop_M1000_985_ct20_2018",
    "stop_M1000_988_ct200_2018",
    
    "stop_M1400_1375_ct0p2_2018",
    "stop_M1400_1380_ct2_2018",
    "stop_M1400_1385_ct20_2018",
    "stop_M1400_1388_ct200_2018",
    
    "C1N2_M600_575_ct0p2_2018",
    "C1N2_M600_580_ct2_2018",
    "C1N2_M600_585_ct20_2018",
    "C1N2_M600_588_ct200_2018",
    
    "C1N2_M1000_975_ct0p2_2018",
    "C1N2_M1000_980_ct2_2018",
    "C1N2_M1000_985_ct20_2018",
    "C1N2_M1000_988_ct200_2018",
    
    "C1N2_M1400_1375_ct0p2_2018",
    "C1N2_M1400_1380_ct2_2018",
    "C1N2_M1400_1385_ct20_2018",
    "C1N2_M1400_1388_ct200_2018",
]


outDir = "/scratch-cbe/users/alikaan.gueven/AN_plots/tmp_checks"
config = "../configs/plotconfig_VRdPhirevert_changeVR.yaml"
json_path = "PrivateSignal_v3.json"
tier = "CustomNanoAODv3"
year = 2018
job_dict = {}

os.makedirs(outDir, exist_ok=True)

for sample in samples:
    command = f'submit_to_cpu.sh "python3 ../autoplotter.py  --sample {sample} --output {outDir} --config {config} --lumi 59800 --json {json_path} --datalabel {tier} --year {year}"'
    # print(command)
    result = run(f'sbatch {command}', shell=True, capture_output = True, text = True)
    # result.stdout looks like many lines of: Submitted batch job 9095285

    job_id = re.search("\d+", result.stdout).group() # Get the number with '\d+'
    info_dict = {'command': f'sbatch {command}',     # Save command [important for resubmitting]
                 'jobid':   job_id}                  # Save job_id  [identify the status with sacct]
    job_dict[sample] = info_dict                     # Add to dict
    print(result.stdout[:-1])

print("\nRewriting {os.path.join(outDir, 'job_ids.json')}...")
with open(os.path.join(outDir, 'job_ids.json'), 'w') as f:
    json.dump(job_dict, f)

print('\nFinished. Exiting...')