# Script to submit the grid search for the DISCO model to SLURM.
#
#
# ------------------------------------------------------------------------------

import os
import re
import json
from pathlib import Path
from subprocess import run




# Parse args

import argparse
p = argparse.ArgumentParser(description="SLURM submission script for the grid search for the DISCO model")
p.add_argument(
    "--dryrun",
    action="store_true",
    help="Show what is about to be run without executing."
)
args = p.parse_args()
# -----------------------------------------------

class DotDict(dict):
    """Dictionary with dot access to attributes."""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__



params = DotDict()
params.scan_x_loCut    = ' '.join([str(s) for s in [0.00]]) # [0.00, 0.20, 0.40, 0.60]])
params.scan_y_loCut    = ' '.join([str(s) for s in [0.00]]) # [0.00, 0.20, 0.40, 0.60]])

params.sigScale        = 1.0
params.bkgScale        = 1.0

params.uniquedir       = 'vtx_PART_859_epoch_87_test3_reverse'
params.tdir            = 'CP_evt'    # 'CP_evt'
params.histname        = 'leading_vtx_ML1_vs_leading_vtx_ML2'

USER = os.getenv('USER')
HISTDIR = Path(f'/scratch-cbe/users/{USER}/AN_plots/ParT_hists')
sigdir = HISTDIR / params.uniquedir / "sig"
files = []
for f in sorted(sigdir.glob("*_hist.root")):
    files.append(f.name.replace("_hist.root", ""))

params.sigtags         = files


command_head = 'sh/submit_to_cpu1.sh "python3 -u python/gridsearch_disco.py '
command_tail = '"'

 # To store job information for each sigtag
job_dict = {}
outDir = HISTDIR / params.uniquedir / "tables"
os.makedirs(outDir, exist_ok=True)



print('INFO:    Submitting gridsearch with command:')


# params.sigtags = [params.sigtags]
params.sigtags = ['C1N2MLstudy_M400_388_ct20_2018']                                               # <----- REMOVE THIS LINE TO SUBMIT ALL

for sigtag in params.sigtags:
    command_args = []
    command_args.append(f'--uniquedir {params.uniquedir}')
    command_args.append(f'--sigtag {sigtag}')
    command_args.append(f'--scan-x-loCut {params.scan_x_loCut}')
    command_args.append(f'--scan-y-loCut {params.scan_y_loCut}')
    command_args.append(f'--sigScale {params.sigScale}')
    command_args.append(f'--bkgScale {params.bkgScale}')
    command_args.append(f'--tdir {params.tdir}')
    command_args.append(f'--histname {params.histname}')
    command = command_head + ' '.join(command_args) + command_tail
    
    if args.dryrun:
        print(command)
    else:
        result = run(f'sbatch {command}', shell=True, capture_output = True, text = True)
        job_id = re.search("\d+", result.stdout).group()    # Get the number with '\d+'
        info_dict = {'command': f'sbatch {command}',        # Save command [important for resubmitting]
                    'jobid':   job_id}                      # Save job_id  [identify the status with sacct]
        job_dict[sigtag] = info_dict                        # Add to dict
        print(result.stdout[:-1])

out_json_path = os.path.join(outDir, 'job_ids.json')
print(f"\nWriting to {out_json_path}...\n")
with open(out_json_path, 'w') as f:
    json.dump(job_dict, f, indent=2)


print('\nFinished. Exiting...')