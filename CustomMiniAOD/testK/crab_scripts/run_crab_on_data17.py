import subprocess

datasets = {
    'Run2017B': '/SingleMuon/Run2017B-15Feb2022_UL2017-v1/AOD',
    'Run2017C': '/SingleMuon/Run2017C-15Feb2022_UL2017-v1/AOD',
    'Run2017D': '/SingleMuon/Run2017D-15Feb2022_UL2017-v1/AOD',
    'Run2017E': '/SingleMuon/Run2017E-15Feb2022_UL2017-v1/AOD',
    'Run2017F': '/SingleMuon/Run2017F-15Feb2022_UL2017-v1/AOD',
}


for tag, name in datasets.items():

    crabConfig = """
import CRABClient
from CRABClient.UserUtilities import config 

config = config()

# config.General.requestName = 'tutorial_Aug2021_Data_analysis'
config.General.workArea = 'crab_projects'
config.General.transferOutputs = True

config.JobType.pluginName = 'Analysis'
config.JobType.psetName = '/users/alikaan.gueven/AOD_to_nanoAOD/CMSSW_13_0_16/src/SoftDisplacedVertices/CustomMiniAOD/configuration/Data_UL17mu_CustomMiniAOD.py'
config.JobType.maxMemoryMB = 4000
config.JobType.numCores = 4

config.Data.inputDataset = '{}'
config.Data.inputDBS = 'global'
config.Data.splitting = 'Automatic'
config.Data.publication = True
config.Data.outputDatasetTag = '{}_mini_v1'
config.Data.lumiMask = 'https://cms-service-dqmdc.web.cern.ch/CAF/certification/Collisions23/Cert_Collisions2023_366442_370790_Golden.json'
config.Data.partialDataset = False
# config.Data.ignoreLocality = True

# config.Site.blacklist=["T2_BR_SPRACE"]
# config.Site.blacklist=["T2_BR_SPRACE", "T2_IT_Pisa"]
# config.Site.whitelist=["T1_RU_JINR_Tape"]
# config.Site.whitelist=["T1_RU*", "T1_US*"]
# config.Site.ignoreGlobalBlacklist = True

config.Site.storageSite = "T2_AT_Vienna"
""".format(name, tag)
    with open("crabConfig.py", "w") as f:
        f.write(crabConfig)
    
    print name
    subprocess.call(['crab', 'submit', '-c', 'crabConfig.py'])

