from subprocess import run, PIPE
import SoftDisplacedVertices.Samples.Samples as ss
import re
import json
import os

year = 2022
outDir_base = "/scratch-cbe/users/alikaan.gueven/AN_plots"
work_subdir = "checks_2022"
unique_dir  = "check_1_ee"
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
            'data': [f'hadd -f {met_out}   {met_in}']
            }

for key, cmds in CMD_dict.items():
    for cmd in cmds:
        print ('CMD:')
        print(cmd)
        print()
        run(cmd, shell=True)
        print('-'*80)
        print()