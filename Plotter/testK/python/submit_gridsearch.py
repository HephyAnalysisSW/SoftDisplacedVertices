from subprocess import run, PIPE
import SoftDisplacedVertices.Samples.Samples as ss
import re
import json
import os
import shutil
from pathlib import Path
import glob

class DotDict(dict):
    """Dictionary with dot access to attributes."""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__



params = DotDict()
params.scan_x_loCut    = ' '.join([str(s) for s in [0.00, 0.20, 0.30, 0.40, 0.50, 0.60]])
params.scan_y_loCut    = ' '.join([str(s) for s in [0.00, 0.20, 0.30, 0.40, 0.50, 0.60]])

params.sigScale        = 1.0
params.bkgScale        = 1.0

params.uniquedir       = 'vtx_PART_859_epoch_87_test1'

USER = os.getenv('USER')
HISTDIR = Path(f'/scratch-cbe/users/{USER}/AN_plots/ParT_hists')
sigdir = HISTDIR / params.uniquedir / "sig"
files = []
for f in sorted(sigdir.glob("*_hist.root")):
    files.append(f.name.replace("_hist.root", ""))

params.sigtags         = files


command_head = 'sh/submit_to_cpu_short.sh "python3 -u '
command_tail = '"'

print('INFO:    Submitting gridsearch with command:')

for sigtag in params.sigtags:
    command_args = []
    command_args.append(f'--uniquedir {params.uniquedir}')
    command_args.append(f'--sigtag {sigtag}')
    command_args.append(f'--scan-x-loCut {params.scan_x_loCut}')
    command_args.append(f'--scan-y-loCut {params.scan_y_loCut}')
    command_args.append(f'--sigScale {params.sigScale}')
    command_args.append(f'--bkgScale {params.bkgScale}')
    command = command_head + ' '.join(command_args) + command_tail
    
    print(command)