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
#import logger

class cmsRunJob:
  def __init__(self,title="job",logLevel = "INFO", input = None, instance = "global", redirector = "root://cms-xrd-global.cern.ch/", targetDir = None, cfg = None, limit = 0, n_split = None, n_files = 0):
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

  def setJob(self,title="job",input = None, instance = "global", redirector = "root://cms-xrd-global.cern.ch/", targetDir = None, limit = 0, n_split = None, n_files = 0):
    #dbs:<DAS name>, local directory, or file with filenames
    self.input = input
    #DAS instance.
    self.instance = instance
    #redirector for xrootd
    self.redirector = redirector
    #output director
    self.targetDir = targetDir
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

  def isValid(self):
    if self.input is None or self.targetDir is None or self.cfg is None:
      return False
    if self.module is None:
      return False
    return True

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
            return [ lst[int(round(n_division * i)): int(round(n_division * (i + 1)))] for i in xrange(n) ]
    
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
    if not os.path.exists( targetDir ):
        os.makedirs( targetDir )
        self.logger.debug( 'Created job directory %s', targetDir )

    targetDir_out = os.path.join(targetDir, 'output')
    self.info["output"] = targetDir_out
    if not os.path.exists( targetDir_out ):
        os.makedirs( targetDir_out )
        self.logger.debug( 'Created output directory %s', targetDir_out )
    
    targetDir_fs = os.path.join( self.targetDir, subDirName, 'fs')
    if not os.path.exists( targetDir_fs ):
        os.makedirs( targetDir_fs )
        self.logger.debug( 'Created TFileService output directory %s', targetDir_fs )
    
    user          = os.getenv("USER")
    #batch_tmp     = "/scratch/%s/batch_input/"%(user)
    batch_tmp     = os.path.join(self.info["jobdir"],"input")
    
    if not os.path.exists( batch_tmp):
        os.makedirs( batch_tmp )
        self.logger.debug( 'Created directory %s', batch_tmp)
    
    # write the configs
    import FWCore.ParameterSet.Config as cms
    import uuid
    if os.path.exists(self.jobname):
      self.logger.warning("{} already exists, will remove the previous one...".format(self.jobname))
      os.remove(self.jobname)
    with file(self.jobname, 'a+') as job_file:
        for i_chunk, chunk in enumerate(chunks):
            # set input if not GEN
            if files is not None:
                self.module.process.source.fileNames = cms.untracked.vstring(map(lambda filename: self.redirector+filename, chunk))
            uuid_ =  str(uuid.uuid4())
            run_dir = '/tmp/%s/'%uuid_
            if not os.path.exists( run_dir ):
                os.makedirs( run_dir )
            move_cmds = []
            # set output
            for out_name, output_module in self.module.process.outputModules.iteritems():
                output_filename     = 'out_%s_%i.root'%(out_name, i_chunk)
                output_tmp_filename = 'out_%s_%i_%s.root'%(out_name, i_chunk, uuid_ )
                output_module.fileName  = cms.untracked.string(os.path.join(run_dir, output_tmp_filename))
                move_cmds.append( (os.path.join(run_dir, output_tmp_filename), os.path.join(targetDir_out, output_filename)) )
            # set output from TFileService
            if hasattr( self.module.process, "TFileService" ):
                output_filename_fs   = 'fs_%i.root'%(i_chunk)
                output_tmp_filename_fs = 'fs_%i_%s.root'%(i_chunk, uuid_ )
                self.module.process.TFileService.fileName = cms.string(os.path.join(run_dir, output_tmp_filename_fs))
                move_cmds.append( (os.path.join(run_dir, output_tmp_filename_fs), os.path.join(targetDir_fs, output_filename_fs)) )
    
            # set maxEvents to -1 if not GEN
            if files is not None:
                if hasattr( self.module.process, "maxEvents" ):
                    self.module.process.maxEvents.input = cms.untracked.int32(-1)
            # dump cfg
            out_cfg_name = os.path.join( batch_tmp, str(uuid.uuid4()).replace('-','_')+'.py' )
            with file(out_cfg_name, 'w') as out_cfg:
                out_cfg.write(self.module.process.dumpPython())
            self.logger.debug("Written %s", out_cfg_name)
    
            move_string =  ";" if len(move_cmds)>0 else ""
            move_string += ";".join(["mv %s %s"%move_cmd for move_cmd in move_cmds])
            job_file.write('mkdir -p %s; cd %s;cmsRun %s'%( run_dir, run_dir, out_cfg_name + move_string + '\n'))

  def submit(self, dryrun=False):
    assert os.path.exists(self.jobname)
    self.logger.info("Submitting jobs")
    logdir = os.path.join(self.info["jobdir"],"log")
    if not os.path.exists( logdir):
        os.makedirs( logdir)
    if not dryrun:
      p = subprocess.Popen(args="submit {0} --output={1} --title={2} --logLevel={3} --nCPUs=4".format(self.jobname,logdir,self.info["title"],self.logLevel),stdout = subprocess.PIPE,stderr = subprocess.STDOUT, shell=True)
      self.logger.debug(p.stdout.read())
    self.logger.info("Archiving {}".format(self.jobname))
    shutil.move(self.jobname,os.path.join(self.info["jobdir"],"input",self.jobname))
    with open(os.path.join(logdir,"jobinfo.json"),"w") as f:
      json.dump(self.info,f,indent=2)

