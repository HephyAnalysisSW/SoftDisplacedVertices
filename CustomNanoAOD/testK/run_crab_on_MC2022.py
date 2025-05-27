import subprocess

datasets = {
    # "wjetstolnu4jets_2022":   "/WtoLNu-4Jets_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-Run3Summer22CustomMiniAODv4-130X_mcRun3_2022_realistic_v5-v2-19cfc522e1e16b3ef9e81defded35d39/USER",
    "zto2nu4jetsht0100_2022": "/Zto2Nu-4Jets_HT-100to200_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-Run3Summer22CustomMiniAODv4-130X_mcRun3_2022_realistic_v5-v1-19cfc522e1e16b3ef9e81defded35d39/USER",
    "zto2nu4jetsht0200_2022": "/Zto2Nu-4Jets_HT-200to400_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-Run3Summer22CustomMiniAODv4-130X_mcRun3_2022_realistic_v5-v1-19cfc522e1e16b3ef9e81defded35d39/USER",
    "zto2nu4jetsht0400_2022": "/Zto2Nu-4Jets_HT-400to800_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-Run3Summer22CustomMiniAODv4-130X_mcRun3_2022_realistic_v5-v2-19cfc522e1e16b3ef9e81defded35d39/USER",
    "zto2nu4jetsht0800_2022": "/Zto2Nu-4Jets_HT-800to1500_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-Run3Summer22CustomMiniAODv4-130X_mcRun3_2022_realistic_v5-v1-19cfc522e1e16b3ef9e81defded35d39/USER",
    "zto2nu4jetsht1500_2022": "/Zto2Nu-4Jets_HT-1500to2500_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-Run3Summer22CustomMiniAODv4-130X_mcRun3_2022_realistic_v5-v1-19cfc522e1e16b3ef9e81defded35d39/USER",
    "zto2nu4jetsht2500_2022": "/Zto2Nu-4Jets_HT-2500_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-Run3Summer22CustomMiniAODv4-130X_mcRun3_2022_realistic_v5-v1-19cfc522e1e16b3ef9e81defded35d39/USER",
    "qcd4jetsht0040_2022" :   "/QCD-4Jets_HT-40to70_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-Run3Summer22CustomMiniAODv4-130X_mcRun3_2022_realistic_v5-v1-19cfc522e1e16b3ef9e81defded35d39/USER",
    "qcd4jetsht0070_2022" :   "/QCD-4Jets_HT-70to100_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-Run3Summer22CustomMiniAODv4-130X_mcRun3_2022_realistic_v5-v2-19cfc522e1e16b3ef9e81defded35d39/USER",
    "qcd4jetsht0100_2022" :   "/QCD-4Jets_HT-100to200_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-Run3Summer22CustomMiniAODv4-130X_mcRun3_2022_realistic_v5-v2-19cfc522e1e16b3ef9e81defded35d39/USER",
    "qcd4jetsht0200_2022" :   "/QCD-4Jets_HT-200to400_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-Run3Summer22CustomMiniAODv4-130X_mcRun3_2022_realistic_v5-v2-19cfc522e1e16b3ef9e81defded35d39/USER",
    "qcd4jetsht0400_2022" :   "/QCD-4Jets_HT-400to600_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-Run3Summer22CustomMiniAODv4-130X_mcRun3_2022_realistic_v5-v2-19cfc522e1e16b3ef9e81defded35d39/USER",
    "qcd4jetsht0600_2022" :   "/QCD-4Jets_HT-600to800_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-Run3Summer22CustomMiniAODv4-130X_mcRun3_2022_realistic_v5-v5-19cfc522e1e16b3ef9e81defded35d39/USER",
    "qcd4jetsht0800_2022" :   "/QCD-4Jets_HT-800to1000_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-Run3Summer22CustomMiniAODv4-130X_mcRun3_2022_realistic_v5-v2-19cfc522e1e16b3ef9e81defded35d39/USER",
    "qcd4jetsht1000_2022" :   "/QCD-4Jets_HT-1000to1200_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-Run3Summer22CustomMiniAODv4-130X_mcRun3_2022_realistic_v5-v1-19cfc522e1e16b3ef9e81defded35d39/USER",
    "qcd4jetsht1200_2022" :   "/QCD-4Jets_HT-1200to1500_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-Run3Summer22CustomMiniAODv4-130X_mcRun3_2022_realistic_v5-v1-19cfc522e1e16b3ef9e81defded35d39/USER",
    "qcd4jetsht1500_2022" :   "/QCD-4Jets_HT-1500to2000_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-Run3Summer22CustomMiniAODv4-130X_mcRun3_2022_realistic_v5-v1-19cfc522e1e16b3ef9e81defded35d39/USER",
    "qcd4jetsht2000_2022" :   "/QCD-4Jets_HT-2000_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-Run3Summer22CustomMiniAODv4-130X_mcRun3_2022_realistic_v5-v3-19cfc522e1e16b3ef9e81defded35d39/USER",
    "ttto4q_2022"         :   "/TTto4Q_TuneCP5_13p6TeV_powheg-pythia8/aguven-Run3Summer22CustomMiniAODv4-130X_mcRun3_2022_realistic_v5-v1-19cfc522e1e16b3ef9e81defded35d39/USER",
    "ttto2l2nu_2022"       :  "/TTto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8/aguven-Run3Summer22CustomMiniAODv4-130X_mcRun3_2022_realistic_v5-v1-19cfc522e1e16b3ef9e81defded35d39/USER",
    "tttolnu2q_2022"      :   "/TTtoLNu2Q_TuneCP5_13p6TeV_powheg-pythia8/aguven-Run3Summer22CustomMiniAODv4-130X_mcRun3_2022_realistic_v5-v1-19cfc522e1e16b3ef9e81defded35d39/USER",

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
config.JobType.psetName = '/afs/cern.ch/user/a/aguven/crab_submissions/CMSSW_13_0_16/src/SoftDisplacedVertices/CustomNanoAOD/configuration/MC_Run3Summer22_CustomNanoAOD.py'
config.JobType.maxMemoryMB = 4000
config.JobType.numCores = 2

config.Data.inputDataset = '{}'
config.Data.inputDBS = 'phys03'
config.Data.splitting = 'Automatic'
# config.Data.splitting = 'FileBased'
# config.Data.unitsPerJob = 30
config.Data.publication = True
config.Data.outputDatasetTag = 'Run3Summer22CustomNanoAODv12-130X_mcRun3_2022_realistic_v5-v1'
# config.Data.partialDataset = True
# config.Data.ignoreLocality = True

# config.Site.blacklist=["T2_BR_SPRACE"]
# config.Site.blacklist=["T2_BR_SPRACE", "T2_IT_Pisa"]
# config.Site.whitelist=["T1_RU_JINR_Tape"]
# config.Site.whitelist=["T1_RU*", "T1_US*"]
# config.Site.ignoreGlobalBlacklist = True

config.Site.storageSite = "T2_AT_Vienna"
""".format(name)
    with open("crabConfig.py", "w") as f:
        f.write(crabConfig)
    
    print(name)
    subprocess.call(['crab', 'submit', '-c', 'crabConfig.py'])
    # subprocess.call(['crab', 'submit', '-c', 'crabConfig.py', '--dryrun'])

# crab_20250326_140211