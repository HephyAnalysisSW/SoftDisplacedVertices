import subprocess

datasets = {
    'Run2023B0':       '/JetMET0/aguven-Run2023B0_mini_v1-db68a568d98f6284caffd959f8045351/USER',
    'Run2023C0_part1': '/JetMET0/aguven-Run2023C0_mini_v1-27920a6238eafef6e245fe9c0109a0f6/USER',
    'Run2023C0_part2': '/JetMET0/aguven-Run2023C0_mini_v1-db68a568d98f6284caffd959f8045351/USER',
    'Run2023D0':       '/JetMET0/aguven-Run2023D0_mini_v1-db68a568d98f6284caffd959f8045351/USER',
    'Run2023B1_part1': '/JetMET1/aguven-Run2023B1_mini_v1-27920a6238eafef6e245fe9c0109a0f6/USER',
    'Run2023B1_part2': '/JetMET1/aguven-Run2023B1_mini_v1-db68a568d98f6284caffd959f8045351/USER',
    'Run2023C1_part1': '/JetMET1/aguven-Run2023C1_mini_v1-27920a6238eafef6e245fe9c0109a0f6/USER',
    'Run2023C1_part2': '/JetMET1/aguven-Run2023C1_mini_v1-db68a568d98f6284caffd959f8045351/USER',
    'Run2023D1_part1': '/JetMET1/aguven-Run2023D1_mini_v1-27920a6238eafef6e245fe9c0109a0f6/USER',
    'Run2023D1_part2': '/JetMET1/aguven-Run2023D1_mini_v1-db68a568d98f6284caffd959f8045351/USER',
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
config.JobType.psetName = '/afs/cern.ch/user/a/aguven/crab_submissions/CMSSW_13_0_16/src/SoftDisplacedVertices/CustomNanoAOD/configuration/Data_Run2023_CustomNanoAOD.py'
config.JobType.maxMemoryMB = 4000
config.JobType.numCores = 2

config.Data.inputDataset = '{}'
config.Data.inputDBS = 'phys03'
config.Data.splitting = 'Automatic'
config.Data.publication = True
config.Data.outputDatasetTag = '{}_nano_v1'
# config.Data.lumiMask = 'https://cms-service-dqmdc.web.cern.ch/CAF/certification/Collisions23/Cert_Collisions2023_366442_370790_Golden.json'
config.Data.partialDataset = False
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

