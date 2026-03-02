#!/usr/bin/env python

import os
import json
import shutil
import argparse
import SoftDisplacedVertices.Samples.Samples as s
import SoftDisplacedVertices.Samples.cmsRunJobs as job

parser = argparse.ArgumentParser()
parser.add_argument('--sample', type=str, nargs='+',
                        help='samples to process')
parser.add_argument('--output', type=str,
                        help='output dir')
parser.add_argument('--config', type=str,
                        help='config to use') 
parser.add_argument('--json', type=str, 
                        help='json for file paths') 
parser.add_argument('--datalabel', type=str,
                        help='datalabel to use in json file') 
parser.add_argument('--redirector', type=str, default='root://eos.grid.vbc.ac.at/',
                        help='redirector to use for the input files.') 
parser.add_argument('--dryrun', action='store_true', default=False,
                        help='Whether to perform a dryrun') 
parser.add_argument('--nfiles', type=int, default=-1,
                        help='The number of files per job to submit for each sample.')
args = parser.parse_args()

input_label = args.datalabel

if __name__=="__main__":

    input_samples = []
    for samp in args.sample:
        s_samp = getattr(s,samp)
        if isinstance(s_samp, list): 
            input_samples += s_samp
        else:
            input_samples.append(s_samp)

    j = job.cmsRunJob(cfg=args.config,logLevel = "INFO")
    
    s.loadData(input_samples,os.path.join(os.environ['CMSSW_BASE'],'src/SoftDisplacedVertices/Samples/json/{}'.format(args.json)),input_label)
    
    sub_cmd = []
    for sp in input_samples:
        targetDir = os.path.join(args.output,sp.name)
        
        assert not os.path.exists(targetDir), "Path {} already exists!".format(targetDir)
        useDBS = False
        if input_label in sp.dataset:
            useDBS = True
        if useDBS:
            assert "root:" in args.redirector, "Please use the redirector for files from eos!"
            input = 'dbs:'+sp.dataset[input_label]
            j.setJob(title=sp.name+input_label,input=input,instance=sp.dataset_instance[input_label],targetDir=targetDir,redirector = args.redirector,n_files=args.nfiles)
            
            j.prepare()
            c = j.submit(dryrun=args.dryrun)
            j.reset()
            sub_cmd.append(c)
        else:
          with open("filename.txt","w") as fns:
            fns.write("\n".join(sp.getFileList(input_label,"")))
        
            j.setJob(title=sp.name+input_label, input="filename.txt",targetDir=targetDir,redirector = args.redirector,n_files=args.nfiles)

          j.prepare()
          c = j.submit(dryrun=args.dryrun)
          shutil.move("filename.txt",os.path.join(targetDir+'/input',"filename.txt"))
          j.reset()
          sub_cmd.append(c)

    with open('jobs.sh','w') as f:
        for i in sub_cmd:
            f.write(i+';\n')
