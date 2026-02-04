import subprocess

datasets = {
    'Run2022F_JetMET': '/JetMET/lian-Run2022F_JetMET_mini-7acd5aba622e0d3a7b7a3e48d7c07484/USER',
    'Run2022G_JetMET': '/JetMET/lian-Run2022G_JetMET_mini-7acd5aba622e0d3a7b7a3e48d7c07484/USER',
}


for tag, name in datasets.items():

    crabConfig = """
import CRABClient
from CRABClient.UserUtilities import config 

config = config()

config.General.requestName = '{1}'
config.General.workArea = 'crab_projects'
config.General.transferOutputs = True

config.JobType.pluginName = 'Analysis'
config.JobType.psetName = '/users/ang.li/public/SoftDV/CMSSW_13_0_16/src/SoftDisplacedVertices/CustomNanoAOD/configuration/Data_Run2022FG_CustomNanoAOD.py'
config.JobType.maxMemoryMB = 4000
config.JobType.numCores = 2

config.Data.inputDataset = '{0}'
config.Data.inputDBS = 'phys03'
config.Data.splitting = 'Automatic'
config.Data.publication = True
config.Data.outputDatasetTag = '{1}_nano_v1'
#config.Data.lumiMask = 'https://cms-service-dqmdc.web.cern.ch/CAF/certification/Collisions22/Cert_Collisions2022_355100_362760_Golden.json'
config.Data.partialDataset = False
# config.Data.ignoreLocality = True

# config.Site.blacklist=["T2_BR_SPRACE"]
# config.Site.whitelist=["T1_RU*", "T1_US*"]
# config.Site.ignoreGlobalBlacklist = True
config.Site.whitelist=['T2_AT_Vienna']

config.Site.storageSite = "T2_AT_Vienna"
""".format(name, tag)
    with open("crabConfig_{}.py".format(tag), "w") as f:
        f.write(crabConfig)
    
    print(name)
    subprocess.call(['crab', 'submit', '-c', 'crabConfig_{}.py'.format(tag)])

