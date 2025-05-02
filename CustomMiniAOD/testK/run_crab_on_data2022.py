import subprocess

datasets = {
    'MET_Run2022B':    '/MET/Run2022B-27Jun2023-v2/AOD',
    # 'MET_Run2022C':    '/MET/Run2022C-27Jun2023-v2/AOD',
    # 'JETMET_Run2022C': '/JetMET/Run2022C-27Jun2023-v1/AOD',
    # 'JETMET_Run2022D': '/JetMET/Run2022D-27Jun2023-v2/AOD',
    # 'JETMET_Run2022E': '/JetMET/Run2022E-27Jun2023-v1/AOD',
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
config.JobType.psetName = '/afs/cern.ch/user/a/aguven/crab_submissions/CMSSW_13_0_16/src/SoftDisplacedVertices/CustomMiniAOD/configuration/Data_Run2022_CustomMiniAOD.py'
config.JobType.maxMemoryMB = 4000
config.JobType.numCores = 2

config.Data.inputDataset = '{}'
config.Data.inputDBS = 'global'
config.Data.splitting = 'Automatic'
config.Data.publication = True
config.Data.outputDatasetTag = '{}-mini-22Sep2023-v1'
config.Data.lumiMask = 'https://cms-service-dqmdc.web.cern.ch/CAF/certification/Collisions22/Cert_Collisions2022_355100_362760_Golden.json'
config.Data.partialDataset = False
config.Data.ignoreLocality = True

# config.Site.blacklist=["T2_BR_SPRACE"]
# config.Site.whitelist=["T1_RU*", "T1_US*"]
# config.Site.ignoreGlobalBlacklist = True

config.Site.storageSite = "T2_AT_Vienna"
""".format(name, tag.split('_')[1])
    with open("crabConfig.py", "w") as f:
        f.write(crabConfig)
    
    print(name)
    subprocess.call(['crab', 'submit', '-c', 'crabConfig.py'])

