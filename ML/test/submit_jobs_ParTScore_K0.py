#!/usr/bin/env python

import os
import json
import uuid
import shutil
import SoftDisplacedVertices.Samples.Samples as s
import SoftDisplacedVertices.Samples.cmsRunJobs as job

dryrun = True
input_label = "CustomNanoAOD"
version = "RotateK0"

input_samples = s.znunu_2018+s.wlnu_2018+s.qcd_2018+s.top_2018
#input_samples = s.met_2018

s.loadData(input_samples,os.path.join(os.environ['CMSSW_BASE'],'src/SoftDisplacedVertices/Samples/json/scratch_MC.json'),input_label)
#s.loadData(input_samples,os.path.join(os.environ['CMSSW_BASE'],'src/SoftDisplacedVertices/Samples/json/scratch_data.json'),input_label)

jobf = open("jobs.sh","w")

for sp in input_samples:
  targetDir = "/scratch-cbe/users/ang.li/SoftDV/NanoAOD_{0}/{1}/".format(version,sp.name)
  os.makedirs(targetDir)
  uuid_ =  str(uuid.uuid4())
  input_fns = sp.getFileList(input_label,"")
  print(len(input_fns))
  i = 0
  for fn in input_fns:
    command = "set -e;mkdir /tmp/%s;" % (uuid_)
    command += "cd /tmp/%s;" %(uuid_)
    command += "nano_postproc.py outDir %s -I SoftDisplacedVertices.ML.ParTScore_K0_run2 ParTScoreModuleConstr;" % (fn)
    command += "cp /tmp/%s/outDir/*.root %s/output_%i.root;" %(uuid_,targetDir,i)
    command += '\n'
    jobf.write(command)
    i += 1

jobf.close()
inputdir = "/scratch-cbe/users/ang.li/SoftDV/NanoAOD_{0}/{1}/".format(version,'input')
if not os.path.exists(inputdir):
    os.makedirs(inputdir)
jbfn = 'jobs{}.sh'
ij = ''
if os.path.exists(os.path.join(inputdir,jbfn.format(ij))):
  ij=1
  while os.path.exists(os.path.join(inputdir,jbfn.format(ij))):
    ij += 1
shutil.copy2('jobs.sh',os.path.join(inputdir,jbfn.format(ij)))
