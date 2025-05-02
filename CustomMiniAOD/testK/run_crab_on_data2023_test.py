import subprocess

datasets = {
    # 'Run2023B0': '/JetMET0/Run2023B-19Dec2023-v1/AOD',
    'Run2023B1': '/JetMET1/aguven-Run2023B1_aod_v1-546c7f514fafa20e4cf509612ce529c3/USER',
    'Run2023C0': '/JetMET0/aguven-Run2023C0_aod_v1-546c7f514fafa20e4cf509612ce529c3/USER',
    'Run2023C1': '/JetMET1/aguven-Run2023C1_aod_v1-546c7f514fafa20e4cf509612ce529c3/USER',
    # 'Run2023D0': '/JetMET0/Run2023D-19Dec2023-v1/AOD',
    'Run2023D1': '/JetMET1/aguven-Run2023D1_aod_v1-546c7f514fafa20e4cf509612ce529c3/USER'
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
config.JobType.psetName = '/afs/cern.ch/user/a/aguven/crab_submissions/CMSSW_13_0_16/src/SoftDisplacedVertices/CustomMiniAOD/configuration/Data_Run2023_CustomMiniAOD.py'
config.JobType.maxMemoryMB = 4000
config.JobType.numCores = 2

config.Data.inputDataset = '{}'
config.Data.inputDBS = 'phys03'
config.Data.splitting = 'Automatic'
config.Data.publication = True
config.Data.outputDatasetTag = '{}_mini_v2'
# config.Data.lumiMask = 'https://cms-service-dqmdc.web.cern.ch/CAF/certification/Collisions23/Cert_Collisions2023_366442_370790_Golden.json'
config.Data.lumiMask = '/afs/cern.ch/user/a/aguven/crab_submissions/CMSSW_13_0_16/src/SoftDisplacedVertices/RECO/testK/lumi_mask.txt'
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
    
    print(name)
    subprocess.call(['crab', 'submit', '-c', 'crabConfig.py'])

