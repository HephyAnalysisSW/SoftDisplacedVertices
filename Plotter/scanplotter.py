# Example usage:
# python3 autoplotter.py --sample stop_M600_580_ct2_2018 --output ./ --config /users/ang.li/public/SoftDV/CMSSW_13_3_0/src/SoftDisplacedVertices/Plotter/plotconfig_sig.yaml --lumi 59683. --json MLNanoAOD.json --metadata metadata_CustomMiniAOD_v3.yaml --datalabel MLNanoAODv2

import os
import uuid
import shutil
import itertools
import SoftDisplacedVertices.Plotter.plotter as p
import SoftDisplacedVertices.Plotter.plot_setting as ps
import SoftDisplacedVertices.Samples.Samples as s

import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--sample', type=str, nargs='+',
                        help='samples to process')
parser.add_argument('--output', type=str,
                        help='output dir')
parser.add_argument('--config', type=str,
                        help='config to use') 
parser.add_argument('--lumi', type=float, default=59683.,
                        help='luminosity to normalise MC samples')
parser.add_argument('--json', type=str, 
                        help='json for file paths') 
parser.add_argument('--metadata', type=str, 
                        help='metadata for sum gen weights of MC samples') 
parser.add_argument('--datalabel', type=str,
                        help='datalabel to use in json file') 
parser.add_argument('--submit', action='store_true', default=False,
                        help='Whether to scale the plot')
args = parser.parse_args()


def dict_product(dicts):
    return (dict(zip(dicts, x)) for x in itertools.product(*dicts.values()))

if __name__=="__main__":

  all_samples = []
  for samp in args.sample:
    s_samp = getattr(s,samp)
    if isinstance(s_samp, list): 
      all_samples += s_samp
    else:
      all_samples.append(s_samp)

  DPHIMET = [1.5]
  DPHIJET = [1]
  LXYSIG = [20]
  PANGLE = [0.2]
  NGOODTK = [1,2,3]
  TKDXYSIG = [4]
  TKDXYDZ = [0.1,0.15,0.2]
  #scan_params = {
  #    '__DPHIMET__': [1.5],
  #    '__DPHIJET__': [1],
  #    '__LXYSIG__': [0,10,20],
  #    '__PANGLE__': [0,0.1,0.2],
  #    '__NGOODTK__': [0,1,2],
  #    '__TKDXYSIG__': [2,3,4],
  #    '__TKDXYDZ__': [0.1,0.15,0.2,0.25,0.3],
  #    '__ML__': [0.97,0.98,0.99],
  #    }
  scan_params = {
      #'__DPHIMET__': [1.5],
      #'__DPHIJET__': [1],
      #'__LXYSIG__': [20],
      #'__PANGLE__': [0.2],
      #'__NGOODTK__': [2],
      #'__TKDXYSIG__': [2,3,4,5,6],
      #'__TKDXYDZ__': [0.1,0.15,0.2,0.25,0.3,0.35,0.4],
      #'__ML__': [0.97,0.98,0.99],
      #'__DPHIMET__': [1.5],
      #'__DPHIJET__': [1],
      #'__LXYSIG__': [0],
      #'__PANGLE__': [0],
      #'__NGOODTK__': [0],
      #'__TKDXYSIG__': [4],
      #'__TKDXYDZ__': [0.25],
      #'__ML__': [0.97,0.98,0.99],
      '__DPHIMET__': [1.5],
      '__DPHIJET__': [1],
      '__ISO__': [5],
      }

  if args.submit:
    jobf = open('jobs.sh',"w")
    for cuts in list(dict_product(scan_params)):
      tag = ''
      with open(args.config, 'r') as f:
        cfg = f.read()
      for cut in cuts:
        tag+=(cut+str(cuts[cut]).replace('.','p'))
        cfg = cfg.replace(cut,str(cuts[cut]))

      outputDir = os.path.join(args.output,'cutscan'+tag)
      assert (not os.path.exists(outputDir)),"Path {} already exists!".format(outputDir)
      os.makedirs(outputDir)
      inputdir = outputDir+'/input'
      os.makedirs(inputdir)
      shutil.copy2(os.path.join(os.getcwd(),'autoplotter.py'),inputdir)
      with open(os.path.join(inputdir,'config.yaml'), 'w') as f:
        f.write(cfg)
      #for samp in all_samples:
      for samp in ["znunu_2018 wlnu_2018 stop_2018"]:
        uuid_ =  str(uuid.uuid4())
        command = "mkdir /tmp/%s;" % (uuid_)
        command += "cd /tmp/%s;" %(uuid_)
        command += "cp %s /tmp/%s/.;" %(inputdir+'/*',uuid_)
        #command += "python3 autoplotter.py --sample {} --output ./ --config config.yaml --lumi {} --json {} --metadata {} --datalabel {};".format(samp.name,args.lumi,args.json,args.metadata,args.datalabel)
        command += "python3 autoplotter.py --sample {} --output ./ --config config.yaml --lumi {} --json {} --metadata {} --datalabel {};".format(samp,args.lumi,args.json,args.metadata,args.datalabel)
        command += "cp ./*.root {}/.;".format(outputDir)
        command += "\n"
        jobf.write(command)
    jobf.close()

