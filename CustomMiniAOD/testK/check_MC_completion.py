import os
import json
import subprocess

def run_dasgoclient_summary(dataset, instance=""):
    """
    Runs dasgoclient with a summary query for the given dataset.
    If an instance is provided, it is added to the query.
    Returns the num_lumi value from the JSON output.
    """
    # Build the instance portion of the query if provided.
    instance_query = f" instance={instance}" if instance else ""
    cmd = f"dasgoclient -query='summary dataset={dataset}{instance_query}'"
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        output = result.stdout.strip()
        # Parse the JSON output which is expected to be a list containing one dictionary.
        data = json.loads(output)
        if data and isinstance(data, list) and "num_lumi" in data[0]:
            return data[0]["num_lumi"]
        else:
            print(f"Could not find 'num_lumi' for dataset: {dataset}")
            return None
    except subprocess.CalledProcessError as e:
        print(f"Error running dasgoclient for {dataset}: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON decode error for dataset {dataset}: {e}")
        return None

def main():
    # Load JSON file with dataset information.
    CMSSW_BASE = os.environ['CMSSW_BASE']
    SDV = os.path.join(CMSSW_BASE, 'src/SoftDisplacedVertices')
    with open(os.path.join(SDV, 'Samples/json/MC_Run3Summer22.json'), 'r') as f:
        data = json.load(f)
    
    # Retrieve the dataset dictionaries for AOD and CustomMiniAOD.
    aod_datasets = data.get("AOD", {}).get("datasets", {})
    custom_mini_aod_datasets = data.get("CustomMiniAOD", {}).get("datasets", {})

    # Iterate over each AOD dataset.
    for dataset_key, aod_dataset in aod_datasets.items():
        print(f"Processing dataset: {dataset_key}")
        
        # Retrieve num_lumi for the AOD dataset.
        aod_num_lumi = run_dasgoclient_summary(aod_dataset)
        if aod_num_lumi is None:
            print(f"  Failed to retrieve AOD summary for {dataset_key}\n")
            continue
        print(f"  AOD num_lumi: {aod_num_lumi}")
        
        # Check for a corresponding CustomMiniAOD dataset.
        custom_entry = custom_mini_aod_datasets.get(dataset_key)
        print(custom_entry)

        if custom_entry:
            custom_num_lumi = 0
            # If custom_entry is a list, sum the num_lumi from each dataset.
            if isinstance(custom_entry, list):
                for ds in custom_entry:
                    num = run_dasgoclient_summary(ds, instance="prod/phys03")
                    if num is None:
                        print(f"  Failed to retrieve summary for CustomMiniAOD dataset: {ds}")
                    else:
                        custom_num_lumi += num
            # Otherwise assume it's a single dataset string.
            else:
                custom_num_lumi = run_dasgoclient_summary(custom_entry, instance="prod/phys03")
                if custom_num_lumi is None:
                    print(f"  Failed to retrieve summary for CustomMiniAOD dataset: {custom_entry}")
                    continue
            
            print(f"  CustomMiniAOD total num_lumi: {custom_num_lumi}")
            
            # Compare the num_lumi values.
            if custom_num_lumi == aod_num_lumi:
                print("  Status: COMPLETED (100%).\n")
            else:
                _percent = float(custom_num_lumi) / float(aod_num_lumi) * 100
                print(f"  Status: NOT FINISHED ({_percent:.1f}%).\n")
        else:
            print("  Warning: No corresponding CustomMiniAOD dataset found.\n")


if __name__ == '__main__':
    main()
