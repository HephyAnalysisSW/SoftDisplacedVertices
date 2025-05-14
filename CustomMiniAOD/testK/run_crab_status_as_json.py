#!/usr/bin/env python3
import argparse
import json
import os
from CRABAPI.RawCommand import crabCommand


def check_crab_status(command_id):
    """Check CRAB job statuses for directories in the given index range."""
    proj_dir = "/users/alikaan.gueven/AOD_to_nanoAOD/CMSSW_13_0_16/src/SoftDisplacedVertices/CustomMiniAOD/testK/crab_projects"
    results = {}
    try:
        PROJ_DIR = "/users/alikaan.gueven/AOD_to_nanoAOD/CMSSW_13_0_16/src/SoftDisplacedVertices/CustomMiniAOD/testK/crab_projects"
        job_dir = os.path.join(PROJ_DIR, command_id)
        status = crabCommand("status", dir=job_dir)
        results[job_dir] = status  # Store the result in a dictionary
    except Exception as e:
        print(f"Error fetching status for {command_id}: {e}")
        results[job_dir] = {"error": str(e)}

    # Save results to a JSON file
    json_filename = "crab_status_results.json"
    with open(json_filename, "w") as json_file:
        json.dump(results, json_file, indent=4)

    print(f"Status results saved to: {json_filename}")

def main():
    datasets = [
    ("/WtoLNu-4Jets_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23DRPremix-130X_mcRun3_2023_realistic_v14-v3/AODSIM", "crab_20250306_183641"),
    # ("/Zto2Nu-4Jets_HT-100to200_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23DRPremix-130X_mcRun3_2023_realistic_v14-v2/AODSIM", "crab_20250306_191254"),
    # ("/Zto2Nu-4Jets_HT-200to400_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23DRPremix-130X_mcRun3_2023_realistic_v14-v2/AODSIM", "crab_20250306_184840"),
    # ("/Zto2Nu-4Jets_HT-400to800_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23DRPremix-130X_mcRun3_2023_realistic_v14-v2/AODSIM", "crab_20250306_184920"),
    # ("/Zto2Nu-4Jets_HT-800to1500_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23DRPremix-130X_mcRun3_2023_realistic_v14-v2/AODSIM", "crab_20250306_184345"),
    # ("/Zto2Nu-4Jets_HT-1500to2500_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23DRPremix-130X_mcRun3_2023_realistic_v14-v2/AODSIM", "crab_20250306_182912"),
    # ("/Zto2Nu-4Jets_HT-2500_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23DRPremix-130X_mcRun3_2023_realistic_v14-v3/AODSIM", "crab_20250306_182937"),
    # ("/QCD-4Jets_HT-40to70_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23DRPremix-130X_mcRun3_2023_realistic_v14-v2/AODSIM", "crab_20250306_184115"),
    # ("/QCD-4Jets_HT-70to100_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23DRPremix-130X_mcRun3_2023_realistic_v14-v2/AODSIM", "crab_20250306_191521"),
    # ("/QCD-4Jets_HT-100to200_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23DRPremix-130X_mcRun3_2023_realistic_v14-v2/AODSIM", "crab_20250306_185149"),
    # ("/QCD-4Jets_HT-200to400_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23DRPremix-130X_mcRun3_2023_realistic_v14-v2/AODSIM", "crab_20250306_190324"),
    # ("/QCD-4Jets_HT-400to600_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23DRPremix-130X_mcRun3_2023_realistic_v14-v3/AODSIM", "crab_20250306_192224"),
    # ("/QCD-4Jets_HT-600to800_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23DRPremix-130X_mcRun3_2023_realistic_v14-v2/AODSIM", "crab_20250306_192700"),
    # ("/QCD-4Jets_HT-800to1000_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23DRPremix-130X_mcRun3_2023_realistic_v14-v2/AODSIM", "crab_20250306_190552"),
    # ("/QCD-4Jets_HT-1000to1200_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23DRPremix-130X_mcRun3_2023_realistic_v14-v2/AODSIM", "crab_20250306_191749"),
    # ("/QCD-4Jets_HT-1200to1500_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23DRPremix-130X_mcRun3_2023_realistic_v14-v2/AODSIM", "crab_20250306_190613"),
    # ("/QCD-4Jets_HT-1500to2000_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23DRPremix-130X_mcRun3_2023_realistic_v14-v3/AODSIM", "crab_20250306_182957"),
    # ("/QCD-4Jets_HT-2000_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23DRPremix-130X_mcRun3_2023_realistic_v14-v2/AODSIM", "crab_20250306_185851"),
    # ("/TTto4Q_TuneCP5_13p6TeV_powheg-pythia8/Run3Summer23DRPremix-130X_mcRun3_2023_realistic_v14-v2/AODSIM", "crab_20250306_184613"),
    # ("/TTto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8/Run3Summer23DRPremix-130X_mcRun3_2023_realistic_v14-v2/AODSIM", "crab_20250306_184900"),
    # ("/TTtoLNu2Q_TuneCP5_13p6TeV_powheg-pythia8/Run3Summer23DRPremix-130X_mcRun3_2023_realistic_v14-v2/AODSIM", "crab_20250306_185416"),
]
    results = {}
    for dataset_name, command_id in datasets:
        print(f"Processing dataset {dataset_name} with command id {command_id}...")
        check_crab_status(command_id)


if __name__ == "__main__":
    main()