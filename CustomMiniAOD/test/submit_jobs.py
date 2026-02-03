#!/usr/bin/env python

import os
import json
import shutil
import SoftDisplacedVertices.Samples.Samples as s
import SoftDisplacedVertices.Samples.cmsRunJobs as job

dryrun = True
input_label = "AOD"
version = "CustomMiniAOD_2022JetMET_FG"

j = job.cmsRunJob(cfg='Data_Run2022FG_CustomMiniAOD.py',logLevel = "INFO")

input_samples = [s.jetmet_2022f,s.jetmet_2022g]

s.loadData(input_samples,os.path.join(os.environ['CMSSW_BASE'],'src/SoftDisplacedVertices/Samples/json/Data_Run3_jetmet_official.json'),input_label,'global')

sub_cmd = []
for sp in input_samples:
  print(sp.name)
  print(sp.dataset)
  targetDir = "/eos/vbc/experiments/cms/store/user/lian/SoftDV/CLIP_{0}/{1}/".format(version,sp.name)
  if os.path.exists(targetDir):
    print("Path {} already exists!".format(targetDir))
    continue
  assert not os.path.exists(targetDir)
  useDBS = False
  if input_label in sp.dataset:
    useDBS = True
  if useDBS:
    input = 'dbs:'+sp.dataset[input_label]
    j.setJob(title=sp.name+input_label+version,input=input,instance=sp.dataset_instance[input_label],redirector="root://eos.grid.vbc.ac.at/",targetDir=targetDir,target_redirector="root://eos.grid.vbc.ac.at/",n_files=10)

    j.prepare()
    c = j.submit(dryrun=dryrun)
    j.reset()
    sub_cmd.append(c)
  else:
    with open("filename.txt","w") as fns:
      fns.write("\n".join(sp.getFileList(input_label,"")))

    j.setJob(title=sp.name+input_label+version, input="filename.txt",redirector = "file:",targetDir=targetDir,n_files=5)
    j.prepare()
    c = j.submit(dryrun=dryrun)
    shutil.move("filename.txt",os.path.join(targetDir+'/input',"filename.txt"))
    j.reset()
    sub_cmd.append(c)

with open('jobs.sh','w') as f:
    for i in sub_cmd:
        f.write(i+';\n')
