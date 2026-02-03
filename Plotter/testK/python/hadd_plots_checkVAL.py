from subprocess import run, PIPE
import SoftDisplacedVertices.Samples.Samples as ss
import re
import json
import os
import glob
from collections import defaultdict

year = 2018
outDir_base = "/scratch-cbe/users/alikaan.gueven/AN_plots/"
work_subdir = "ParT_hists"
unique_dir  = "validation_merged_20251213"
workbase_dir = os.path.join(outDir_base, work_subdir)
work_dir = os.path.join(workbase_dir, unique_dir)

dirs  = {'data':  os.path.join(work_dir, 'data')}

sig_out  = os.path.join(dirs['data'], f'val_20251213_sig_hist.root')
val_out  = os.path.join(dirs['data'], f'val_20251213_val_hist.root')

sig_in      = os.path.join(dirs['data'], f'val_20251213_sig_hist*.root')
val_in      = os.path.join(dirs['data'], f'val_20251213_val_hist*.root')


CMD_dict = {'sig':  [f'hadd -f {sig_out}   {sig_in}'],
            'val':  [f'hadd -f {val_out}   {val_in}']
            }



for key, cmds in CMD_dict.items():
    for cmd in cmds:
        print ('CMD:')
        print(cmd)
        print()
        run(cmd, shell=True)
        print('-'*80)
        print()