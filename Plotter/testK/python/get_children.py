import json
import subprocess

# Path to the JSON file
# json_file_path = "/users/alikaan.gueven/AOD_to_nanoAOD/CMSSW_13_0_16/src/SoftDisplacedVertices/Samples/json/MC_Run3Summer22.json"
json_file_path = "/users/alikaan.gueven/AOD_to_nanoAOD/CMSSW_13_0_16/src/SoftDisplacedVertices/Samples/json/Data_MET2022_20250620.json"

# Load the JSON data
with open(json_file_path, 'r') as file:
    data = json.load(file)

# Access the nested keys
datasets = data.get("CustomMiniAOD", {}).get("datasets", {})

# Iterate through the keys and values
for key, value in datasets.items():
    try:
        # Run the subprocess command
        result = subprocess.run(
            ["dasgoclient", f"-query=child dataset={value} instance=prod/phys03"],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"\"{key}\":\"{result.stdout.strip()}\",")
    except subprocess.CalledProcessError as e:
        print(f"Error while processing {key}: {e.stderr}")