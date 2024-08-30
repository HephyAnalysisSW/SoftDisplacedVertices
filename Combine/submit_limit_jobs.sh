#!/bin/bash 
# Usage: sbatch submit_to_cpu.sh "python3 python3 makeLimits.py --datacard {datacard} --limitdir {limitdir}"


#SBATCH --job-name=limit_calc
#SBATCH --output=/scratch-cbe/users/alikaan.gueven/job_outs/job_%j.out 
#SBATCH --ntasks 1 
#SBATCH --cpus-per-task=1
#SBATCH --mem-per-cpu=1G 
#SBATCH --nodes=1-1 
#SBATCH --partition=c 
#SBATCH --qos=rapid
#SBATCH --time=00:05:00 
cd /users/alikaan.gueven/AngPlotter/CMSSW_14_1_0_pre4/src/SoftDisplacedVertices/Plotter/testK
cmssw-el9<<EOF
cmsenv
echo ----------------------------------------------- 
($1)
EOF

# Since cmssw-el9 cannot acces sbatch, we request each job to swith OS by themselves.
# cmssw-el9 runs in interactive mode, therefore expects inputs
# these inputs are passed via so-called heredoc method (e.g. <<EOF ... some-code ... EOF)