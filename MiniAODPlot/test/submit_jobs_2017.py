#!/usr/bin/env python

import os
import json
import shutil
import SoftDisplacedVertices.Samples.Samples as s
import SoftDisplacedVertices.Samples.cmsRunJobs as job

dryrun = False
input_label = "CustomMiniAOD"
version = "MaterialMap_muon"

j = job.cmsRunJob(cfg='runplot_2017_cfg.py',logLevel = "INFO")

input_samples = s.muon_2017 

s.loadData(input_samples,os.path.join(os.environ['CMSSW_BASE'],'src/SoftDisplacedVertices/Samples/json/Data_muon_run2.json'),input_label)

for sp in input_samples:
  targetDir = "/scratch-cbe/users/ang.li/SoftDV/CLIP_{0}/{1}/".format(version,sp.name)
  assert not os.path.exists(targetDir), "Path {} already exists!".format(targetDir)
  useDBS = False
  if input_label in sp.dataset:
    useDBS = True
  if useDBS:
    input = 'dbs:'+sp.dataset[input_label]
    j.setJob(title=sp.name+input_label+version,input=input,instance=sp.dataset_instance[input_label],targetDir=targetDir,redirector = "root://eos.grid.vbc.ac.at/",n_files=20)

    j.prepare()
    j.submit(dryrun=dryrun)
    j.reset()
  else:
    with open("filename.txt","w") as fns:
      fns.write("\n".join(sp.getFileList(input_label,"")))

    j.setJob(title=sp.name+input_label+version, input="filename.txt",targetDir=targetDir,redirector = "root://eos.grid.vbc.ac.at/",n_files=20)
    j.prepare()
    j.submit(dryrun=dryrun)
    shutil.move("filename.txt",os.path.join(targetDir+'/input',"filename.txt"))
    j.reset()


