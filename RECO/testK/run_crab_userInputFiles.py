import subprocess

datasets = {
    # 'Run2023B1': '/JetMET1/Run2023B-v1/RAW',
    'Run2023C0': '/JetMET0/Run2023C-v1/RAW',
    'Run2023C1': '/JetMET1/Run2023C-v1/RAW',
    'Run2023D1': '/JetMET1/Run2023D-v1/RAW'
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
config.JobType.psetName = '/afs/cern.ch/user/a/aguven/crab_submissions/CMSSW_13_0_16/src/SoftDisplacedVertices/RECO/configuration/Data_Run2023_RECO.py'
config.JobType.maxMemoryMB = 4000
config.JobType.numCores = 2

config.Data.inputDataset = '{}'
config.Data.inputDBS = 'global'
config.Data.splitting = 'Automatic'
config.Data.publication = True
config.Data.outputDatasetTag = '{}_aod_v1'
config.Data.lumiMask = '/afs/cern.ch/user/a/aguven/crab_submissions/CMSSW_13_0_16/src/SoftDisplacedVertices/RECO/testK/lumi_mask.txt'
# config.Data.partialDataset = True
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

