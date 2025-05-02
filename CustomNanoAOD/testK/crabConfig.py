
import CRABClient
from CRABClient.UserUtilities import config 

config = config()

# config.General.requestName = 'tutorial_Aug2021_Data_analysis'
config.General.workArea = 'crab_projects'
config.General.transferOutputs = True

config.JobType.pluginName = 'Analysis'
config.JobType.psetName = '/afs/cern.ch/user/a/aguven/crab_submissions/CMSSW_13_0_16/src/SoftDisplacedVertices/CustomNanoAOD/configuration/Data_Run2023_CustomNanoAOD.py'
config.JobType.maxMemoryMB = 4000
config.JobType.numCores = 2

config.Data.inputDataset = '/JetMET1/aguven-Run2023D1_mini_v1-db68a568d98f6284caffd959f8045351/USER'
config.Data.inputDBS = 'phys03'
config.Data.splitting = 'Automatic'
config.Data.publication = True
config.Data.outputDatasetTag = 'Run2023D1_part2_nano_v1'
# config.Data.lumiMask = 'https://cms-service-dqmdc.web.cern.ch/CAF/certification/Collisions23/Cert_Collisions2023_366442_370790_Golden.json'
config.Data.partialDataset = False
# config.Data.ignoreLocality = True

# config.Site.blacklist=["T2_BR_SPRACE"]
# config.Site.whitelist=["T1_RU*", "T1_US*"]
# config.Site.ignoreGlobalBlacklist = True

config.Site.storageSite = "T2_AT_Vienna"
