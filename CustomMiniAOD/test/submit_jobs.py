#!/usr/bin/env python

import os
import json
import shutil
import SoftDisplacedVertices.Samples.Samples as s
import SoftDisplacedVertices.Samples.cmsRunJobs as job

dryrun = True
#input_label = "CustomMiniAODv1"
#input_label = "CustomMiniAOD_v3"
input_label = "AOD"
#version = "CustomMiniAOD_MLstudy"
version = "CustomMiniAOD_v3_test"
#version = "CustomMiniAOD_lowdm"

j = job.cmsRunJob(cfg='MC_Run3Summer24_CustomMiniAOD.py',logLevel = "INFO")

input_samples = [s.c1n2_2024[0]]

s.loadData(input_samples,os.path.join(os.environ['CMSSW_BASE'],'src/SoftDisplacedVertices/Samples/json/PrivateSignal_2024.json'),input_label)

for sp in input_samples:
  print(sp.name)
  targetDir = "/scratch-cbe/users/ang.li/SoftDV/CLIP_{0}/{1}/".format(version,sp.name)
  if os.path.exists(targetDir):
    continue
  assert not os.path.exists(targetDir)
  useDBS = False
  if input_label in sp.dataset:
    useDBS = True
  if useDBS:
    input = 'dbs:'+sp.dataset[input_label]
    j.setJob(title=sp.name+input_label+version,input=input,instance=sp.dataset_instance[input_label],targetDir=targetDir,n_files=5)

    j.prepare()
    j.submit(dryrun=dryrun)
    j.reset()
  else:
    with open("filename.txt","w") as fns:
      fns.write("\n".join(sp.getFileList(input_label,"")))

    j.setJob(title=sp.name+input_label+version, input="filename.txt",redirector = "file:",targetDir=targetDir,n_files=5)
    j.prepare()
    j.submit(dryrun=dryrun)
    shutil.move("filename.txt",os.path.join(targetDir+'/input',"filename.txt"))
    j.reset()


