#!/usr/bin/env python

import os
import uuid
import shutil
import argparse
import SoftDisplacedVertices.Samples.Samples as s

parser = argparse.ArgumentParser(description="Prepare ParTScore_K nano_postproc jobs for slurm submission")
parser.add_argument("--era", required=True, choices=["run2", "2022_2023", "2024"])
parser.add_argument("--data", action="store_true", help="prepare JetMET data jobs instead of MC")
args = parser.parse_args()

input_label = "CustomNanoAOD"
version = "ParTScore_K"
eos_redirector = "root://eos.grid.vbc.ac.at/"
eos_basedir = "/eos/vbc/experiments/cms/store/user/lian/NanoAOD_{0}/".format(version)
proxy = "/users/ang.li/private/.proxy"
# dasgoclient (file listing of the Run3 data samples) needs the proxy at submission time as well
os.environ.setdefault("X509_USER_PROXY", proxy)
# input files of one sample are grouped into jobs of at most this total size
max_input_bytes_per_job = 10e9
jsondir = os.path.join(os.environ['CMSSW_BASE'], 'src/SoftDisplacedVertices/Samples/json')

# era -> lists of (samples, json file) for MC and data, postproc module, name of the jobs file copied to the input dir
era_config = {
    "run2": {
        "samples": [
            (s.znunu_2017+s.wlnu_2017+s.qcd_2017+s.top_2017, "MC_RunIISummer20UL17_20241003.json"),
            (s.znunu_2018+s.wlnu_2018+s.qcd_2018+s.top_2018, "MC_RunIISummer20UL18_20241003.json"),
        ],
        "data_samples": [
            (s.met_2017, "Data_MET2017.json"),
            (s.met_2018, "Data_production_20240326.json"),
        ],
        "module": "SoftDisplacedVertices.ML.ParTScore_K_run2",
        "jobsfile": "jobsrun2{}.sh",
    },
    "2022_2023": {
        "samples": [
            (s.znunu_2022Pre+s.wlnu_2022Pre+s.qcd_2022Pre+s.top_2022Pre
             + s.znunu_2022Post+s.wlnu_2022Post+s.qcd_2022Post+s.top_2022Post, "MC_Run3Summer22_20250621.json"),
            (s.znunu_2023Pre+s.wlnu_2023Pre+s.qcd_2023Pre+s.top_2023Pre
             + s.znunu_2023Post+s.wlnu_2023Post+s.qcd_2023Post+s.top_2023Post, "MC_Run3Summer23_20250409.json"),
        ],
        "data_samples": [
            (s.met_2022Pre+s.met_2022Post+s.met_2023Pre+s.met_2023Post, "Data_Run3_jetmet_official.json"),
        ],
        "module": "SoftDisplacedVertices.ML.ParTScore_K_run3",
        "jobsfile": "jobsrun3{}.sh",
    },
    "2024": {
        "samples": [
            (s.znunu_2024+s.wlnu_2024+s.qcd_2024+s.top_2024, "MC_Run3Summer24_20260330.json"),
        ],
        "data_samples": [
            (s.met_2024, "Data_Run3_jetmet_official.json"),
        ],
        "module": "SoftDisplacedVertices.ML.ParTScore_K_2024",
        "jobsfile": "jobs2024{}.sh",
    },
}

cfg = era_config[args.era]
sample_key = "data_samples" if args.data else "samples"
jbfn = cfg["jobsfile"].replace("{}", "data{}") if args.data else cfg["jobsfile"]

input_samples = []
for samples, jsonfn in cfg[sample_key]:
    s.loadData(samples, os.path.join(jsondir, jsonfn), input_label)
    input_samples += samples

def fileSize(fn):
  """size in bytes; xrootd URLs from DAS are mapped to the local EOS mount"""
  if fn.startswith(eos_redirector):
    fn = "/eos/vbc/experiments/cms/" + fn[len(eos_redirector):].lstrip('/')
  return os.path.getsize(fn)

def groupFiles(fns, max_bytes):
  """consecutive groups of files with total size <= max_bytes; a larger file gets its own group"""
  groups = []
  current, current_bytes = [], 0
  for fn in fns:
    size = fileSize(fn)
    if current and current_bytes + size > max_bytes:
      groups.append(current)
      current, current_bytes = [], 0
    current.append(fn)
    current_bytes += size
  if current:
    groups.append(current)
  return groups

jobf = open("jobs.sh","w")
njobs = 0

for sp in input_samples:
  targetDir = "/scratch-cbe/users/ang.li/SoftDV/NanoAOD_{0}/{1}/".format(version,sp.name)
  os.makedirs(targetDir)
  eosDir = os.path.join(eos_basedir, sp.name)
  input_fns = sp.getFileList(input_label,"")
  groups = groupFiles(input_fns, max_input_bytes_per_job)
  print(sp.name, len(input_fns), "files ->", len(groups), "jobs")
  i = 0
  for group in groups:
    # one working dir per job, so jobs of the same sample on the same node don't collide
    uuid_ =  str(uuid.uuid4())
    command = "set -e;export X509_USER_PROXY=%s;" % (proxy)
    command += "mkdir /tmp/%s;" % (uuid_)
    command += "cd /tmp/%s;" %(uuid_)
    for fn in group:
      # each input file keeps its own output_<i>.root
      command += "nano_postproc.py out_%i %s -I %s ParTScoreModuleConstr;" % (i, fn, cfg["module"])
      command += "cp /tmp/%s/out_%i/*.root %s/output_%i.root;" %(uuid_,i,targetDir,i)
      command += "xrdcp -f -p /tmp/%s/out_%i/*.root %s%s/output_%i.root;" %(uuid_,i,eos_redirector,eosDir,i)
      command += "rm -rf /tmp/%s/out_%i;" %(uuid_,i)
      i += 1
    command += "cd /tmp;rm -rf /tmp/%s;" %(uuid_)
    command += '\n'
    jobf.write(command)
    njobs += 1

jobf.close()
print("total jobs:", njobs)
inputdir = "/scratch-cbe/users/ang.li/SoftDV/NanoAOD_{0}/{1}/".format(version,'input')
if not os.path.exists(inputdir):
    os.makedirs(inputdir)
ij = ''
if os.path.exists(os.path.join(inputdir,jbfn.format(ij))):
  ij=1
  while os.path.exists(os.path.join(inputdir,jbfn.format(ij))):
    ij += 1
shutil.copy2('jobs.sh',os.path.join(inputdir,jbfn.format(ij)))
