import subprocess
import json
import time
import os

dataset = "/JetMET/Run2022F-v1/RAW"
project = 'crab_20250513_120736'




# Run crab report 
# ---------------------------------------------------------
script_dir = os.path.dirname(os.path.realpath(__file__))
proj_dir = os.path.join(script_dir, 'crab_projects/' + project)

subprocess.call(['crab', 'report', proj_dir])
notfinished_json = os.path.join(proj_dir, "results/notFinishedLumis.json")
missingFiles = []

# Query dasgoclient
# ---------------------------------------------------------
with open(notfinished_json) as f:
    run_lumi = json.load(f)
    for run, lumiList in run_lumi.items():
        print("-" * 80)
        print(run)
        for lumiRange in lumiList:
            for lumi in range(lumiRange[0], lumiRange[1] + 1):
                print(lumi)
                p = subprocess.Popen('dasgoclient -query=\"file dataset={} run={} lumi={}\"'.format(dataset, run, lumi),
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

                stdout, stderr = p.communicate()  # This waits for the process and reads both outputs
                missingFile = stdout.decode('utf-8')
                if missingFile not in missingFiles:
                    missingFiles.append(missingFile)
                # print missingFiles
                # time.sleep(1)

with open("missingFiles.txt", "w") as mF:
    for missingFile in missingFiles:
        mF.write(missingFile)

