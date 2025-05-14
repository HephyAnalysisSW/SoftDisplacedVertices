import subprocess

datasets = {
    'Run2023B0': '/JetMET0/Run2023B-19Dec2023-v1/AOD',
    'Run2023B1': '/JetMET1/Run2023B-19Dec2023-v1/AOD',
    'Run2023C0': '/JetMET0/Run2023C-19Dec2023-v1/AOD',
    'Run2023C1': '/JetMET1/Run2023C-19Dec2023-v1/AOD',
    'Run2023D0': '/JetMET0/Run2023D-19Dec2023-v1/AOD',
    'Run2023D1': '/JetMET1/Run2023D-19Dec2023-v1/AOD'
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
config.JobType.psetName = '/users/alikaan.gueven/AOD_to_nanoAOD/CMSSW_13_0_16/src/SoftDisplacedVertices/CustomMiniAOD/configuration/Data_Run2023_CustomMiniAOD.py'
config.JobType.maxMemoryMB = 8000
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

