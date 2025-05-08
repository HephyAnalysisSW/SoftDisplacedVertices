#!/usr/bin/env python2


""" 
    Usage:
    submit --OPTIONS "FILE"  :  Will submit a batch job for each command line in FILE.
    If the commandline ends with #SPLIT2, where 2 can be any number, an array job will be executed with (2) jobs.
    Each jobs gets the additional command options --nJobs 2 --job 0 and --nJobs 2 --job 1
    
    submit --OPTIONS "COMMAND"  :  Will submit a batch job for the command.
    
    default runs with CMSSW, set --cmssw None for running w/o cmssw

    Log files by default are stored at /mnt/hephy/cms/USER/batch_output/
"""

# Standard imports
import os, time, re, sys
import shlex, uuid, time, datetime
import shutil

from clipHelpers import read_from_subprocess

# Defaults
home          = os.getenv("HOME")
user          = os.getenv("USER")
user_initial  = user[0]
cwd           = os.getcwd()
hostname      = os.getenv("HOSTNAME")
proxy         = os.getenv("X509_USER_PROXY")
submit_time   = time.strftime("%Y%m%d_%H%M%S", time.localtime())
inSingularity = os.path.exists("/.singularity.d/")
#batch_output  = "/scratch-cbe/users/%s/batch_output"%(user)
#batch_tmp     = "/scratch-cbe/users/%s/batch_input"%(user)
batch_output  = "/scratch/%s/batch_output"%(user)
batch_tmp     = "/scratch/%s/batch_input"%(user)

if not "clip" in hostname:
    raise Exception( "Running submit outside of clip is not supported!" )

if inSingularity:
    raise Exception( "Running submit inside of Singularity is not supported!" )

logChoices       = ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG', 'TRACE', 'NOTSET', 'SYNC']
queueChoices     = ["short", "medium", "long"] # long: 14 days, medium: 2 days, short: 8h
partitionChoices = ["c", "m", "g"] # c: regular node, m: high memory node, g: GPU node
# Parser
from optparse import OptionParser

parser = OptionParser()
parser.add_option('--logLevel',           dest="logLevel",           default="INFO",     choices=logChoices,       help="Log level for logging" )
parser.add_option('--status',             dest="status",                                 action='store_true',      help="Runs just squeue -u USER")
parser.add_option("--jobInfo",            dest="jobInfo",            default=None,       type=int,                 help="Print info to jobId" )
parser.add_option("--title",              dest="title",              default="batch",                              help="Job Title on batch" )
parser.add_option("--output",             dest="output",             default=batch_output,                         help="Logfile directory. Default is /mnt/hephy/cms/%s/batch_output/")
parser.add_option("--tmpDirectory",       dest="tmpDirectory",       default=batch_tmp,                            help="tmpfile directory. Default is /mnt/hephy/cms/%s/batch_input/")
parser.add_option('--dpm',                dest="dpm",                                    action='store_true',      help="Use dpm?")
parser.add_option('--dryrun',             dest="dryrun",                                 action='store_true',      help='Create submission files without submit?', )
parser.add_option("--queue",              dest="queue",              default="short",    choices=queueChoices,     help="Queue for batch job, default is short")
parser.add_option("--partition",          dest="partition",          default=None,       choices=partitionChoices, help="Partition for batch job, default is c")
parser.add_option("--nNodes" ,            dest="nNodes",             default=None,       type=int,                 help="Number of nodes requested" )
parser.add_option("--nTasks" ,            dest="nTasks",             default=None,       type=int,                 help="Number of times the job will be executed (each with same settings)" )
parser.add_option("--nCPUs"  ,            dest="nCPUs",              default=None,       type=int,                 help="Number of CPUs per task" )
parser.add_option("--nGPUs"  ,            dest="nGPUs",              default=None,       type=int,                 help="Number of GPUs (if --partition g) per task" )
parser.add_option("--gNodes"  ,           dest="gNodes",             default=None,       type=str,                 help="Select specific GPU node, options: P100, V100, RTX, A100")
parser.add_option("--memory",             dest="memory",             default=None,       type=str,                 help="Request memory in GB. Default is 4GB/core")
parser.add_option("--walltime",           dest="walltime",           default="08:00:00", type=str,                 help="Walltime in format DD-HH:MM:SS or HH:MM:SS. Default is 8h!")
parser.add_option("--cmssw",              dest="cmssw",              default="local",    type=str,                 help="Load CMSSW version from singularity container in the format XX_XX_XX. Default is 10_2_18. Set it to None to run without CMSSW!")
parser.add_option('--noLog',              dest="noLog",                                  action='store_true',      help="Do not create a log file")

(options,args) = parser.parse_args()

# Logger
import logger
logger = logger.get_logger( options.logLevel, logFile=None )

# Check and format input
if len(args) != 1 and not options.jobInfo and not options.status:
    raise Exception("Only one argument accepted! Instead this was given: %s"%args)

if options.cmssw == "None":
    options.cmssw = None

if options.cmssw and options.cmssw != "local" and not os.path.exists("/mnt/hephy/cms/container/cmssw_CMSSW_%s.sif"%options.cmssw):
    raise Exception("Singularity container for CMSSW version %s not found: /mnt/hephy/cms/container/cmssw_CMSSW_%s.sif"%(options.cmssw,options.cmssw))

if options.noLog:
    options.output = "/dev/null"

if options.walltime:
    # check format
    walls  = re.findall('^[0-9]{2}\-[0-9]{2}\:[0-9]{2}\:[0-9]{2}$',options.walltime)
    walls += re.findall('^[0-9]{1,3}\:[0-9]{2}\:[0-9]{2}$',options.walltime)
    if not walls:
        raise Exception("Input to walltime must be in the format DD-HH:MM:SS or HH:MM:SS!")
    options.walltime = walls[0]
    wall             = walls[0]
    days             = 0
    if "-" in wall:
        days = int(wall.split("-")[0])
        wall = wall.split("-")[1]
    hours, minutes, seconds = map( int, wall.split(":") )
    walltime = int(datetime.timedelta( days=days, hours=hours, minutes=minutes, seconds=seconds ).total_seconds())
    # check queue for walltime
    if   walltime > 1209600: raise Exception("No queue supports such a long walltime!") # > 14 days
    elif walltime > 172800:  options.queue = "long"   # > 2 days
    elif walltime > 28800:   options.queue = "medium" # > 8 hours
    else:                    options.queue = "short" if not options.queue else options.queue  # <= 8 hours
    if options.dpm: os.environ["min_proxyTime"] = str(int(walltime/3600.)) # minimum proxy time in hours

if options.nGPUs:
    options.partition = "g"
if options.gNodes:
    options.partition = "g"

def getProxy():
    # make sure the proxy is valid as long as your job may take
    if options.queue and not os.getenv("min_proxyTime"):
        if   options.queue == "long":    os.environ["min_proxyTime"] = "192"  # overall max proxy time
        elif options.queue == "medium":  os.environ["min_proxyTime"] = "48"   # proxy > 2 days
        elif options.queue == "short":   os.environ["min_proxyTime"] = "8"    # proxy > 8h
    elif not os.getenv("min_proxyTime"): os.environ["min_proxyTime"] = "8"    # proxy > 8h (default queue)

    if options.cmssw: os.environ["cmssw"] = options.cmssw

    res   = read_from_subprocess( [ "getProxy" ] )
    error = not bool(res)
    for out in res:
        if out and not "find a valid proxy" in out: print out
        if "error" in out.lower(): error = True
    if error:
        logger.info( "Error in getting proxy! Exiting..." )
        sys.exit(1)
    logger.info( "Using proxy certificate %s", proxy )
    proxy_cmd = "export X509_USER_PROXY=%s"%proxy
    return proxy_cmd

def getCommands( line ):
    commands = []
    split    = 1

    try:
        m     = re.search(r"SPLIT[0-9][0-9]*", line)
        split = int(m.group(0).replace('SPLIT',''))
    except:
    	pass

    line = line.split('#')[0]
    if line:
        if split > 1:
            commands.append( (line + " --nJobs %i --job $SLURM_ARRAY_TASK_ID"%split, split) )
        else:
            commands.append( (line, split) )

    return commands

def make_batch_job( file, script, command, proxy_cmd, nJobs=1 ):
    # Submission script
    submitCommands  = []

    submitCommands += ["#!/usr/bin/bash"]
    submitCommands += [""]
    submitCommands += ["#SBATCH -J %s"%options.title]
    submitCommands += ["#SBATCH -D %s"%cwd]

    if options.noLog:
        submitCommands += ["#SBATCH -o /dev/null"]
        submitCommands += ["#SBATCH -e /dev/null"]
    else:
        if nJobs > 1:
            submitCommands += ["#SBATCH -o %s/batch.%%A-%%a.%%J.out"%(options.output)]
            submitCommands += ["#SBATCH -e %s/batch.%%A-%%a.%%J.err"%(options.output)]
        else:
            submitCommands += ["#SBATCH -o %s/batch.%%J.out"%(options.output)]
            submitCommands += ["#SBATCH -e %s/batch.%%J.err"%(options.output)]
    submitCommands += [""]
    if options.nNodes:
        submitCommands += ["#SBATCH --nodes=%i"%options.nNodes]
    if options.nTasks:
        submitCommands += ["#SBATCH --ntasks=%i"%options.nTasks]
    if options.nCPUs:
        submitCommands += ["#SBATCH --cpus-per-task=%i"%options.nCPUs]
    if options.memory:
        submitCommands += ["#SBATCH --mem-per-cpu=%s"%options.memory]
    if options.walltime:
        submitCommands += ["#SBATCH --time=%s"%options.walltime]
    if options.queue:
        submitCommands += ["#SBATCH --qos=%s"%options.queue]
    if options.nGPUs:
        submitCommands += ["#SBATCH --gres=gpu:%i"%options.nGPUs]
    if options.gNodes:
        submitCommands += ["#SBATCH --gres=gpu:%s:%i"%(options.gNodes, options.nGPUs)]
    if options.partition:
        submitCommands += ["#SBATCH --partition %s"%options.partition]
    if nJobs > 1:
        submitCommands += ["#SBATCH --array=0-%i"%(nJobs-1)]
    submitCommands += [""]
    submitCommands += ["echo JobID $SLURM_JOB_ID, Array JobID $SLURM_ARRAY_JOB_ID, TaskID $SLURM_ARRAY_TASK_ID" if nJobs > 1 else "echo JobID $SLURM_JOB_ID"]
    submitCommands += ["echo"]
    submitCommands += [""]

    if options.cmssw and options.cmssw != "local":
        submitCommands += ["echo Loading CMSSW version %s from singularity container /mnt/hephy/cms/container/cmssw_CMSSW_%s.sif"%(options.cmssw, options.cmssw)]
#        submitCommands += ["module load singularity/3.4.1"]
        submitCommands += ["singularity exec /mnt/hephy/cms/container/cmssw_CMSSW_%s.sif sh %s"%(options.cmssw, script)]

    else:
        submitCommands += ["sh " + script]

    if nJobs > 1:
        submitCommands += ["if [ $SLURM_ARRAY_TASK_ID -eq %i ]; then"%(nJobs-1)]
        submitCommands += ["    rm %s"%script]
        submitCommands += ["    echo Removed execution file: '%s'"%script]
        submitCommands += ["fi"]
    else:
        submitCommands += ["rm %s"%script]
        submitCommands += ["echo Removed execution file: '%s'"%script]

#    submitCommands += ["echo"]
#    submitCommands += ["echo Job Statistics:"]
#    submitCommands += ["seff $SLURM_JOB_ID"]

    with open( file, "w" ) as f:
        for cmd in submitCommands:
            f.write(cmd+"\n")
    
    # Execution script
    scriptCommands  = []
    scriptCommands += ["#!/usr/bin/bash"]
    scriptCommands += [""]
    scriptCommands += ["echo Exporting Kerberos Token"]
    scriptCommands += ["echo KRB5CCNAME=~/.krbcc"]
    scriptCommands += ["export KRB5CCNAME=~/.krbcc"]
    scriptCommands += [""]

    if options.cmssw:
        if options.cmssw == "local":
            scriptCommands += ["source /cvmfs/cms.cern.ch/cmsset_default.sh"]
            scriptCommands += ["eval `scramv1 runtime -sh`"]
        else:
            scriptCommands += ["eval $(/opt/cms/common/scram runtime -sh)"]

        if proxy_cmd:
            scriptCommands += [proxy_cmd]
            scriptCommands += ["echo"]
            scriptCommands += ["echo Checking Proxy Certificate:"]
            scriptCommands += ["echo"]
            scriptCommands += ["voms-proxy-info -all"]

    scriptCommands += ["echo"]
    if options.nTasks:
        scriptCommands += ["echo Executing user command for each of the %i tasks"%options.nTasks]
        scriptCommands += ["echo 'srun -l %s'"%command]
        scriptCommands += ["echo"]
        scriptCommands += ["srun -l %s"%command]

    else:
        scriptCommands += ["echo Executing user command:"]
        scriptCommands += ["echo '%s'"%command]
        scriptCommands += ["echo"]
        scriptCommands += [command]

    scriptCommands += ["echo"]

    if proxy_cmd and options.cmssw:
        scriptCommands += ["echo Checking Proxy Certificate:"]
        scriptCommands += ["echo"]
        scriptCommands += ["voms-proxy-info -all"]

    scriptCommands += ["echo"]
    scriptCommands += ["echo Done executing command:"]
    scriptCommands += ["echo '%s'"%command]

    with open( script, "w" ) as f:
        for cmd in scriptCommands:
            f.write(cmd+"\n")
    

if __name__ == '__main__':

    # Execute commands w/o submission (if set)
    if options.status:
        os.system("squeue -u %s"%user)
        sys.exit(0)

    if options.jobInfo:
        os.system("jobinfo %i"%options.jobInfo)
        sys.exit(0)

    # create logfile output dir
    if not options.noLog and not os.path.isdir( options.output ):
        os.makedirs( options.output )

    # create logfile input directory
    if not os.path.isdir( options.tmpDirectory ):
        os.makedirs( options.tmpDirectory )

    # If X509_USER_PROXY is set, use existing proxy.
    proxy_cmd = getProxy() if options.dpm else ""

    # load file with commands
    if os.path.isfile( args[0] ):
        commands = []
        with open( args[0], "r" ) as f:
            for line in f.xreadlines():
                commands.extend( getCommands( line.rstrip("\n") ) )

    # or just the one command
    elif isinstance( args[0], str ):
        commands = getCommands( args[0] )

    for command in commands:
        hash_string    = hash( "_".join( map( str, [time.time(), command, uuid.uuid4()] ) ) )
        job_file       = "%s/batch_%s.sub"%(options.tmpDirectory,hash_string)
        script_file    = "%s/script_%s.sh"%(options.tmpDirectory,hash_string)
        submit_command = "sbatch %s"%(job_file)

        make_batch_job( job_file, script_file, command[0], proxy_cmd, nJobs=command[1] )

        logger.debug( "Created submission file: %s"%job_file )
        logger.debug( "Created execution file: %s"%script_file )

        if not options.dryrun:
            os.system( submit_command )
            os.remove( job_file )
            logger.debug( "Removed submission file: %s"%job_file )
            logger.info( "Log file written to %s"%options.output )
        else:
            logger.info( "Submit command: %s"%submit_command )
            logger.info( "Created submission file: %s"%job_file )
            logger.info( "Created execution file: %s"%script_file )

