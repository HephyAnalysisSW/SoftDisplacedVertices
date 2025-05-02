import subprocess
import textwrap
import time

datasets = {
    # "wjetstolnu4jets_bpix_2023":   ["/WtoLNu-4Jets_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-Run3Summer23BPixCustomMiniAODv4-130X_mcRun3_2023_realistic_postBPix_v2-v1-298548b3858e6f1d013555f737950efb/USER",
    #                                 "/WtoLNu-4Jets_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-Run3Summer23BPixCustomMiniAODv4-130X_mcRun3_2023_realistic_postBPix_v2-v1-327299388cefa102c805243eb816c186/USER"],
    # "zto2nu4jetsht0100_bpix_2023": ["/Zto2Nu-4Jets_HT-100to200_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-Run3Summer23BPixCustomMiniAODv4-130X_mcRun3_2023_realistic_postBPix_v2-v1-298548b3858e6f1d013555f737950efb/USER",
    #                                 "/Zto2Nu-4Jets_HT-100to200_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-Run3Summer23BPixCustomMiniAODv4-130X_mcRun3_2023_realistic_postBPix_v2-v1-327299388cefa102c805243eb816c186/USER"],
    # "zto2nu4jetsht0200_bpix_2023": "/Zto2Nu-4Jets_HT-200to400_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-Run3Summer23BPixCustomMiniAODv4-130X_mcRun3_2023_realistic_postBPix_v2-v1-327299388cefa102c805243eb816c186/USER",
    # "zto2nu4jetsht0400_bpix_2023": "/Zto2Nu-4Jets_HT-400to800_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-Run3Summer23BPixCustomMiniAODv4-130X_mcRun3_2023_realistic_postBPix_v2-v1-298548b3858e6f1d013555f737950efb/USER",
    # "zto2nu4jetsht0800_bpix_2023": "/Zto2Nu-4Jets_HT-800to1500_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-Run3Summer23BPixCustomMiniAODv4-130X_mcRun3_2023_realistic_postBPix_v2-v1-298548b3858e6f1d013555f737950efb/USER",
    # "zto2nu4jetsht1500_bpix_2023": "/Zto2Nu-4Jets_HT-1500to2500_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-Run3Summer23BPixCustomMiniAODv4-130X_mcRun3_2023_realistic_postBPix_v2-v1-298548b3858e6f1d013555f737950efb/USER",
    # "zto2nu4jetsht2500_bpix_2023": ["/Zto2Nu-4Jets_HT-2500_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-Run3Summer23BPixCustomMiniAODv4-130X_mcRun3_2023_realistic_postBPix_v2-v1-298548b3858e6f1d013555f737950efb/USER",
    #                                 "/Zto2Nu-4Jets_HT-2500_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-Run3Summer23BPixCustomMiniAODv4-130X_mcRun3_2023_realistic_postBPix_v2-v1-327299388cefa102c805243eb816c186/USER"],
    # "qcd4jetsht0040_bpix_2023" :   "/QCD-4Jets_HT-40to70_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-Run3Summer23BPixCustomMiniAODv4-130X_mcRun3_2023_realistic_postBPix_v2-v1-298548b3858e6f1d013555f737950efb/USER",
    # "qcd4jetsht0070_bpix_2023" :   "/QCD-4Jets_HT-70to100_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-Run3Summer23BPixCustomMiniAODv4-130X_mcRun3_2023_realistic_postBPix_v2-v1-298548b3858e6f1d013555f737950efb/USER",
    # "qcd4jetsht0100_bpix_2023" :   ["/QCD-4Jets_HT-100to200_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-Run3Summer23BPixCustomMiniAODv4-130X_mcRun3_2023_realistic_postBPix_v2-v1-298548b3858e6f1d013555f737950efb/USER",
    #                                 "/QCD-4Jets_HT-100to200_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-Run3Summer23BPixCustomMiniAODv4-130X_mcRun3_2023_realistic_postBPix_v2-v1-327299388cefa102c805243eb816c186/USER"],
    # "qcd4jetsht0200_bpix_2023" :   "/QCD-4Jets_HT-200to400_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-Run3Summer23BPixCustomMiniAODv4-130X_mcRun3_2023_realistic_postBPix_v2-v1-298548b3858e6f1d013555f737950efb/USER",
    # "qcd4jetsht0400_bpix_2023" :   "/QCD-4Jets_HT-400to600_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-Run3Summer23BPixCustomMiniAODv4-130X_mcRun3_2023_realistic_postBPix_v2-v3-327299388cefa102c805243eb816c186/USER",
    "qcd4jetsht0600_bpix_2023" :   "/QCD-4Jets_HT-600to800_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-Run3Summer23BPixCustomMiniAODv4-130X_mcRun3_2023_realistic_postBPix_v2-v3-327299388cefa102c805243eb816c186/USER",
    # "qcd4jetsht0800_bpix_2023" :   "/QCD-4Jets_HT-800to1000_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-Run3Summer23BPixCustomMiniAODv4-130X_mcRun3_2023_realistic_postBPix_v2-v1-327299388cefa102c805243eb816c186/USER",
    # "qcd4jetsht1000_bpix_2023" :   "/QCD-4Jets_HT-1000to1200_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-Run3Summer23BPixCustomMiniAODv4-130X_mcRun3_2023_realistic_postBPix_v2-v1-298548b3858e6f1d013555f737950efb/USER",
    # "qcd4jetsht1200_bpix_2023" :   "/QCD-4Jets_HT-1200to1500_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-Run3Summer23BPixCustomMiniAODv4-130X_mcRun3_2023_realistic_postBPix_v2-v1-298548b3858e6f1d013555f737950efb/USER",
    # "qcd4jetsht1500_bpix_2023" :   "/QCD-4Jets_HT-1500to2000_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-Run3Summer23BPixCustomMiniAODv4-130X_mcRun3_2023_realistic_postBPix_v2-v1-327299388cefa102c805243eb816c186/USER",
    # "qcd4jetsht2000_bpix_2023" :   ["/QCD-4Jets_HT-2000_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-Run3Summer23BPixCustomMiniAODv4-130X_mcRun3_2023_realistic_postBPix_v2-v1-298548b3858e6f1d013555f737950efb/USER",
    #                                 "/QCD-4Jets_HT-2000_TuneCP5_13p6TeV_madgraphMLM-pythia8/aguven-Run3Summer23BPixCustomMiniAODv4-130X_mcRun3_2023_realistic_postBPix_v2-v1-327299388cefa102c805243eb816c186/USER"],
    # "ttto4q_bpix_2023"         :   "/TTto4Q_TuneCP5_13p6TeV_powheg-pythia8/aguven-Run3Summer23BPixCustomMiniAODv4-130X_mcRun3_2023_realistic_postBPix_v2-v1-298548b3858e6f1d013555f737950efb/USER",
    # "ttto2lnu_bpix_2023"       :   "/TTtoLNu2Q_TuneCP5_13p6TeV_powheg-pythia8/aguven-Run3Summer23BPixCustomMiniAODv4-130X_mcRun3_2023_realistic_postBPix_v2-v1-298548b3858e6f1d013555f737950efb/USER",
    # "tttolnu2q_bpix_2023"      :   ["/TTto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8/aguven-Run3Summer23BPixCustomMiniAODv4-130X_mcRun3_2023_realistic_postBPix_v2-v1-298548b3858e6f1d013555f737950efb/USER",
    #                                 "/TTto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8/aguven-Run3Summer23BPixCustomMiniAODv4-130X_mcRun3_2023_realistic_postBPix_v2-v1-327299388cefa102c805243eb816c186/USER"]
}

def getConfig(inputDataset):
    crabConfig = textwrap.dedent("""\
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
        config.Data.outputDatasetTag = 'Run3Summer23BPixNanoAODv12-130X_mcRun3_2023_realistic_postBPix_v2-v2'

        config.Site.storageSite = "T2_AT_Vienna"
    """.format(inputDataset))
    return crabConfig

def runConfig(config_str):
    with open("crabConfig.py", "w") as f:
        f.write(config_str)
    subprocess.call(['crab', 'submit', '-c', 'crabConfig.py'])

def main():
    for tag, inputDataset in datasets.items():
        if isinstance(inputDataset, str):
            inputDataset = [inputDataset]
        elif isinstance(inputDataset, list):
            pass
        
        for dataset in inputDataset:
            print(dataset, '\n')
            crabConfig = getConfig(dataset)
            # print(crabConfig)
            runConfig(crabConfig)
            # time.sleep(5)


if __name__ == "__main__":
    main()