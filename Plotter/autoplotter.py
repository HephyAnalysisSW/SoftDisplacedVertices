# Example usage:
# python3 autoplotter.py --sample stop_M600_580_ct2_2018 --output ./ --config /users/ang.li/public/SoftDV/CMSSW_13_3_0/src/SoftDisplacedVertices/Plotter/plotconfig_sig.yaml --lumi 59683. --json MLNanoAOD.json --metadata metadata_CustomMiniAOD_v3.yaml --datalabel MLNanoAODv2

import os
import math
import uuid
import shutil
import SoftDisplacedVertices.Plotter.plotter as p
import SoftDisplacedVertices.Plotter.plot_setting as ps
import SoftDisplacedVertices.Samples.Samples as s

import argparse

def partition(lst, n):
    ''' Partition list into chunks of approximately equal size'''
    # http://stackoverflow.com/questions/2659900/python-slicing-a-list-into-n-nearly-equal-length-partitions
    n_division = len(lst) / float(n)
    return [ lst[int(round(n_division * i)): int(round(n_division * (i + 1)))] for i in range(n) ]

parser = argparse.ArgumentParser()
parser.add_argument('--sample', type=str, nargs='+',
                        help='samples to process')
parser.add_argument('--output', type=str,
                        help='output dir')
parser.add_argument('--config', type=str,
                        help='config to use') 
parser.add_argument('--lumi', type=float, default=59683.,
                        help='luminosity to normalise MC samples')
parser.add_argument('--json', type=str, 
                        help='json for file paths') 
parser.add_argument('--metadata', type=str,default='',
                        help='metadata for sum gen weights of MC samples') 
parser.add_argument('--datalabel', type=str,
                        help='datalabel to use in json file') 
parser.add_argument('--filelist', type=str,default='',
                        help='path of the txt file that include the list of files to run') 
parser.add_argument('--postfix', type=str,default='',
                        help='postfix of the output file') 
parser.add_argument('--year', type=str,
                        help='Which year does the data correspond to') 
parser.add_argument('--data', action='store_true', default=False,
                        help='Whether the input is data') 
parser.add_argument('--submit', action='store_true', default=False,
                        help='Whether to scale the plot')
parser.add_argument('--njobs', type=int, default=1,
                        help='The number of jobs to submit for each sample. Could be a list of a single value.')
parser.add_argument('--nfiles', type=int, default=-1,
                        help='The number of files per job to submit for each sample. Could be a list of a single value.')
args = parser.parse_args()


if __name__=="__main__":

  all_samples = []
  for samp in args.sample:
    s_samp = getattr(s,samp)
    if isinstance(s_samp, list): 
      all_samples += s_samp
    else:
      all_samples.append(s_samp)

  print("Using config {}".format(args.config))

  if args.submit:
    s.loadData(all_samples,os.path.join(os.environ['CMSSW_BASE'],'src/SoftDisplacedVertices/Samples/json/{}'.format(args.json)),args.datalabel)
    inputdir = args.output+'/input'
    if os.path.exists(args.output):
      print("WARNING! {} already exists! Continuing...".format(args.output))
    else:
      os.makedirs(args.output)
    if os.path.exists(os.path.join(args.output,'input')):
      print("WARNING! Input dir already exists! Continuing...".format(args.output))
    else:
      os.makedirs(inputdir)
    if os.path.exists(os.path.join(inputdir,os.path.basename(args.config))):
      print("WARNING! Config {} already exists! Reusing for plotting...".format(os.path.basename(args.config)))
    else:
      shutil.copy2(args.config,inputdir)
    if os.path.exists(os.path.join(inputdir,'autoplotter.py')):
      print("WARNING! File autoplotter.py already exists! Reusing for plotting...")
    else:
      shutil.copy2(os.path.join(os.getcwd(),'autoplotter.py'),inputdir)

    jobf = open('jobs.sh',"w")
    if args.data:
      data = '--data'
    else:
      data=''
    for samp in all_samples:
      outputdir_sample = os.path.join(args.output,samp.name)
      if os.path.exists(outputdir_sample):
        print("Path {} already exists! Skipping...".format(outputdir_sample))
        continue
      inputdir_sample = outputdir_sample+'/input'
      os.makedirs(inputdir_sample)
      files = samp.getFileList(args.datalabel,"")
      njobs = min(args.njobs, len(files))
      if args.nfiles>0:
        njobs = int(math.ceil(len(files)/float(args.nfiles)))
      chunks = partition( files, min(njobs , len(files) ) ) 
      print("Got %i files and n_split into %i jobs of %3.2f files/job on average." % ( len(files), len(chunks), len(files)/float(len(chunks))))
      for ic in range(len(chunks)):
        with open("{}_fn{}.txt".format(samp.name,ic),"w") as fns:
          fns.write("\n".join(chunks[ic]))
        shutil.copy2("{}_fn{}.txt".format(samp.name,ic),inputdir_sample)
        os.remove("{}_fn{}.txt".format(samp.name,ic))

      for ij in range(len(chunks)):
        flname = "{}_fn{}.txt".format(samp.name,ij)
        uuid_ =  str(uuid.uuid4())
        command = "set -e;mkdir /tmp/%s;" % (uuid_)
        command += "cd /tmp/%s;" %(uuid_)
        if 'eos' in inputdir:
          command += "xrdcp -r root://eos.grid.vbc.ac.at/%s /tmp/%s/.;" %(inputdir,uuid_)
          command += "cp /tmp/%s/input/* /tmp/%s/.;" %(uuid_,uuid_)
          command += "xrdcp -r root://eos.grid.vbc.ac.at/%s /tmp/%s/input/.;" %(inputdir_sample,uuid_)
          command += "cp /tmp/%s/input/input/* /tmp/%s/.;" %(uuid_,uuid_)
        else:
          command += "cp %s /tmp/%s/.;" %(inputdir+'/*',uuid_)
          command += "cp %s /tmp/%s/.;" %(inputdir_sample+'/*',uuid_)
        #command += "cp %s /tmp/%s/.;" %(os.path.join(os.environ['CMSSW_BASE'],'src/SoftDisplacedVertices/Plotter/autoplotter.py'),uuid_)
        #command += "python3 autoplotter.py --sample {} --output ./ --config {};".format(samp.name,args.config)
        if args.metadata=='':
          command += "python3 autoplotter.py --sample {} --output ./ --config ./{} --lumi {} --json {} --datalabel {} --filelist ./{} --year {} --postfix _{} {};".format(samp.name,os.path.basename(args.config),args.lumi,args.json,args.datalabel,flname,args.year,ij,data)
        else:
          command += "python3 autoplotter.py --sample {} --output ./ --config ./{} --lumi {} --json {} --metadata {} --datalabel {} {} {};".format(samp.name,os.path.basename(args.config),args.lumi,args.json,args.metadata,args.datalabel, args.year, data)
        if 'eos' in outputdir_sample:
          fname = "{}_hist_{}".format(samp.name,ij)
          command += "eoscp ./{0}.root {1}/{0}.root;".format(fname,outputdir_sample)
          command += "eoscp ./{0}.pkl {1}/{0}.pkl;".format(fname,outputdir_sample)
        else:
          command += "cp ./*.root {}/.;".format(outputdir_sample)
          command += "cp ./*.pkl {}/.;".format(outputdir_sample)
        command += "\n"
        jobf.write(command)
    jobf.close()
    jbfn = 'jobs{}.sh'
    ij = ''
    if os.path.exists(os.path.join(inputdir,jbfn.format(ij))):
      ij=1
      while os.path.exists(os.path.join(inputdir,jbfn.format(ij))):
        ij += 1
    shutil.copy2('jobs.sh',os.path.join(inputdir,jbfn.format(ij)))

  else:
    lumi = args.lumi # units in pb-1
    #label = "MLNanoAODv2"
    #input_json = "MLNanoAOD.json"
    #info = "metadata_CustomMiniAOD_v3.yaml"
    s.loadData(all_samples,os.path.join(os.environ['CMSSW_BASE'],'src/SoftDisplacedVertices/Samples/json/{}'.format(args.json)),args.datalabel)
    info_path = os.path.join(os.environ['CMSSW_BASE'],'src/SoftDisplacedVertices/Samples/json/{}'.format(args.metadata))

    plotter = p.Plotter(datalabel=args.datalabel,outputDir=args.output,lumi=lumi,info_path=info_path,input_filelist=args.filelist,config=args.config,year=args.year,isData=args.data,postfix=args.postfix)

    for sample in all_samples:
      plotter.setSample(sample)
      plotter.makeHistFiles()
