import subprocess
import json
import time

dataset = "/JetMET0/Run2023B-19Dec2023-v1/AOD"

missingFiles = []

notpublished_json = "crab_projects/crab_20240808_163841/results/notPublishedLumis.json"

with open(notpublished_json) as f:
    run_lumi = json.load(f)
    for run, lumiList in run_lumi.items():
        print "-" * 80
        print run
        for lumiRange in lumiList:
            # nlumis = lumiRange[1] - lumiRange[0]
            # print lumiRange[0]
            # print lumiRange[1]
            # print range(lumiRange[0], lumiRange[1] + 1)
            for lumi in range(lumiRange[0], lumiRange[1] + 1):
                print lumi
                # print '-query=\"file dataset={} run={} lumi={}\"'.format(dataset, run, lumi)
                # subprocess.call('dasgoclient -query=\"file dataset={} run={} lumi={}\"'.format(dataset, run, lumi),
                #                 shell=True)
                p = subprocess.Popen('dasgoclient -query=\"file dataset={} run={} lumi={}\"'.format(dataset, run, lumi),
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
                p.wait()
                missingFile = p.stdout.read()
                if missingFile not in missingFiles:
                    missingFiles.append(missingFile)
                # print missingFiles
                # time.sleep(1)

with open("missingFiles.txt", "w") as mF:
    for missingFile in missingFiles:
        mF.write(missingFile)

