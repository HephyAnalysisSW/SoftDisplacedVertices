#!/bin/bash 

# Usage: sbatch submit_to_cpu.sh "python3 autoplotter.py  --sample wjetstolnuht0100_2018  --output /scratch-cbe/users/alikaan.gueven/2018_limits --config configs/calc_limits.yaml --lumi 59800 --json CustomNanoAOD_v3_bkg.json --datalabel CustomNanoAOD"


#SBATCH --job-name=autoplotter
#SBATCH --output=/scratch-cbe/users/alikaan.gueven/job_outs/job_%j.out 
#SBATCH --ntasks 1 
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=2000M 
#SBATCH --nodes=1-1 
#SBATCH --partition=c 
#SBATCH --qos=short
#SBATCH --time=08:00:00 
cd /users/alikaan.gueven/AOD_to_nanoAOD/Plotter_run3/CMSSW_15_0_5/src/SoftDisplacedVertices/Plotter/testK
cmssw-el9<<EOF
cmsenv
echo ----------------------------------------------- 
($1)
EOF

# Since cmssw-el9 cannot acces sbatch, we request each job to swith OS by themselves.
# cmssw-el9 runs in interactive mode, therefore expects inputs
# these inputs are passed via so-called heredoc method (e.g. <<EOF ... some-code ... EOF)