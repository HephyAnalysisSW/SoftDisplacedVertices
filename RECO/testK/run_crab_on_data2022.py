import subprocess

datasets = {
    # 'Run2022C-v1': '/JetMET/Run2022C-v1/RAW',
    'Run2022E-v1': '/JetMET/Run2022E-v1/RAW',
    # 'Run2022F-v1': '/JetMET/Run2022F-v1/RAW',
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
config.JobType.psetName = '/afs/cern.ch/user/a/aguven/crab_submissions/CMSSW_13_0_16/src/SoftDisplacedVertices/RECO/configuration/Data_Run2022_RECO.py'
config.JobType.maxMemoryMB = 8000
config.JobType.numCores = 4

config.Data.inputDataset = '{}'
config.Data.inputDBS = 'global'
# config.Data.splitting = 'Automatic'
config.Data.splitting = 'FileBased'
config.Data.unitsPerJob = 1
config.JobType.maxJobRuntimeMin = 1440
config.Data.publication = True
config.Data.outputDatasetTag = '{}_aod_v1'

# Run2022C
# --------------------------------------------------------------------
# config.Data.lumiMask = '/afs/cern.ch/user/a/aguven/crab_submissions/CMSSW_13_0_16/src/SoftDisplacedVertices/CustomMiniAOD/testK/crab_projects/crab_20250513_120549/results/notFinishedLumis.json'
# config.Data.inputBlocks = ['/JetMET/Run2022C-v1/RAW#4cc8f898-85d5-4100-a865-c4bb9ec9a4ce', '/JetMET/Run2022C-v1/RAW#70bea70a-0716-4a71-8fa6-a1ecd9e084ae', '/JetMET/Run2022C-v1/RAW#fe6064dd-5d32-4339-bd27-655f82a19a41']

config.Data.lumiMask = '/afs/cern.ch/user/a/aguven/crab_submissions/CMSSW_13_0_16/src/SoftDisplacedVertices/CustomMiniAOD/testK/crab_projects/crab_20250522_102408/results/notPublishedLumis.json'
config.Data.inputBlocks = ['/JetMET/Run2022E-v1/RAW#6077757b-462d-41cf-930c-c9a00505b2e5']


# Run2022F
# --------------------------------------------------------------------
# config.Data.lumiMask = '/afs/cern.ch/user/a/aguven/crab_submissions/CMSSW_13_0_16/src/SoftDisplacedVertices/CustomMiniAOD/testK/crab_projects/crab_20250513_120736/results/notFinishedLumis.json'
# config.Data.inputBlocks = ['/JetMET/Run2022F-v1/RAW#f0b37297-acb7-4cbb-a2b5-89218d2b5e2d', '/JetMET/Run2022F-v1/RAW#f8198790-1f38-412c-9de9-e80e813b6b83', '/JetMET/Run2022F-v1/RAW#5d75a80b-8d6d-464d-b999-b4e02f76e8aa']

# config.Data.partialDataset = True
# config.Data.ignoreLocality = True

# config.Site.blacklist=["T2_BR_SPRACE"]
# config.Site.whitelist=["T1_RU*", "T1_US*"]
# config.Site.ignoreGlobalBlacklist = True

config.Site.storageSite = "T2_AT_Vienna"
""".format(name, tag)
    with open("crabConfig.py", "w") as f:
        f.write(crabConfig)
    
    print(name)
    subprocess.call(['crab', 'submit', '-c', 'crabConfig.py'])