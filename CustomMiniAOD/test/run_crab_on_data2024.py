import subprocess

datasets = {
            #"jetmet0_2024c":    "/JetMET0/Run2024C-EXOSoftDisplacedVertices-2024CDEReprocessing-v1/AOD",
            #"jetmet0_2024d":    "/JetMET0/Run2024D-EXOSoftDisplacedVertices-2024CDEReprocessing-v1/AOD",
            #"jetmet0_2024e":    "/JetMET0/Run2024E-EXOSoftDisplacedVertices-2024CDEReprocessing-v1/AOD",
            "jetmet0_2024f":    "/JetMET0/Run2024F-EXOSoftDisplacedVertices-PromptReco-v1/AOD",
            "jetmet0_2024g":    "/JetMET0/Run2024G-EXOSoftDisplacedVertices-PromptReco-v1/AOD",
            "jetmet0_2024h":    "/JetMET0/Run2024H-EXOSoftDisplacedVertices-PromptReco-v1/AOD",
            "jetmet0_2024i1":   "/JetMET0/Run2024I-EXOSoftDisplacedVertices-PromptReco-v1/AOD",
            "jetmet0_2024i2":   "/JetMET0/Run2024I-EXOSoftDisplacedVertices-PromptReco-v2/AOD",

            "jetmet1_2024c":    "/JetMET1/Run2024C-EXOSoftDisplacedVertices-2024CDEReprocessing-v2/AOD",
            #"jetmet1_2024d":    "/JetMET1/Run2024D-EXOSoftDisplacedVertices-2024CDEReprocessing-v1/AOD",
            #"jetmet1_2024e":    "/JetMET1/Run2024E-EXOSoftDisplacedVertices-2024CDEReprocessing-v1/AOD",
            "jetmet1_2024f":    "/JetMET1/Run2024F-EXOSoftDisplacedVertices-PromptReco-v1/AOD",
            "jetmet1_2024g":    "/JetMET1/Run2024G-EXOSoftDisplacedVertices-PromptReco-v1/AOD",
            "jetmet1_2024h":    "/JetMET1/Run2024H-EXOSoftDisplacedVertices-PromptReco-v1/AOD",
            "jetmet1_2024i1":   "/JetMET1/Run2024I-EXOSoftDisplacedVertices-PromptReco-v1/AOD",
            "jetmet1_2024i2":   "/JetMET1/Run2024I-EXOSoftDisplacedVertices-PromptReco-v2/AOD"
}


for tag, name in datasets.items():

    crabConfig = """
import CRABClient
from CRABClient.UserUtilities import config 

config = config()

config.General.requestName = 'crab_{1}'
config.General.workArea = 'crab_projects'
config.General.transferOutputs = True

config.JobType.pluginName = 'Analysis'
config.JobType.psetName = '/users/ang.li/public/SoftDV/CMSSW_15_0_2/src/SoftDisplacedVertices/CustomMiniAOD/configuration/2024/Data_Run2024_CustomMiniAOD.py'
config.JobType.maxMemoryMB = 4000
config.JobType.numCores = 2

config.Data.inputDataset = '{0}'
config.Data.inputDBS = 'global'
config.Data.splitting = 'Automatic'
config.Data.publication = True
config.Data.outputDatasetTag = '{1}_mini_v1'
config.Data.lumiMask = 'https://cms-service-dqmdc.web.cern.ch/CAF/certification/Collisions24/Cert_Collisions2024_378981_386951_Golden.json'
config.Data.partialDataset = False
# config.Data.ignoreLocality = True

# config.Site.blacklist=["T2_BR_SPRACE"]
# config.Site.whitelist=["T1_RU*", "T1_US*"]
# config.Site.ignoreGlobalBlacklist = True

config.Site.storageSite = "T2_AT_Vienna"
""".format(name, tag)
    with open("crabConfig_{}.py".format(tag), "w") as f:
        f.write(crabConfig)
    
    print(name)
    subprocess.call(['crab', 'submit', '-c', 'crabConfig_{}.py'.format(tag)])

