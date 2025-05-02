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
    PROJ_DIR = "/afs/cern.ch/user/a/aguven/crab_submissions/CMSSW_13_0_16/src/SoftDisplacedVertices/CustomMiniAOD/testK/crab_projects"
    command = ["crab", "status", "-d", f"{PROJ_DIR}/{command_id}"]
    
    try:
        output = subprocess.check_output(command, universal_newlines=True)
    except subprocess.CalledProcessError as e:
        print(f"Error executing command for command id {command_id}: {e}")
        return {
            "finished": None,
            "total": None,
            "status": None,
            "outputDatasetTag": None,
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

    # Extract output dataset
    outputDatasetTag_match = re.search(r'^Output dataset:\s*(\S+)', output, re.MULTILINE)
    outputDatasetTag = status_match.group(1) if status_match else None

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
        ()
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
            "outputDatasetTag": data["outputDatasetTag"],
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
