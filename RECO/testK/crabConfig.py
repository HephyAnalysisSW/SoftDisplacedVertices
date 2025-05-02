
import CRABClient
from CRABClient.UserUtilities import config 

config = config()

# config.General.requestName = 'tutorial_Aug2021_Data_analysis'
config.General.workArea = 'crab_projects'
config.General.transferOutputs = True

config.JobType.pluginName = 'Analysis'
config.JobType.psetName = '/afs/cern.ch/user/a/aguven/crab_submissions/CMSSW_13_0_16/src/SoftDisplacedVertices/RECO/configuration/Data_Run2023_RECO.py'
config.JobType.maxMemoryMB = 8000
config.JobType.numCores = 4

config.Data.inputDataset = '/JetMET1/Run2023C-v1/RAW'
config.Data.inputDBS = 'global'
# config.Data.splitting = 'Automatic'
config.Data.splitting = 'FileBased'
config.Data.unitsPerJob = 1
config.JobType.maxJobRuntimeMin = 1440
config.Data.publication = True
config.Data.outputDatasetTag = 'Run2023C1_aod_v1'
config.Data.lumiMask = '/afs/cern.ch/user/a/aguven/crab_submissions/CMSSW_13_0_16/src/SoftDisplacedVertices/RECO/testK/lumi_mask.txt'
config.Data.inputBlocks = ['/JetMET1/Run2023C-v1/RAW#b83949de-530b-4b1c-834a-d91269020eaa']
# config.Data.partialDataset = True
# config.Data.ignoreLocality = True

# config.Site.blacklist=["T2_BR_SPRACE"]
# config.Site.whitelist=["T1_RU*", "T1_US*"]
# config.Site.ignoreGlobalBlacklist = True

config.Site.storageSite = "T2_AT_Vienna"
