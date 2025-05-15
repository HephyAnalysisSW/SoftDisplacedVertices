#!/usr/bin/env python

import os
import json
import shutil
import SoftDisplacedVertices.Samples.Samples as s
import SoftDisplacedVertices.Samples.cmsRunJobs as job

dryrun = False
#input_label = "CustomMiniAODv1"
input_label = "AOD"
version = "CustomMiniAOD_v3_decaymode"

j = job.cmsRunJob(cfg='MC_UL18_CustomMiniAOD.py',logLevel = "INFO",redirector = "file:")

#input_samples = s.znunu_2018 + s.wlnu_2018
input_samples = [s.stop_2018[1]]
#input_samples = s.c1n2_2018

s.loadData(input_samples,os.path.join(os.environ['CMSSW_BASE'],'src/SoftDisplacedVertices/Samples/json/CustomMiniAOD_v3_decaymode.json'),input_label)

for sp in input_samples:
  targetDir = "/scratch-cbe/users/ang.li/SoftDV/CLIP_{0}/{1}/".format(version,sp.name)
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

    j.setJob(title=sp.name+input_label+version, input="filename.txt",redirector = "file:",targetDir=targetDir,n_files=1)
    j.prepare()
    j.submit(dryrun=dryrun)
    shutil.move("filename.txt",os.path.join(targetDir+'/input',"filename.txt"))
    j.reset()


