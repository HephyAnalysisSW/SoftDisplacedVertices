import subprocess

datasets = {
    'Run2023C1_JetMET0': '/JetMET0/lian-jetmet0_2023c1_mini-10f911a333cf2fbe84f211b19d14be51/USER',
    'Run2023C2_JetMET0': '/JetMET0/lian-jetmet0_2023c2_mini-10f911a333cf2fbe84f211b19d14be51/USER',
    'Run2023C3_JetMET0': '/JetMET0/lian-jetmet0_2023c3_mini-10f911a333cf2fbe84f211b19d14be51/USER',
    'Run2023C4_JetMET0': '/JetMET0/lian-jetmet0_2023c4_mini-10f911a333cf2fbe84f211b19d14be51/USER',
    'Run2023D1_JetMET0': '/JetMET0/lian-jetmet0_2023d1_mini-10f911a333cf2fbe84f211b19d14be51/USER',
    'Run2023D2_JetMET0': '/JetMET0/lian-jetmet0_2023d2_mini-10f911a333cf2fbe84f211b19d14be51/USER',
    'Run2023C1_JetMET1': '/JetMET1/lian-jetmet1_2023c1_mini-10f911a333cf2fbe84f211b19d14be51/USER',
    'Run2023C2_JetMET1': '/JetMET1/lian-jetmet1_2023c2_mini-10f911a333cf2fbe84f211b19d14be51/USER',
    'Run2023C3_JetMET1': '/JetMET1/lian-jetmet1_2023c3_mini-10f911a333cf2fbe84f211b19d14be51/USER',
    'Run2023C4_JetMET1': '/JetMET1/lian-jetmet1_2023c4_mini-10f911a333cf2fbe84f211b19d14be51/USER',
    'Run2023D1_JetMET1': '/JetMET1/lian-jetmet1_2023d1_mini-10f911a333cf2fbe84f211b19d14be51/USER',
    'Run2023D2_JetMET1': '/JetMET1/lian-jetmet1_2023d2_mini-10f911a333cf2fbe84f211b19d14be51/USER',
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
config.JobType.psetName = '/users/ang.li/public/SoftDV/CMSSW_13_0_16/src/SoftDisplacedVertices/CustomNanoAOD/configuration/Data_Run2023_CustomNanoAOD.py'
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

