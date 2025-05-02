import json
import subprocess
from FWCore.PythonUtilities.LumiList import LumiList
# >>> pwd
# /users/alikaan.gueven/Production/CMSSW_10_6_28/src/SoftDisplacedVertices/CustomMiniAOD/testK/2017_production

# GOLDEN_JSON = 'https://cms-service-dqmdc.web.cern.ch/CAF/certification/Collisions17/13TeV/Legacy_2017/Cert_294927-306462_13TeV_UL2017_Collisions17_GoldenJSON.txt'

lumistoProcess = {
    'Run2023B0' : 'crab_20250306_143730',
    'Run2023B1' : 'crab_20250306_143255',
    'Run2023C0' : 'crab_20250306_143959',
    'Run2023C1' : 'crab_20250306_144436',
    'Run2023D0' : 'crab_20250306_142818',
    'Run2023D1' : 'crab_20250306_142547',
}


processedLumis = {
    'Run2023B0' : ['crab_20250306_143730', ],                                                   # DONE
    'Run2023B1' : ['crab_20250306_143255', 'crab_20250318_111204', ],
    'Run2023C0' : ['crab_20250306_143959', 'crab_20250314_123822', 'crab_20250318_111229', 'crab_20250318_122757'],
    'Run2023C1' : ['crab_20250306_144436', 'crab_20250314_123855', 'crab_20250318_111253', 'crab_20250318_122820'],
    'Run2023D0' : ['crab_20250306_142818', ],                                                   # DONE
    'Run2023D1' : ['crab_20250306_142547', 'crab_20250318_111139', 'crab_20250318_122656']
}


for tag, proj_dirs in processedLumis.items():
    for i in proj_dirs:
        subprocess.call(['crab', 'report', f"crab_projects/{i}"])
    to_process = LumiList(filename="crab_projects/{}/results/lumisToProcess.json".format(lumistoProcess[tag]))
    residue = to_process
    for proj_dir in proj_dirs:
        processed = LumiList(filename="crab_projects/{}/results/processedLumis.json".format(proj_dir))
        residue = residue - processed
    print(tag)
    print(residue)
    print('-'*80)

