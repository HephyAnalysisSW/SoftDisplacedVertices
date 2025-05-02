import subprocess

datasets = {
    # 'Zto2Nu-4Jets_HT-100to200_bpix':    '/Zto2Nu-4Jets_HT-100to200_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23BPixDRPremix-130X_mcRun3_2023_realistic_postBPix_v2-v2/AODSIM',
    # 'Zto2Nu-4Jets_HT-200to400_bpix':    '/Zto2Nu-4Jets_HT-200to400_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23BPixDRPremix-130X_mcRun3_2023_realistic_postBPix_v2-v2/AODSIM',
    # 'Zto2Nu-4Jets_HT-400to800_bpix':    '/Zto2Nu-4Jets_HT-400to800_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23BPixDRPremix-130X_mcRun3_2023_realistic_postBPix_v2-v2/AODSIM',
    # 'Zto2Nu-4Jets_HT-800to1500_bpix':   '/Zto2Nu-4Jets_HT-800to1500_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23BPixDRPremix-130X_mcRun3_2023_realistic_postBPix_v2-v2/AODSIM',
    # 'Zto2Nu-4Jets_HT-1500to2500_bpix':  '/Zto2Nu-4Jets_HT-1500to2500_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23BPixDRPremix-130X_mcRun3_2023_realistic_postBPix_v2-v2/AODSIM',
    # 'Zto2Nu-4Jets_HT-2500_bpix':        '/Zto2Nu-4Jets_HT-2500_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23BPixDRPremix-130X_mcRun3_2023_realistic_postBPix_v2-v3/AODSIM',

    # 'WtoLNu-4Jets_bpix':'/WtoLNu-4Jets_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23BPixDRPremix-130X_mcRun3_2023_realistic_postBPix_v2-v3/AODSIM',

    # 'QCD-4Jets_HT-40to70_bpix':      '/QCD-4Jets_HT-40to70_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23BPixDRPremix-130X_mcRun3_2023_realistic_postBPix_v2-v3/AODSIM',
    # 'QCD-4Jets_HT-70to100_bpix':     '/QCD-4Jets_HT-70to100_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23BPixDRPremix-130X_mcRun3_2023_realistic_postBPix_v2-v3/AODSIM',
    # 'QCD-4Jets_HT-100to200_bpix':    '/QCD-4Jets_HT-100to200_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23BPixDRPremix-130X_mcRun3_2023_realistic_postBPix_v2-v4/AODSIM',
    # 'QCD-4Jets_HT-200to400_bpix':    '/QCD-4Jets_HT-200to400_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23BPixDRPremix-130X_mcRun3_2023_realistic_postBPix_v2-v3/AODSIM',
    'QCD-4Jets_HT-400to600_bpix':    '/QCD-4Jets_HT-400to600_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23BPixDRPremix-130X_mcRun3_2023_realistic_postBPix_v2-v4/AODSIM',
    # 'QCD-4Jets_HT-600to800_bpix':    '/QCD-4Jets_HT-600to800_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23BPixDRPremix-130X_mcRun3_2023_realistic_postBPix_v2-v3/AODSIM',
    # 'QCD-4Jets_HT-800to1000_bpix':   '/QCD-4Jets_HT-800to1000_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23BPixDRPremix-130X_mcRun3_2023_realistic_postBPix_v2-v4/AODSIM',
    # 'QCD-4Jets_HT-1000to1200_bpix':  '/QCD-4Jets_HT-1000to1200_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23BPixDRPremix-130X_mcRun3_2023_realistic_postBPix_v2-v4/AODSIM',
    # 'QCD-4Jets_HT-1200to1500_bpix':  '/QCD-4Jets_HT-1200to1500_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23BPixDRPremix-130X_mcRun3_2023_realistic_postBPix_v2-v4/AODSIM',
    # 'QCD-4Jets_HT-1500to2000_bpix':  '/QCD-4Jets_HT-1500to2000_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23BPixDRPremix-130X_mcRun3_2023_realistic_postBPix_v2-v3/AODSIM',
    # 'QCD-4Jets_HT-2000_bpix':        '/QCD-4Jets_HT-2000_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23BPixDRPremix-130X_mcRun3_2023_realistic_postBPix_v2-v4/AODSIM',

    # 'TTto4Q_bpix':      '/TTto4Q_TuneCP5_13p6TeV_powheg-pythia8/Run3Summer23BPixDRPremix-130X_mcRun3_2023_realistic_postBPix_v2-v3/AODSIM',
    # 'TTtoLNu2Q_bpix':   '/TTtoLNu2Q_TuneCP5_13p6TeV_powheg-pythia8/Run3Summer23BPixDRPremix-130X_mcRun3_2023_realistic_postBPix_v2-v3/AODSIM',
    # 'TTto2L2Nu_bpix':   '/TTto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8/Run3Summer23BPixDRPremix-130X_mcRun3_2023_realistic_postBPix_v2-v3/AODSIM',
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
config.JobType.psetName = '/afs/cern.ch/user/a/aguven/crab_submissions/CMSSW_13_0_16/src/SoftDisplacedVertices/CustomMiniAOD/configuration/MC_Run3Summer23BPix_CustomMiniAOD.py'
config.JobType.maxMemoryMB = 4000
config.JobType.numCores = 2

config.Data.inputDataset = '{}'
config.Data.inputDBS = 'global'
config.Data.splitting = 'Automatic'
config.Data.publication = True
config.Data.outputDatasetTag = 'Run3Summer23BPixCustomMiniAODv4-130X_mcRun3_2023_realistic_postBPix_v2-v3'
# config.Data.partialDataset = True
# config.Data.ignoreLocality = True

# config.Site.whitelist=["T2_AT_Vienna"]
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

