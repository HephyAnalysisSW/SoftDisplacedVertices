from subprocess import run, PIPE
import SoftDisplacedVertices.Samples.Samples as ss
import re
import json
import os

year = 2018
outDir_base = "/scratch-cbe/users/alikaan.gueven/AN_plots/"
work_subdir = "vtx_reco/mc_data/"
unique_dir  = "20241210"
work_dir = os.path.join(outDir_base, work_subdir)

dirs  = {'sig':  os.path.join(os.path.join(work_dir, 'sig'),  str(unique_dir)),
         'bkg':  os.path.join(os.path.join(work_dir, 'bkg'),  str(unique_dir)),
         'data': os.path.join(os.path.join(work_dir, 'data'), str(unique_dir))}


met_out   = os.path.join(dirs['data'],f'met_{year}_hist.root')
wjets_out = os.path.join(dirs['bkg'], f'wjets_{year}_hist.root')
zjets_out = os.path.join(dirs['bkg'], f'zjets_{year}_hist.root')
qcd_out   = os.path.join(dirs['bkg'], f'qcd_{year}_hist.root') 
top_out   = os.path.join(dirs['bkg'], f'top_{year}_hist.root')

met_in   = os.path.join(dirs['data'],f'met{year}*_hist.root')
wjets_in = os.path.join(dirs['bkg'], f'wjetstolnuht*{year}_hist.root')
zjets_in = os.path.join(dirs['bkg'], f'zjetstonunuht*{year}_hist.root')
qcd_in =   os.path.join(dirs['bkg'], f'qcdht*{year}_hist.root')
top_in = ' '.join([os.path.join(dirs['bkg'], f'st_*{year}_hist.root'),
                os.path.join(dirs['bkg'], f'ttbar_{year}_hist.root')])


CMD_dict = {'bkg':  [f'hadd {wjets_out} {wjets_in}',
                     f'hadd {zjets_out} {zjets_in}',
                     f'hadd {qcd_out}   {qcd_in}',
                     f'hadd {top_out}   {top_in}'],
            'data': [f'hadd {met_out}   {met_in}']}

for key, cmds in CMD_dict.items():
    for cmd in cmds:
        print ('CMD:')
        print(cmd)
        print()
        run(cmd, shell=True)
        print('-'*80)
        print()