#!/usr/bin/env python3
import subprocess
import re
import json


def run_crab_status(command_id):
    """
    Run the 'crab status' command for a given command id.
    Returns a dictionary with keys: finished, total, status, help_url, and dashboard_url.
    If a particular field is not found, its value will be None.
    """
    PROJ_DIR = "/users/alikaan.gueven/AOD_to_nanoAOD/CMSSW_13_0_16/src/SoftDisplacedVertices/CustomMiniAOD/testK/crab_projects"
    command = ["crab", "status", "-d", f"{PROJ_DIR}/{command_id}"]
    
    try:
        output = subprocess.check_output(command, universal_newlines=True)
    except subprocess.CalledProcessError as e:
        print(f"Error executing command for command id {command_id}: {e}")
        return {
            "finished": None,
            "total": None,
            "status": None,
            "help_url": None,
            "dashboard_url": None,
        }

    # Extract finished and total job numbers
    finished_total_match = re.search(r'finished\s+[\d.]+%\s+\((\d+)/(\d+)\)', output)
    if finished_total_match:
        finished = int(finished_total_match.group(1))
        total = int(finished_total_match.group(2))
    else:
        print(f"Could not parse job status for command id {command_id}.")
        finished, total = None, None

    # Extract CRAB server status
    status_match = re.search(r'^Status on the CRAB server:\s*(\S+)', output, re.MULTILINE)
    status = status_match.group(1) if status_match else None

    # Extract status on scheduler
    scheduler_match = re.search(r'^Status on the scheduler:\s*(\S+)', output, re.MULTILINE)
    scheduler = scheduler_match.group(1) if scheduler_match else None

    # Extract Task URL for HELP
    help_url_match = re.search(r'^Task URL to use for HELP:\s*(\S+)', output, re.MULTILINE)
    help_url = help_url_match.group(1) if help_url_match else None

    # Extract Dashboard monitoring URL
    dashboard_match = re.search(r'^Dashboard monitoring URL:\s*(\S+)', output, re.MULTILINE)
    dashboard_url = dashboard_match.group(1) if dashboard_match else None

    return {
        "finished": finished,
        "total": total,
        "status": status,
        "scheduler": scheduler,
        "help_url": help_url,
        "dashboard_url": dashboard_url,
    }

def main():
    datasets = [
    ("/WtoLNu-4Jets_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23DRPremix-130X_mcRun3_2023_realistic_v14-v3/AODSIM", "crab_20250306_183641"),
    ("/Zto2Nu-4Jets_HT-100to200_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23DRPremix-130X_mcRun3_2023_realistic_v14-v2/AODSIM", "crab_20250306_191254"),
    ("/Zto2Nu-4Jets_HT-200to400_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23DRPremix-130X_mcRun3_2023_realistic_v14-v2/AODSIM", "crab_20250306_184840"),
    ("/Zto2Nu-4Jets_HT-400to800_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23DRPremix-130X_mcRun3_2023_realistic_v14-v2/AODSIM", "crab_20250306_184920"),
    ("/Zto2Nu-4Jets_HT-800to1500_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23DRPremix-130X_mcRun3_2023_realistic_v14-v2/AODSIM", "crab_20250306_184345"),
    ("/Zto2Nu-4Jets_HT-1500to2500_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23DRPremix-130X_mcRun3_2023_realistic_v14-v2/AODSIM", "crab_20250306_182912"),
    ("/Zto2Nu-4Jets_HT-2500_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23DRPremix-130X_mcRun3_2023_realistic_v14-v3/AODSIM", "crab_20250306_182937"),
    ("/QCD-4Jets_HT-40to70_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23DRPremix-130X_mcRun3_2023_realistic_v14-v2/AODSIM", "crab_20250306_184115"),
    ("/QCD-4Jets_HT-70to100_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23DRPremix-130X_mcRun3_2023_realistic_v14-v2/AODSIM", "crab_20250306_191521"),
    ("/QCD-4Jets_HT-100to200_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23DRPremix-130X_mcRun3_2023_realistic_v14-v2/AODSIM", "crab_20250306_185149"),
    ("/QCD-4Jets_HT-200to400_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23DRPremix-130X_mcRun3_2023_realistic_v14-v2/AODSIM", "crab_20250306_190324"),
    ("/QCD-4Jets_HT-400to600_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23DRPremix-130X_mcRun3_2023_realistic_v14-v3/AODSIM", "crab_20250306_192224"),
    ("/QCD-4Jets_HT-600to800_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23DRPremix-130X_mcRun3_2023_realistic_v14-v2/AODSIM", "crab_20250306_192700"),
    ("/QCD-4Jets_HT-800to1000_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23DRPremix-130X_mcRun3_2023_realistic_v14-v2/AODSIM", "crab_20250306_190552"),
    ("/QCD-4Jets_HT-1000to1200_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23DRPremix-130X_mcRun3_2023_realistic_v14-v2/AODSIM", "crab_20250306_191749"),
    ("/QCD-4Jets_HT-1200to1500_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23DRPremix-130X_mcRun3_2023_realistic_v14-v2/AODSIM", "crab_20250306_190613"),
    ("/QCD-4Jets_HT-1500to2000_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23DRPremix-130X_mcRun3_2023_realistic_v14-v3/AODSIM", "crab_20250306_182957"),
    ("/QCD-4Jets_HT-2000_TuneCP5_13p6TeV_madgraphMLM-pythia8/Run3Summer23DRPremix-130X_mcRun3_2023_realistic_v14-v2/AODSIM", "crab_20250306_185851"),
    ("/TTto4Q_TuneCP5_13p6TeV_powheg-pythia8/Run3Summer23DRPremix-130X_mcRun3_2023_realistic_v14-v2/AODSIM", "crab_20250306_184613"),
    ("/TTto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8/Run3Summer23DRPremix-130X_mcRun3_2023_realistic_v14-v2/AODSIM", "crab_20250306_184900"),
    ("/TTtoLNu2Q_TuneCP5_13p6TeV_powheg-pythia8/Run3Summer23DRPremix-130X_mcRun3_2023_realistic_v14-v2/AODSIM", "crab_20250306_185416"),
]

    
    results = {}

    for dataset_name, command_id in datasets:
        print(f"Processing dataset {dataset_name} with command id {command_id}...")
        data = run_crab_status(command_id)
        results[dataset_name] = {
            "command_id": command_id,
            "finished": data["finished"],
            "total": data["total"],
            "status": data["status"],
            "scheduler": data["scheduler"],
            "help_url": data["help_url"],
            "dashboard_url": data["dashboard_url"]
        }

    # Save results to a JSON file.
    name = "crab_status_results.json"
    with open(name, "w") as json_file:
        json.dump(results, json_file, indent=4)
    
    print("Results saved to", name)

if __name__ == "__main__":
    main()
