#!/usr/bin/env python

import os
import json
import shutil
import SoftDisplacedVertices.Samples.Samples as s
import SoftDisplacedVertices.Samples.cmsRunJobs as job

dryrun = False
input_label = "CustomMiniAOD_v3_MLTraining_new"
#input_label = "CustomMiniAODv0"
#version = "CustomNanoAODv0_IVF_nosharetk"
version = "MLTree_v3_MLTraining_GNNKF"

j = job.cmsRunJob(cfg='mltree_cfg.py',logLevel = "INFO")

#input_samples = s.znunu_2018 + s.stop_2018[0:3]
input_samples = s.stop_2018
#input_samples = [s.stop_M600_585_ct20]

s.loadData(input_samples,os.path.join(os.environ['CMSSW_BASE'],'src/SoftDisplacedVertices/Samples/json/CustomMiniAOD_v3_MLTraining.json'),input_label)

for sp in input_samples:
  targetDir = "/scratch-cbe/users/ang.li/SoftDV/MLTree_{0}/{1}/".format(version,sp.name)
  assert not os.path.exists(targetDir)
  useDBS = False
  if input_label in sp.dataset:
    useDBS = True
  if useDBS:
    input = 'dbs:'+sp.dataset[input_label]
    j.setJob(title=sp.name+input_label+version,input=input,instance=sp.dataset_instance[input_label],targetDir=targetDir,n_files=100)

    j.prepare()
    j.submit(dryrun=dryrun)
    j.reset()
  else:
    with open("filename.txt","w") as fns:
      fns.write("\n".join(sp.getFileList(input_label,"")))

    j.setJob(title=sp.name+input_label+version, input="filename.txt",targetDir=targetDir,n_files=100)
    j.prepare()
    j.submit(dryrun=dryrun)
    shutil.move("filename.txt",os.path.join(targetDir+'/input',"filename.txt"))
    j.reset()


