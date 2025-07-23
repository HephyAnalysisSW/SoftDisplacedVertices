import os,glob
import re
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
  with open('jobs.sh','wb') as rf:
    for d in os.listdir(args.dir):
      if (d=='input') or (not os.path.isdir(os.path.join(args.dir,d))):
        continue
  
      jobsh = glob.glob(os.path.join(args.dir,d,'input',"job_*.sh"))
      assert len(jobsh)==1, "more than one .sh file found!"
      with open(jobsh[0], 'r') as file:
        for line in file:
          match = re.search(r'output/out_NANOAODSIMoutput_\d+\.root', line)
          if not match:
            raise Exception("Output file pattern not found!")
  
          outputfile = match.group()
          if not os.path.exists(os.path.join(args.dir,d,outputfile)):
            print("\033[1;31m Not all jobs succeeded for {}: {} missing. \033[0m".format(d,outputfile))
            rf.write(line)
  


