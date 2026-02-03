#!/usr/bin/env python

### This script takes the job directory and summarizes the job output as a json file

import os
import json
import argparse
import shutil
import subprocess

import SoftDisplacedVertices.Samples.Samples as sps

parser = argparse.ArgumentParser()
parser.add_argument('--label', help="label of jobs / datasets")
parser.add_argument('--dir', help="directory of jobs")
parser.add_argument('--output', default=None, help="Path to transfer the output")
parser.add_argument('--redirector', default="root://eos.grid.vbc.ac.at/", help="Redirector if transfering to eos")
parser.add_argument('--eos', action='store_true', help="Whether the output is in eos")
args = parser.parse_args()

assert os.path.exists(args.dir), "Dir {} does not exist!".format(args.dir)
if args.output is None:
  args.output = '/eos/vbc/experiments/cms/store/user/{0}/{1}/'.format(os.environ['CERN_USER'],args.label)
  args.eos = True

if os.path.exists(args.output):
  print("Output path already exists!")
else:
  if args.eos:
    p = subprocess.Popen("xrdfs {0} mkdir {1}".format(args.redirector,args.output), stdout = subprocess.PIPE,stderr = subprocess.STDOUT, shell=True)
  else:
    os.makedirs(args.output)


d = {
      args.label:{
        "dataset":{},
        "dir":{},
      },
    }

for s in os.listdir(args.dir):
  valid = False
  try:
    getattr(sps,s)
  except:
    valid = False
  else:
    valid = True
  if valid:
    with open(os.path.join(args.dir,s,"log/jobinfo.json"),'r') as fj:
      info = json.load(fj)
    source_dir = info["output"]
    newdir = os.path.join(args.output,s)
    if os.path.exists(newdir):
      print("Target directory already exists! {}".format(newdir))
      print("Will override...")
    if args.eos:
      print("xrdfs {0} mkdir -p {1}".format(args.redirector,newdir))
      p = subprocess.Popen(args="xrdfs {0} mkdir -p {1}".format(args.redirector,newdir),stdout = subprocess.PIPE,stderr = subprocess.STDOUT, shell=True)
      print(p.stdout.read())
      print("xrdcp -rf -np {0} {1}".format(source_dir,args.redirector+newdir))
      p = subprocess.Popen(args="xrdcp -rf -np {0} {1}".format(source_dir,args.redirector+newdir),stdout = subprocess.PIPE,stderr = subprocess.STDOUT, shell=True)
      print(p.stdout.read())
    else:
      shutil.copytree(os.path.join(args.dir,s),newdir, dirs_exist_ok=True)
    d[args.label]["dir"][s] = os.path.join(newdir,os.path.basename(info["output"]))

json_name = os.path.join(os.environ['CMSSW_BASE'],'src/SoftDisplacedVertices/Samples/json/{}'.format(args.label))

if os.path.exists(json_name+'.json'):
  i = 1
  json_name += '_{}'
  while os.path.exists(json_name.format(i)+'.json'):
    i += 1

  json_name_new = json_name.format(i)
else:
  json_name_new = json_name

assert not os.path.exists(json_name_new+'.json')

with open(json_name_new+'.json',"w") as f:
  json.dump(d,f,indent=4)

