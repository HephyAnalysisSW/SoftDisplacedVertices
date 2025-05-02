import subprocess

datasets = {
    # 'WtoLNu-4Jets':                 '/WtoLNu-4Jets_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-WtoLNu-4Jets-d9d4a8997533295ad2643cfe4fc69981/USER',

    # 'Zto2Nu-4Jets_HT-100to200':     '/Zto2Nu-4Jets_HT-100to200_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-Zto2Nu-4Jets_HT-100to200-d9d4a8997533295ad2643cfe4fc69981/USER',
    # 'Zto2Nu-4Jets_HT-200to400':     '/Zto2Nu-4Jets_HT-200to400_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-Zto2Nu-4Jets_HT-200to400-d9d4a8997533295ad2643cfe4fc69981/USER',
    # 'Zto2Nu-4Jets_HT-400to800':     '/Zto2Nu-4Jets_HT-400to800_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-Zto2Nu-4Jets_HT-400to800-d9d4a8997533295ad2643cfe4fc69981/USER',
    # 'Zto2Nu-4Jets_HT-800to1500':    '/Zto2Nu-4Jets_HT-800to1500_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-Zto2Nu-4Jets_HT-800to1500-d9d4a8997533295ad2643cfe4fc69981/USER',
    # 'Zto2Nu-4Jets_HT-1500to2500':   '/Zto2Nu-4Jets_HT-1500to2500_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-Zto2Nu-4Jets_HT-1500to2500-d9d4a8997533295ad2643cfe4fc69981/USER',
    # 'Zto2Nu-4Jets_HT-2500':         '/Zto2Nu-4Jets_HT-2500_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-Zto2Nu-4Jets_HT-2500-d9d4a8997533295ad2643cfe4fc69981/USER',

    # 'QCD-4Jets_HT-40to70':          '/QCD-4Jets_HT-40to70_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-QCD-4Jets_HT-40to70-d9d4a8997533295ad2643cfe4fc69981/USER',
    # 'QCD-4Jets_HT-70to100':         '/QCD-4Jets_HT-70to100_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-QCD-4Jets_HT-70to100-d9d4a8997533295ad2643cfe4fc69981/USER',
    # 'QCD-4Jets_HT-100to200':        '/QCD-4Jets_HT-100to200_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-QCD-4Jets_HT-100to200-d9d4a8997533295ad2643cfe4fc69981/USER',
    # 'QCD-4Jets_HT-200to400':        '/QCD-4Jets_HT-200to400_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-QCD-4Jets_HT-200to400-90a90d443b97ea2ceb6d49de64adc934/USER',
    # 'QCD-4Jets_HT-400to600':        '/QCD-4Jets_HT-400to600_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-QCD-4Jets_HT-400to600-d9d4a8997533295ad2643cfe4fc69981/USER',
    # 'QCD-4Jets_HT-600to800':        '/QCD-4Jets_HT-600to800_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-QCD-4Jets_HT-600to800-d9d4a8997533295ad2643cfe4fc69981/USER',
    # 'QCD-4Jets_HT-800to1000':       '/QCD-4Jets_HT-800to1000_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-QCD-4Jets_HT-800to1000-d9d4a8997533295ad2643cfe4fc69981/USER',
    # 'QCD-4Jets_HT-1000to1200':      '/QCD-4Jets_HT-1000to1200_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-QCD-4Jets_HT-1000to1200-d9d4a8997533295ad2643cfe4fc69981/USER',
    # 'QCD-4Jets_HT-1200to1500':      '/QCD-4Jets_HT-1200to1500_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-QCD-4Jets_HT-1200to1500-d9d4a8997533295ad2643cfe4fc69981/USER',
    # 'QCD-4Jets_HT-1500to2000':      '/QCD-4Jets_HT-1500to2000_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-QCD-4Jets_HT-1500to2000-d9d4a8997533295ad2643cfe4fc69981/USER',
    # 'QCD-4Jets_HT-2000':            '/QCD-4Jets_HT-2000_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-QCD-4Jets_HT-2000-d9d4a8997533295ad2643cfe4fc69981/USER',

    # 'TTto4Q':                       '/TTto4Q_TuneCP5_13p6TeV_powheg-pythia8/aguven-TTto4Q-d9d4a8997533295ad2643cfe4fc69981/USER',
    # 'TTtoLNu2Q':                    '/TTtoLNu2Q_TuneCP5_13p6TeV_powheg-pythia8/aguven-TTtoLNu2Q-d9d4a8997533295ad2643cfe4fc69981/USER',
    # 'TTto2L2Nu':                    '/TTto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8/aguven-TTto2L2Nu-d9d4a8997533295ad2643cfe4fc69981/USER',
    

    # Addition (NOT DUPLICATE!)
    # 'WtoLNu-4Jets':                 '/WtoLNu-4Jets_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-WtoLNu-4Jets-90a90d443b97ea2ceb6d49de64adc934/USER',
    # 'QCD-4Jets_HT-70to100':         '/QCD-4Jets_HT-70to100_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-QCD-4Jets_HT-70to100-90a90d443b97ea2ceb6d49de64adc934/USER',
    # 'QCD-4Jets_HT-100to200':        '/QCD-4Jets_HT-100to200_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-QCD-4Jets_HT-100to200-90a90d443b97ea2ceb6d49de64adc934/USER',
    # 'QCD-4Jets_HT-400to600':        '/QCD-4Jets_HT-400to600_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-QCD-4Jets_HT-400to600-90a90d443b97ea2ceb6d49de64adc934/USER',
    'TTto4Q':                       '/TTto4Q_TuneCP5_13p6TeV_powheg-pythia8/aguven-TTto4Q-90a90d443b97ea2ceb6d49de64adc934/USER',
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
config.JobType.psetName = '/afs/cern.ch/user/a/aguven/crab_submissions/CMSSW_13_0_16/src/SoftDisplacedVertices/CustomNanoAOD/configuration/MC_Run3Summer23_CustomNanoAOD.py'
config.JobType.maxMemoryMB = 4000
config.JobType.numCores = 2

config.Data.inputDataset = '{}'
config.Data.inputDBS = 'phys03'
config.Data.splitting = 'Automatic'
config.Data.publication = True
config.Data.outputDatasetTag = 'Run3Summer23CustomNanoAODv12-130X_mcRun3_2023_realistic_v14-v2'
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

# crab_20250326_140211