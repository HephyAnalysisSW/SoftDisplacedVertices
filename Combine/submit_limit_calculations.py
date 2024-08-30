# You cannot use sbatch within Singularity.
# Use different environment. Each job will switch OS and run Combine in the correct CMSSW.

# Example usage:
# python submit_limit_calculations.py

import subprocess
import os

datacard_dir = '/users/alikaan.gueven/AngPlotter/CMSSW_14_1_0_pre4/src/SoftDisplacedVertices/Plotter/testK/datacards/MC_SP'
limitdir  =    '/users/alikaan.gueven/AngPlotter/CMSSW_14_1_0_pre4/src/SoftDisplacedVertices/Plotter/testK/limits/MC_SP'

os.makedirs(limitdir, exist_ok=True)

for root, dirs, files in os.walk(datacard_dir):
    print("Submitting", root, "...")
    if len(files) == 0:
        continue    # this skips the outmost directory, namely "MC_SP".
    else:
        sample_name = root.split('/')[-1]
        sample_limitdir = os.path.join(limitdir, sample_name)
    for filename in files:
        datacard = os.path.join(root, filename)
        command = f'submit_limit_jobs.sh "python3 makeLimits.py --datacard {datacard} --limitdir {limitdir}"'
        subprocess.run(f'sbatch {command}', shell=True)