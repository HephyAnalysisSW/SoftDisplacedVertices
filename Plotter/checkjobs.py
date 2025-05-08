import os,glob
import shutil
import subprocess
import SoftDisplacedVertices.Samples.Samples as s

import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--dir', type=str,
    help='directory of the jobs')
parser.add_argument('--rm', action='store_true', default=False,
    help='whether to remove the failed dir.')
args = parser.parse_args()

if __name__=="__main__":
  for d in os.listdir(args.dir):
    if (d=='input') or (not os.path.isdir(os.path.join(args.dir,d))):
      continue
    njobs = len(glob.glob(os.path.join(args.dir,d,'input','*.txt')))
    nfiles = len(glob.glob(os.path.join(args.dir,d,'*.root')))
    npkl = len(glob.glob(os.path.join(args.dir,d,'*.pkl')))
    if (not nfiles==njobs) or (not npkl==njobs):
      print("\033[1;31m Not all jobs succeeded for {}. \033[0m".format(d))
      if args.rm:
        print("Removing {}".format(os.path.join(args.dir,d)))
        shutil.rmtree(os.path.join(args.dir,d))


