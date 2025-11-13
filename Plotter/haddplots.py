import os,glob
import subprocess
import pickle
import numpy as np
import colorama
from colorama import Fore
import SoftDisplacedVertices.Samples.Samples as s

import argparse

def addpkls(pkls):
  d_new = {}
  for ipkl in pkls:
    print(ipkl)
    with open(ipkl,'rb') as f:
      data = pickle.load(f)
    for k in data:
      if not k in d_new:
        d_new[k] = {}
      for kk in data[k]:
        if not kk in d_new[k]:
          d_new[k][kk] = []
        if len(data[k][kk])==0:
          continue
        d_new[k][kk].append(data[k][kk])
  for k in d_new:
    for kk in d_new[k]:
      if len(d_new[k][kk])==0:
        d_new[k][kk] = np.array(d_new[k][kk])
      else:
        d_new[k][kk] = np.concatenate(d_new[k][kk],axis=0)
  return d_new


if __name__=="__main__":

  parser = argparse.ArgumentParser()
  parser.add_argument('--dir', type=str,
      help='directory of the jobs')
  parser.add_argument('--pkl', action='store_true',
      help='whether pkl files should be added.')
  args = parser.parse_args()

  for d in os.listdir(args.dir):
    if (d=='input') or (not os.path.isdir(os.path.join(args.dir,d))):
      continue
    njobs = len(glob.glob(os.path.join(args.dir,d,'input','*.txt')))
    nfiles = len(glob.glob(os.path.join(args.dir,d,'*.root')))
    if not nfiles==njobs:
      #print("\033[1;31m Not all files are processed. Will hadd whatever if availible.\033[0m")
      print("\033[1;31m Not all files are processed. Skipping...\033[0m")
      continue
    targetpath = os.path.join(args.dir,'{0}_hist.root'.format(d))
    if os.path.exists(targetpath):
      print("\033[1;31m File {} already exists! Skipping...\033[0m".format(targetpath))
      continue
    else:
      haddcmd = 'hadd {0} {1}/{2}/*.root > {1}/{2}/haddlog.txt'.format(targetpath,args.dir,d)
      print(haddcmd)
      process = subprocess.Popen(haddcmd,shell=True,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
      stdout, stderr = process.communicate()
      if (process.returncode!=0):
        print("\033[1;31m Hadd failed! Error message below:\033[0m")
        print(stderr)
    if args.pkl:
      npkl = len(glob.glob(os.path.join(args.dir,d,'*.pkl')))
      if not npkl==njobs:
        print("\033[1;31m Not all files are processed. Skipping...\033[0m")
        continue
      targetpath = os.path.join(args.dir,'{0}_hist.pkl'.format(d))
      if os.path.exists(targetpath):
        print("\033[1;31m File {} already exists! Skipping...\033[0m".format(targetpath))
        #continue
      else:
        sourcepath = glob.glob(os.path.join(args.dir,d,'*.pkl'))
        try:
          dtotal = addpkls(sourcepath)
          with open(targetpath,'wb') as f:
            pickle.dump(dtotal,f)
        except Exception as e:
          print(Fore.RED + f"Error: {e}")

