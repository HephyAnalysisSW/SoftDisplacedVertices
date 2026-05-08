#!/bin/bash 

#SBATCH --job-name=plotter_run3
#SBATCH --output=/scratch-cbe/users/alikaan.gueven/job_outs/job_%j.out 
#SBATCH --ntasks 1 
#SBATCH --cpus-per-task=4
#SBATCH --mem-per-cpu=500M
#SBATCH --nodes=1-1 
#SBATCH --partition=c 
#SBATCH --qos=short
#SBATCH --time=04:00:00 
cd /users/alikaan.gueven/AOD_to_nanoAOD/Plotter_run3/CMSSW_15_0_5/src/SoftDisplacedVertices/Plotter/testK
cmssw-el9<<EOF
cmsenv
echo ----------------------------------------------- 
($1)
EOF

# Since cmssw-el9 cannot acces sbatch, we request each job to swith OS by themselves.
# cmssw-el9 runs in interactive mode, therefore expects inputs
# these inputs are passed via so-called heredoc method (e.g. <<EOF ... some-code ... EOF)