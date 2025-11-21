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
unique_dir  = "vtx_PART_859_epoch_87_test1_copy"
workbase_dir = os.path.join(outDir_base, work_subdir)
work_dir = os.path.join(workbase_dir, unique_dir)

dirs  = {'sig':  os.path.join(work_dir, 'sig'),
         'bkg':  os.path.join(work_dir, 'bkg'),
         'data': os.path.join(work_dir, 'data')}


met_out      = os.path.join(dirs['data'],f'met_{year}_hist.root')
wjets_out    = os.path.join(dirs['bkg'], f'wjets_{year}_hist.root')
zjets_out    = os.path.join(dirs['bkg'], f'zjets_{year}_hist.root')
qcd_out      = os.path.join(dirs['bkg'], f'qcd_{year}_hist.root') 
top_out      = os.path.join(dirs['bkg'], f'top_{year}_hist.root')
all_bkg_out  = os.path.join(dirs['bkg'], f'all_{year}_hist.root')

met_in      = os.path.join(dirs['data'],f'met{year}*.root')
wjets_in    = os.path.join(dirs['bkg'], f'w*{year}*.root')
zjets_in    = os.path.join(dirs['bkg'], f'z*{year}*.root')
qcd_in      = os.path.join(dirs['bkg'], f'qcd*{year}*.root')
top_in      = os.path.join(dirs['bkg'], f'tt*{year}*.root')
if year < 2022:
    top_in = top_in + " " + os.path.join(dirs['bkg'], f'st_*{year}*.root')


all_bkg_in  = f"{wjets_out} {zjets_out} {qcd_out} {top_out}"

CMD_dict = {'bkg':  [f'hadd -f {wjets_out} {wjets_in}',
                     f'hadd -f {zjets_out} {zjets_in}',
                     f'hadd -f {qcd_out}   {qcd_in}',
                     f'hadd -f {top_out}   {top_in}',
                     f'hadd -f {all_bkg_out}   {all_bkg_in}'],
            # 'data': [f'hadd -f {met_out}   {met_in}']
            }

# ----------------   signal   ----------------------------------------------------
# group the individual signals like stop_..._hist0.root stop_..._hist1.root stop_..._hist2.root
# without mixing different signal points.
# 
glob_pattern = os.path.join(dirs['sig'], f'stop_M*_ct*_2018_hist*.root')
files = glob.glob(glob_pattern)

# Dictionary to group files by their common prefix
groups = defaultdict(list)

# Regular expression to extract the group key (everything before _hist...)
pattern = re.compile(r"(stop_M\d+_\d+_ct\d+_2018)_hist\d+\.root")

for f in files:
    match = pattern.match(os.path.basename(f))
    if match:
        key = match.group(1)  # e.g., "stop_M600_585_ct20_2018"
        groups[key].append(f)

sig_commands = []
for key, group in groups.items():
    group_out = os.path.join(dirs['sig'], f"{key}_hist.root")
    sig_commands.append(f'hadd -f {group_out} {" ".join(group)}')

# --------------------------------------------------------------------------------

CMD_dict['sig'] = sig_commands




for key, cmds in CMD_dict.items():
    for cmd in cmds:
        print ('CMD:')
        print(cmd)
        print()
        run(cmd, shell=True)
        print('-'*80)
        print()