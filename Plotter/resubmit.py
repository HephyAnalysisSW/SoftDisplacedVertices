import os,glob
import re
import math
import uuid
import shutil
import SoftDisplacedVertices.Plotter.plotter as p
import SoftDisplacedVertices.Plotter.plot_setting as ps
import SoftDisplacedVertices.Samples.Samples as s

import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--sample', type=str, nargs='+',
                        help='samples to process')
parser.add_argument('--jobdir', type=str,
                        help='output dir')
parser.add_argument('--config', type=str,
                        help='config to use') 
parser.add_argument('--lumi', type=float, default=59683.,
                        help='luminosity to normalise MC samples')
parser.add_argument('--json', type=str, 
                        help='json for file paths') 
parser.add_argument('--datalabel', type=str,
                        help='datalabel to use in json file') 
parser.add_argument('--year', type=str,
                        help='Which year does the data correspond to') 
parser.add_argument('--data', action='store_true', default=False,
                        help='Whether the input is data') 
args = parser.parse_args()

if __name__=="__main__":

  jobf = open('jobs.sh',"w")
  if args.data:
    data = '--data'
  else:
    data=''
  all_samples = []
  for samp in args.sample:
    s_samp = getattr(s,samp)
    if isinstance(s_samp, list): 
      all_samples += s_samp
    else:
      all_samples.append(s_samp)
  for samp in all_samples:
    d = samp.name
    jobs_full = glob.glob(os.path.join(args.jobdir,d,'input','*.txt'))
    jobs = []
    for ij in jobs_full:
      match = re.search(r'_fn(\d+)\.txt', ij)
      if match:
        jidx = match.group(1)
      else:
        raise Exception("No index can be found in filename!")
      jobs.append(jidx)
    files_full = glob.glob(os.path.join(args.jobdir,d,'*.root'))
    files = []
    for ifi in files_full:
      match = re.search(r'hist_(\d+)\.root', ifi)
      if match:
        fidx = match.group(1)
      else:
        raise Exception("No index can be found in filename!")
      files.append(fidx)
    pkls_full = glob.glob(os.path.join(args.jobdir,d,'*.pkl'))
    pkls = []
    for ipkl in pkls_full:
      match = re.search(r'hist_(\d+)\.pkl', ipkl)
      if match:
        fidx = match.group(1)
      else:
        raise Exception("No index can be found in filename!")
      pkls.append(fidx)
    jobs_miss = []
    for ij in jobs:
      if (not ij in files) or (not ij in pkls):
        jobs_miss.append(ij)
    if len(jobs_miss)>0:
      print("\033[1;31m Not all jobs succeeded for {}. \033[0m".format(d))
      print(" Jobs missing: {}".format(jobs_miss))

    for ij in jobs_miss:
      # clean the directory
      rootfn = os.path.join(args.jobdir,d,'{}_hist_{}.root'.format(d,ij))
      pklfn = os.path.join(args.jobdir,d,'{}_hist_{}.pkl'.format(d,ij))
      if os.path.exists(rootfn):
        os.remove(rootfn)
        print("File {} removed.".format(rootfn))
      if os.path.exists(pklfn):
        os.remove(pklfn)
        print("File {} removed.".format(pklfn))

      flname = "{}_fn{}.txt".format(d,ij)
      uuid_ =  str(uuid.uuid4())
      command = "set -e; mkdir /tmp/%s;" % (uuid_)
      command += "cd /tmp/%s;" %(uuid_)
      if 'eos' in args.jobdir:
        command += "xrdcp -r root://eos.grid.vbc.ac.at/%s /tmp/%s/.;" %(os.path.join(args.jobdir,'input'),uuid_)
        command += "cp /tmp/%s/input/* /tmp/%s/.;" %(uuid_,uuid_)
        command += "xrdcp -r root://eos.grid.vbc.ac.at/%s /tmp/%s/input/.;" %(os.path.join(args.jobdir,d,'input'),uuid_)
        command += "cp /tmp/%s/input/input/* /tmp/%s/.;" %(uuid_,uuid_)
      else:
        command += "cp %s /tmp/%s/.;" %(os.path.join(args.jobdir,'input')+'/*',uuid_)
        command += "cp %s /tmp/%s/.;" %(os.path.join(args.jobdir,d,'input')+'/*',uuid_)

      #command += "cp %s /tmp/%s/.;" %(os.path.join(args.jobdir,d,'input')+'/*',uuid_)
      command += "python3 autoplotter.py --sample {} --output ./ --config ./{} --lumi {} --json {} --datalabel {} --filelist ./{} --year {} --postfix _{} {};".format(d,os.path.basename(args.config),args.lumi,args.json,args.datalabel,flname,args.year,ij,data)
      if 'eos' in args.jobdir:
        fname = "{}_hist_{}".format(d,ij)
        command += "eoscp ./{}.root {}/.;".format(fname,os.path.join(args.jobdir,d))
        command += "eoscp ./{}.pkl {}/.;".format(fname,os.path.join(args.jobdir,d))
      else:
        command += "cp ./*.root {}/.;".format(os.path.join(args.jobdir,d))
        command += "cp ./*.pkl {}/.;".format(os.path.join(args.jobdir,d))
      command += "\n"
      jobf.write(command)
  jobf.close()
  jbfn = 'jobs_resub_{}.sh'
  ij = ''
  if os.path.exists(os.path.join(args.jobdir,'input',jbfn.format(ij))):
    ij=1
    while os.path.exists(os.path.join(args.jobdir,'input',jbfn.format(ij))):
      ij += 1
  shutil.copy2('jobs.sh',os.path.join(args.jobdir,'input',jbfn.format(ij)))

