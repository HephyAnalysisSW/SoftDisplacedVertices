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
                  "config.JobType.psetName = '/afs/cern.ch/user/a/aguven/crab_submissions/CMSSW_13_0_16/src/SoftDisplacedVertices/CustomMiniAOD/configuration/Data_Run2023_CustomMiniAOD.py' \n"
                  "config.JobType.maxMemoryMB = 4000 \n"
                  "config.JobType.numCores = 2 \n"

                  "config.Data.inputDataset = '{}' \n"
                  # "config.Data.userInputFiles = '/store/data/Run2023D/JetMET1/AOD/19Dec2023-v1/2560000/c58f223d-4c0a-4612-84b4-42218c1f51a0.root'{} \n"
                  # "config.Data.outputPrimaryDataset = 'JetMET1' \n"
                  "config.Data.inputDBS = 'global' \n"
                  "config.Data.splitting = 'LumiBased' \n"
                  "config.Data.unitsPerJob = 1 \n"
                  "config.Data.publication = True \n"
                  "config.Data.outputDatasetTag = '{}_mini_v1' \n"
                  "config.Data.lumiMask = '{}' \n"
                  "config.Data.partialDataset = False \n"

                  "config.Site.storageSite = 'T2_AT_Vienna' \n"
                 ).format(dataset, tag, lumiMask)
    with open("crabConfig.py", "w") as f:
        f.write(crabConfig)


resubmit_list = [
    # ("", "Run2023D1", "crab_20250306_142547"),
    ("/JetMET1/Run2023D-19Dec2023-v1/AOD", "Run2023D1", "crab_20250318_111139"),
    ("/JetMET1/Run2023B-19Dec2023-v1/AOD", "Run2023B1", "crab_20250318_111204"),
    ("/JetMET0/Run2023C-19Dec2023-v1/AOD", "Run2023C0", "crab_20250318_111229"),
    ("/JetMET1/Run2023C-19Dec2023-v1/AOD", "Run2023C1", "crab_20250318_111253")
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
