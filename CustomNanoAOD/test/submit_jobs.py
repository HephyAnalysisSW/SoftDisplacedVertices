#!/usr/bin/env python

import os
import json
import shutil
import SoftDisplacedVertices.Samples.Samples as s
import SoftDisplacedVertices.Samples.cmsRunJobs as job

dryrun = False
#input_label = "CustomMiniAOD"
input_label = "CustomMiniAOD_v3"
version = "CustomNanoAOD_v3_GNNAVRIVF_new"

j = job.cmsRunJob(cfg='MC_UL18_CustomNanoAOD.py',logLevel = "INFO")

#input_samples = s.znunu_2018+s.wlnu_2018+s.qcd_2018+s.top_2018
input_samples = [s.stop_M600_588_ct200_2018,s.stop_M600_588_ct20_2018,s.stop_M600_585_ct20_2018,s.stop_M600_585_ct2_2018]

#s.loadData(input_samples,os.path.join(os.environ['CMSSW_BASE'],'src/SoftDisplacedVertices/Samples/json/MC_RunIISummer20UL18.json'),input_label)
s.loadData(input_samples,os.path.join(os.environ['CMSSW_BASE'],'src/SoftDisplacedVertices/Samples/json/Signal_CentralProduction.json'),input_label)

for sp in input_samples:
  targetDir = "/scratch-cbe/users/ang.li/SoftDV/CLIP_{0}/{1}/".format(version,sp.name)
  #assert not os.path.exists(targetDir), "Path {} already exists!".format(targetDir)
  if os.path.exists(targetDir):
    print("Path {} already exists!".format(targetDir))
    continue
  useDBS = False
  #if input_label in sp.dataset:
  #  useDBS = True
  if useDBS:
    input = 'dbs:'+sp.dataset[input_label]
    j.setJob(title=sp.name+input_label+version,input=input,instance=sp.dataset_instance[input_label],targetDir=targetDir,n_files=1)

    j.prepare()
    j.submit(dryrun=dryrun)
    j.reset()
  else:
    with open("filename.txt","w") as fns:
      fns.write("\n".join(sp.getFileList(input_label,"")))

    j.setJob(title=sp.name+input_label+version, input="filename.txt",targetDir=targetDir,redirector = "root://eos.grid.vbc.ac.at/",n_files=1)
    j.prepare()
    j.submit(dryrun=dryrun)
    shutil.move("filename.txt",os.path.join(targetDir+'/input',"filename.txt"))
    j.reset()


