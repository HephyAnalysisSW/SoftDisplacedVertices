#!/usr/bin/env python

import os
import uuid
import shutil
import argparse
import SoftDisplacedVertices.Samples.Samples as s

parser = argparse.ArgumentParser(description="Prepare ParTScore_D (D meson rotation study) nano_postproc jobs for slurm submission")
parser.add_argument("--era", required=True, choices=["run2", "2022_2023", "2024"])
parser.add_argument("--data", action="store_true", help="prepare JetMET data jobs instead of MC")
args = parser.parse_args()

input_label = "CustomNanoAOD"
version = "ParTScore_D"
eos_redirector = "root://eos.grid.vbc.ac.at/"
eos_basedir = "/eos/vbc/experiments/cms/store/user/lian/NanoAOD_{0}/".format(version)
proxy = "/users/ang.li/private/.proxy"
# MC input files of one sample are grouped into jobs of at most max_bytes total size and max_files files
# (era_config can override both); data runs one file per job (data takes much longer per byte than MC)
mc_grouping = {"max_bytes": 3e9, "max_files": None}
jsondir = os.path.join(os.environ['CMSSW_BASE'], 'src/SoftDisplacedVertices/Samples/json')
# inputs are the ParTScore_K outputs, which carry SDVSecVtx_ParTScore
input_json = {
    "MC": "scratch_MC_ParTScore_K.json",
    "data": "scratch_data_ParTScore_K.json",
}

# era -> MC and data samples, postproc module, name of the jobs file copied to the input dir
era_config = {
    "run2": {
        "samples": s.znunu_2017+s.wlnu_2017+s.qcd_2017+s.top_2017
                 + s.znunu_2018+s.wlnu_2018+s.qcd_2018+s.top_2018,
        "data_samples": s.met_2017+s.met_2018,
        "module": "SoftDisplacedVertices.ML.ParTScore_D_run2",
        "jobsfile": "jobsrun2{}.sh",
    },
    "2022_2023": {
        "samples": s.znunu_2022Pre+s.wlnu_2022Pre+s.qcd_2022Pre+s.top_2022Pre
                 + s.znunu_2022Post+s.wlnu_2022Post+s.qcd_2022Post+s.top_2022Post
                 + s.znunu_2023Pre+s.wlnu_2023Pre+s.qcd_2023Pre+s.top_2023Pre
                 + s.znunu_2023Post+s.wlnu_2023Post+s.qcd_2023Post+s.top_2023Post,
        "data_samples": s.met_2022Pre+s.met_2022Post+s.met_2023Pre+s.met_2023Post,
        "module": "SoftDisplacedVertices.ML.ParTScore_D_run3",
        "jobsfile": "jobsrun3{}.sh",
    },
    "2024": {
        "samples": s.znunu_2024+s.wlnu_2024+s.qcd_2024+s.top_2024,
        "data_samples": s.met_2024,
        "module": "SoftDisplacedVertices.ML.ParTScore_D_2024",
        "jobsfile": "jobs2024{}.sh",
        # many small files: smaller groups, and fewer files per job to limit the per-file startup
        "mc_grouping": {"max_bytes": 2e9, "max_files": 50},
    },
}

cfg = era_config[args.era]
sample_key = "data_samples" if args.data else "samples"
jbfn = cfg["jobsfile"].replace("{}", "data{}") if args.data else cfg["jobsfile"]

input_samples = cfg[sample_key]
s.loadData(input_samples, os.path.join(jsondir, input_json["data" if args.data else "MC"]), input_label)

def groupFiles(fns, max_bytes, max_files=None):
  """consecutive groups of files with total size <= max_bytes and at most max_files files; a larger file gets its own group"""
  groups = []
  current, current_bytes = [], 0
  for fn in fns:
    size = os.path.getsize(fn)
    if current and (current_bytes + size > max_bytes or (max_files and len(current) >= max_files)):
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
  if args.data:
    groups = [[fn] for fn in input_fns]
  else:
    grouping = cfg.get("mc_grouping", mc_grouping)
    groups = groupFiles(input_fns, grouping["max_bytes"], grouping["max_files"])
  print(sp.name, len(input_fns), "files ->", len(groups), "jobs")
  for group in groups:
    # one working dir per job, so jobs of the same sample on the same node don't collide
    uuid_ =  str(uuid.uuid4())
    command = "set -e;export X509_USER_PROXY=%s;" % (proxy)
    command += "mkdir /tmp/%s;" % (uuid_)
    command += "cd /tmp/%s;" %(uuid_)
    for fn in group:
      # output_<i>.root keeps the index of the input output_<i>.root
      i = int(os.path.basename(fn)[len("output_"):-len(".root")])
      command += "nano_postproc.py out_%i %s -I %s ParTScoreModuleConstr;" % (i, fn, cfg["module"])
      command += "cp /tmp/%s/out_%i/*.root %s/output_%i.root;" %(uuid_,i,targetDir,i)
      command += "xrdcp -f -p /tmp/%s/out_%i/*.root %s%s/output_%i.root;" %(uuid_,i,eos_redirector,eosDir,i)
      command += "rm -rf /tmp/%s/out_%i;" %(uuid_,i)
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
