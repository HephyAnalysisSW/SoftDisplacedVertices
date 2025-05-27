import subprocess

datasets = {
    # "wjetstolnu4jets_ee_2022":   "/WtoLNu-4Jets_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-Run3Summer22EEMiniAODv4-130X_mcRun3_2022_realistic_postEE_v6-v1-8c5ad256337976e7626d1bd32f265263/USER",
    "zto2nu4jetsht0100_ee_2022": "/Zto2Nu-4Jets_HT-100to200_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-Run3Summer22EEMiniAODv4-130X_mcRun3_2022_realistic_postEE_v6-v1-8c5ad256337976e7626d1bd32f265263/USER",
    "zto2nu4jetsht0200_ee_2022": "/Zto2Nu-4Jets_HT-200to400_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-Run3Summer22EEMiniAODv4-130X_mcRun3_2022_realistic_postEE_v6-v1-8c5ad256337976e7626d1bd32f265263/USER",
    "zto2nu4jetsht0400_ee_2022": "/Zto2Nu-4Jets_HT-400to800_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-Run3Summer22EEMiniAODv4-130X_mcRun3_2022_realistic_postEE_v6-v3-8c5ad256337976e7626d1bd32f265263/USER",
    "zto2nu4jetsht0800_ee_2022": "/Zto2Nu-4Jets_HT-800to1500_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-Run3Summer22EEMiniAODv4-130X_mcRun3_2022_realistic_postEE_v6-v1-8c5ad256337976e7626d1bd32f265263/USER",
    "zto2nu4jetsht1500_ee_2022": "/Zto2Nu-4Jets_HT-1500to2500_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-Run3Summer22EEMiniAODv4-130X_mcRun3_2022_realistic_postEE_v6-v1-8c5ad256337976e7626d1bd32f265263/USER",
    "zto2nu4jetsht2500_ee_2022": "/Zto2Nu-4Jets_HT-2500_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-Run3Summer22EEMiniAODv4-130X_mcRun3_2022_realistic_postEE_v6-v1-8c5ad256337976e7626d1bd32f265263/USER",
    "qcd4jetsht0040_ee_2022" :   "/QCD-4Jets_HT-40to70_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-Run3Summer22EEMiniAODv4-130X_mcRun3_2022_realistic_postEE_v6-v3-8c5ad256337976e7626d1bd32f265263/USER",
    "qcd4jetsht0070_ee_2022" :   "/QCD-4Jets_HT-70to100_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-Run3Summer22EEMiniAODv4-130X_mcRun3_2022_realistic_postEE_v6-v1-8c5ad256337976e7626d1bd32f265263/USER",
    "qcd4jetsht0100_ee_2022" :   "/QCD-4Jets_HT-100to200_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-Run3Summer22EEMiniAODv4-130X_mcRun3_2022_realistic_postEE_v6-v1-8c5ad256337976e7626d1bd32f265263/USER",
    "qcd4jetsht0200_ee_2022" :   "/QCD-4Jets_HT-200to400_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-Run3Summer22EEMiniAODv4-130X_mcRun3_2022_realistic_postEE_v6-v1-8c5ad256337976e7626d1bd32f265263/USER",
    "qcd4jetsht0400_ee_2022" :   "/QCD-4Jets_HT-400to600_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-Run3Summer22EEMiniAODv4-130X_mcRun3_2022_realistic_postEE_v6-v3-8c5ad256337976e7626d1bd32f265263/USER",
    "qcd4jetsht0600_ee_2022" :   "/QCD-4Jets_HT-600to800_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-Run3Summer22EEMiniAODv4-130X_mcRun3_2022_realistic_postEE_v6-v3-8c5ad256337976e7626d1bd32f265263/USER",
    "qcd4jetsht0800_ee_2022" :   "/QCD-4Jets_HT-800to1000_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-Run3Summer22EEMiniAODv4-130X_mcRun3_2022_realistic_postEE_v6-v1-8c5ad256337976e7626d1bd32f265263/USER",
    "qcd4jetsht1000_ee_2022" :   "/QCD-4Jets_HT-1000to1200_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-Run3Summer22EEMiniAODv4-130X_mcRun3_2022_realistic_postEE_v6-v1-8c5ad256337976e7626d1bd32f265263/USER",
    "qcd4jetsht1200_ee_2022" :   "/QCD-4Jets_HT-1200to1500_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-Run3Summer22EEMiniAODv4-130X_mcRun3_2022_realistic_postEE_v6-v1-8c5ad256337976e7626d1bd32f265263/USER",
    "qcd4jetsht1500_ee_2022" :   "/QCD-4Jets_HT-1500to2000_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-Run3Summer22EEMiniAODv4-130X_mcRun3_2022_realistic_postEE_v6-v1-8c5ad256337976e7626d1bd32f265263/USER",
    "qcd4jetsht2000_ee_2022" :   "/QCD-4Jets_HT-2000_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-Run3Summer22EEMiniAODv4-130X_mcRun3_2022_realistic_postEE_v6-v1-8c5ad256337976e7626d1bd32f265263/USER",
    "ttto4q_ee_2022"         :   "/TTto4Q_TuneCP5_13p6TeV_powheg-pythia8/aguven-Run3Summer22EEMiniAODv4-130X_mcRun3_2022_realistic_postEE_v6-v1-8c5ad256337976e7626d1bd32f265263/USER",
    "ttto2l2nu_ee_2022"      :   "/TTto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8/aguven-Run3Summer22EEMiniAODv4-130X_mcRun3_2022_realistic_postEE_v6-v1-8c5ad256337976e7626d1bd32f265263/USER",
    "tttolnu2q_ee_2022"      :   "/TTtoLNu2Q_TuneCP5_13p6TeV_powheg-pythia8/aguven-Run3Summer22EEMiniAODv4-130X_mcRun3_2022_realistic_postEE_v6-v4-8c5ad256337976e7626d1bd32f265263/USER"

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
config.JobType.psetName = '/afs/cern.ch/user/a/aguven/crab_submissions/CMSSW_13_0_16/src/SoftDisplacedVertices/CustomNanoAOD/configuration/MC_Run3Summer22EE_CustomNanoAOD.py'
config.JobType.maxMemoryMB = 4000
config.JobType.numCores = 2

config.Data.inputDataset = '{}'
config.Data.inputDBS = 'phys03'
config.Data.splitting = 'Automatic'
# config.Data.splitting = 'FileBased'
# config.Data.unitsPerJob = 30
config.Data.publication = True
config.Data.outputDatasetTag = 'Run3Summer22EECustomNanoAODv12-130X_mcRun3_2022_realistic_postEE_v6-v1'
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