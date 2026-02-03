#!/usr/bin/env python

#Standard imports
import math

# general imports
import os
import sys
import shutil
import argparse
import subprocess
import json
import logger
import shutil
#import logger

from XRootD import client
from XRootD.client.flags import MkDirFlags

class cmsRunJob:
  def __init__(self,title="job",logLevel = "INFO", input = None, instance = "global", redirector = "root://cms-xrd-global.cern.ch/", targetDir = None, target_redirector = None, cfg = None, limit = 0, n_split = None, n_files = 0):
    #Log level for logging
    self.logLevel = logLevel
    #dbs:<DAS name>, local directory, or file with filenames
    self.input = input
    #DAS instance.
    self.instance = instance
    #redirector for xrootd
    self.redirector = redirector
    #output director
    self.targetDir = targetDir
    #target directory redirector (if on eos)
    self.eosfs = None
    self.target_redirector = target_redirector
    if target_redirector is not None:
        self.eosfs = client.FileSystem(target_redirector)
    #Which config.
    self.cfg = cfg
    #Limit DAS query?
    self.limit = limit
    #Number of jobs.
    self.n_split = n_split
    #Number of files per job.
    self.n_files = n_files
    self.logger = logger.get_logger( self.logLevel, logFile=None )
    self.info = {
        "title":title,
        "input":self.input,
        "outname":"out",
        }
    self.jobname = "job_{}.sh".format(title)

    self.module = None

    # Deal with the config
    self.logger.info("Config: %s", self.cfg)
    import imp
    if os.path.exists( self.cfg ):
        self.module = imp.load_source('process_tmp', os.path.expandvars(self.cfg))
        self.logger.info( "Loaded config" )
    else:
        self.logger.error( "Did not find cfg %s", self.cfg )
        sys.exit(-1)

  def reset(self):
    #dbs:<DAS name>, local directory, or file with filenames
    self.input = None
    #DAS instance.
    self.instance = "global"
    #redirector for xrootd
    self.redirector = "root://cms-xrd-global.cern.ch/"
    #output director
    self.targetDir = None
    #target directory redirector (if on eos)
    self.target_redirector = None
    self.eosfs = None
    #Limit DAS query?
    self.limit = 0
    #Number of jobs.
    self.n_split = None
    #Number of files per job.
    self.n_files = 0
    self.info = {
        "title":"job",
        "input":self.input,
        "outname":"out",
        }
    self.jobname = "job.sh"

  def setJob(self,title="job",input = None, instance = "global", redirector = "root://cms-xrd-global.cern.ch/", targetDir = None, target_redirector = None, limit = 0, n_split = None, n_files = 0):
    #dbs:<DAS name>, local directory, or file with filenames
    self.input = input
    #DAS instance.
    self.instance = instance
    #redirector for xrootd
    self.redirector = redirector
    #output director
    self.targetDir = targetDir
    #target directory redirector (if on eos)
    self.eosfs = None
    self.target_redirector = target_redirector
    if target_redirector is not None:
        self.eosfs = client.FileSystem(target_redirector)
    #Limit DAS query?
    self.limit = limit
    #Number of jobs.
    self.n_split = n_split
    #Number of files per job.
    self.n_files = n_files
    self.info = {
        "title":title,
        "input":self.input,
        "outname":"out",
        }
    self.jobname = "job_{}.sh".format(title)
    user          = os.getenv("USER")
    self.batch_tmp     = "/scratch-cbe/users/%s/SoftDV/jobs/%s/input"%(user,self.jobname.replace(".sh",''))

  def isValid(self):
    if self.input is None or self.targetDir is None or self.cfg is None:
      return False
    if self.module is None:
      return False
    return True

  def createDir(self, newdir, redirector=None):
    if redirector is not None:
        # check dir exists on eos
        status, _ = self.eosfs.stat(newdir)
        if not status.ok:
            status, _ = self.eosfs.mkdir(newdir, flags=MkDirFlags.MAKEPATH)
        if status.ok:
            self.logger.debug( 'Created job directory %s', newdir )
        else:
            self.logger.error( 'Failed to create directory %s', newdir )
    elif not os.path.exists( newdir ):
        os.makedirs( newdir )
        self.logger.debug( 'Created job directory %s', newdir )

  def prepare(self):
    assert self.isValid()
    # Deal with the sample
    files = []
    # get from dbs
    subDirName = ''
    if self.input.startswith('dbs:'):
        DASName = self.input[4:] 
        # name for the subdirectory FIXME: I think this is not necessary so comment out...
        #subDirName = DASName.lstrip('/').replace('/','_')
        def _dasPopen(dbs):
            self.logger.info('DAS query\t: %s',  dbs)
            return os.popen(dbs)
    
        query, qwhat = DASName, "dataset"
        if "#" in DASName: qwhat = "block"
    
        self.logger.info("Sample: %s", DASName)
    
        dbs='dasgoclient -query="file %s=%s instance=prod/%s" --limit %i'%(qwhat,query, self.instance, self.limit)
        dbsOut = _dasPopen(dbs).readlines()
    
        for line in dbsOut:
            if line.startswith('/store/'):
                files.append(line.rstrip())
    elif os.path.exists( self.input ) and os.path.isfile( self.input ):
        with open( self.input, 'r') as inputfile:
            for line in inputfile.readlines():
                line = line.rstrip('\n').rstrip()
                if line.endswith('.root'):
                    files.append(line)
    #get from directory
    elif os.path.exists( self.input ) and os.path.isdir( self.input ):
        for filename in os.listdir( self.input ):
            if filename.endswith('.root'):
                files.append(os.path.join( self.input, filename ))
    elif self.input.lower() == 'gen':
        files = None
    
    if files is not None:
        if len(files)==0:
            raise RuntimeError('Found zero files for input %s'%self.input)
        
        def partition(lst, n):
            ''' Partition list into chunks of approximately equal size'''
            # http://stackoverflow.com/questions/2659900/python-slicing-a-list-into-n-nearly-equal-length-partitions
            n_division = len(lst) / float(n)
            return [ lst[int(round(n_division * i)): int(round(n_division * (i + 1)))] for i in range(n) ]
    
        # 1 job / file as default
        if self.n_split is None:
            self.n_split=len(files)
        if self.n_files>0:
            self.n_split = int(math.ceil(len(files)/float(self.n_files)))
        chunks = partition( files, min(self.n_split , len(files) ) ) 
        self.logger.info( "Got %i files and n_split into %i jobs of %3.2f files/job on average." % ( len(files), len(chunks), len(files)/float(len(chunks))) )
        for chunk in chunks:
            pass
    else:
        chunks = range(self.n_files)
    self.info["njobs"] = len(chunks)
    
    targetDir = os.path.join( self.targetDir, subDirName )
    self.info["jobdir"] = targetDir
    self.createDir(targetDir,self.target_redirector)

    targetDir_out = os.path.join(targetDir, 'output')
    self.info["output"] = targetDir_out
    self.createDir(targetDir_out,self.target_redirector)
    
    targetDir_fs = os.path.join( self.targetDir, subDirName, 'fs')
    self.createDir(targetDir_fs,self.target_redirector)
    
    targetDir_in  = os.path.join(self.info["jobdir"],"input")

    if os.path.exists(self.batch_tmp):
        print("Tmp path {} exists, removing...".format(self.batch_tmp))
        shutil.rmtree(self.batch_tmp)
    
    self.createDir(self.batch_tmp)
    self.createDir(targetDir_in,self.target_redirector)
    
    # write the configs
    import FWCore.ParameterSet.Config as cms

    files_tomove = []
    # set output
    for out_name, output_module in self.module.process.outputModules.items():
        files_tomove.append(output_module.fileName.value())
    # set output from TFileService
    if hasattr( self.module.process, "TFileService" ):
        files_tomove.append(self.module.process.TFileService.fileName.value())
    
    # set maxEvents to -1 if not GEN
    if files is not None:
        if hasattr( self.module.process, "maxEvents" ):
            assert(self.module.process.maxEvents.input==-1), "maxEvent not -1!"
    # dump cfg
    out_cfg_name_local = 'job_cfg.py'
    out_cfg_name_tmp = os.path.join( self.batch_tmp, out_cfg_name_local )
    out_cfg_name = os.path.join( targetDir_in, out_cfg_name_local )
    #shutil.copy(self.cfg,out_cfg_name_tmp)
    if self.eosfs is None:
        shutil.copy(self.cfg,out_cfg_name)
    else:
        cmd = f'xrdcp {self.cfg} {self.target_redirector}{out_cfg_name}'
        proc = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        assert proc.returncode==0, f"{cmd} failed."
    self.logger.debug("Config copied %s", out_cfg_name)

    import uuid
    if os.path.exists(self.jobname):
      self.logger.warning("{} already exists, will remove the previous one...".format(self.jobname))
      os.remove(self.jobname)
    with open(self.jobname, 'a+') as job_file:
        for i_chunk, chunk in enumerate(chunks):
            uuid_ =  str(uuid.uuid4())
            run_dir = '/tmp/%s/'%uuid_
            if not os.path.exists( run_dir ):
                os.makedirs( run_dir )

            if self.eosfs is None:
                input_cmds = "cp {} {};".format(out_cfg_name,os.path.join(run_dir,out_cfg_name_local))
            else:
                input_cmds = "xrdcp {}/{} {};".format(self.target_redirector,out_cfg_name,os.path.join(run_dir,out_cfg_name_local))
            if files is not None:
                intputfn_local = "input_list.txt"
                intputfn_tmp = os.path.join(self.batch_tmp,"input_list_%i.txt"%(i_chunk))
                intputfn = os.path.join(targetDir_in,"input_list_%i.txt"%(i_chunk))
                with open(intputfn_tmp,"w") as f_inputlist:
                    for ic in chunk:
                        f_inputlist.write(self.redirector+ic+"\n")

                input_cmds += "cp {} {};".format(intputfn_tmp,os.path.join(run_dir,intputfn_local))
                #if self.eosfs is None:
                #    #shutil.copy(intputfn_tmp,intputfn)
                #    input_cmds += "cp {} {};".format(intputfn,os.path.join(run_dir,intputfn_local))
                #else:
                #    #cmd = f'xrdcp {intputfn_tmp} {self.target_redirector}{intputfn}'
                #    #proc = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                #    #assert proc.returncode==0, f"{cmd} failed."
                #    input_cmds += "xrdcp {}/{} {};".format(self.target_redirector,intputfn,os.path.join(run_dir,intputfn_local))

            move_cmds = []
            for ifile in files_tomove:
                move_cmds.append( (ifile,os.path.join(targetDir_out, ifile.replace('.root','_%i.root'%(i_chunk)))) )
    
            move_string =  ";" if len(move_cmds)>0 else ""
            if self.eosfs is None:
                move_string += ";".join(["mv %s %s"%move_cmd for move_cmd in move_cmds])
                move_string += ";cp {} {};".format(intputfn_local,intputfn)
            else:
                move_string += ";".join([f"xrdcp {move_cmd[0]} {self.target_redirector}/{move_cmd[1]}" for move_cmd in move_cmds])
                move_string += ";xrdcp {} {}/{};".format(intputfn_local,self.target_redirector,intputfn)
            job_file.write('set -e;mkdir -p %s; cd %s;%s cmsRun %s'%( run_dir, run_dir, input_cmds, out_cfg_name_local + move_string + '\n'))

  def submit(self, dryrun=False):
    assert os.path.exists(self.jobname)
    self.logger.info("Submitting jobs")
    logdir = os.path.join(self.info["jobdir"],"log")
    self.createDir(logdir,self.target_redirector)
    if not dryrun:
      p = subprocess.Popen(args="/groups/hephy/cms/ang.li/Tools/scripts/submit_el8 {0} --output={1} --title={2} --logLevel={3}".format(self.jobname,logdir,self.info["title"],self.logLevel),stdout = subprocess.PIPE,stderr = subprocess.STDOUT, shell=True)
      self.logger.debug(p.stdout.read())
    self.logger.info("Archiving {}".format(self.jobname))

    if self.eosfs is None:
        shutil.copy(self.jobname,os.path.join(self.info["jobdir"],"input",self.jobname))
    else:
        cmd = f'xrdcp {self.jobname} {self.target_redirector}/{os.path.join(self.info["jobdir"],"input",self.jobname)}'
        proc = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        assert proc.returncode==0, f"{cmd} failed."
    self.logger.debug("Job file moved %s", os.path.join(self.info["jobdir"],"input",self.jobname))

    with open(os.path.join(self.batch_tmp,"jobinfo.json"),"w") as f:
      json.dump(self.info,f,indent=2)
    if self.eosfs is None:
        shutil.copy(os.path.join(self.batch_tmp,"jobinfo.json"),os.path.join(logdir,"jobinfo.json"))
    else:
        cmd = f'xrdcp {os.path.join(self.batch_tmp,"jobinfo.json")} {self.target_redirector}/{os.path.join(logdir,"jobinfo.json")}'
        proc = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        assert proc.returncode==0, f"{cmd} failed."
    self.logger.debug("Json file moved %s", os.path.join(logdir,"jobinfo.json"))
    return "/groups/hephy/cms/ang.li/Tools/scripts/submit_el8 {0} --output={1} --title={2} --logLevel={3}".format(self.jobname,logdir,self.info["title"],self.logLevel)

