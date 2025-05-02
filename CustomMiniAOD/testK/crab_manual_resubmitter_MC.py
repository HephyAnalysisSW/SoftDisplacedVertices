#!/usr/bin/python3
import subprocess
import os


def get_crabConfig(dataset, tag, lumiMask):
    crabConfig = ("import CRABClient \n"
                  "from CRABClient.UserUtilities import config  \n"

                  "config = config() \n"
                  "config.General.workArea = 'crab_projects' \n"
                  "config.General.transferOutputs = True \n"

                  "config.JobType.pluginName = 'Analysis' \n"
                  "config.JobType.psetName = '/afs/cern.ch/user/a/aguven/crab_submissions/CMSSW_13_0_16/src/SoftDisplacedVertices/CustomMiniAOD/configuration/MC_Run3Summer23BPix_CustomMiniAOD.py' \n"
                  "config.JobType.maxMemoryMB = 4000 \n"
                  "config.JobType.numCores = 2 \n"

                  "config.Data.inputDataset = '{}' \n"
                  "config.Data.inputDBS = 'global' \n"
                  "config.Data.splitting = 'Automatic' \n"
                  "config.Data.publication = True \n"
                  "config.Data.outputDatasetTag = '{}Run3Summer23BPixCustomMiniAODv4-130X_mcRun3_2023_realistic_postBPix_v2-v1' \n"
                  "config.Data.lumiMask = '{}' \n"
#                   "config.Data.partialDataset = False \n"

                  "config.Site.storageSite = 'T2_AT_Vienna' \n"
                 ).format(dataset, tag, lumiMask)
    with open("crabConfig.py", "w") as f:
        f.write(crabConfig)


resubmit_list = [
    ("/WtoLNu-4Jets_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23BPixDRPremix-130X_mcRun3_2023_realistic_postBPix_v2-v3/AODSIM",             "", "crab_20250307_141654"),
    ("/Zto2Nu-4Jets_HT-100to200_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23BPixDRPremix-130X_mcRun3_2023_realistic_postBPix_v2-v2/AODSIM", "", "crab_20250307_150338"),
    ("/Zto2Nu-4Jets_HT-2500_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23BPixDRPremix-130X_mcRun3_2023_realistic_postBPix_v2-v3/AODSIM",     "", "crab_20250307_143756"),
    ("/QCD-4Jets_HT-100to200_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23BPixDRPremix-130X_mcRun3_2023_realistic_postBPix_v2-v4/AODSIM",    "", "crab_20250307_151511"),
    ("/QCD-4Jets_HT-2000_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23BPixDRPremix-130X_mcRun3_2023_realistic_postBPix_v2-v4/AODSIM",        "", "crab_20250307_151037"),
    ("/TTto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8/Run3Summer23BPixDRPremix-130X_mcRun3_2023_realistic_postBPix_v2-v3/AODSIM",                     "", "crab_20250307_150811")
    ]


for dataset, tag, project in resubmit_list:
    print("-"*80)
    print(project)
    script_dir = os.path.dirname(os.path.realpath(__file__))
    proj_dir = os.path.join(script_dir, 'crab_projects/' + project)
    subprocess.call(['crab', 'report', proj_dir])
    
    notFinishedLumis = os.path.join(proj_dir, 'results/notFinishedLumis.json')
    get_crabConfig(dataset, tag, notFinishedLumis)
    subprocess.call(['crab', 'submit', '-c', 'crabConfig.py'])
    print("\n")
