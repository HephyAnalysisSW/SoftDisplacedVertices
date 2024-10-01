#!/bin/bash

export SCRAM_ARCH=slc7_amd64_gcc700
source /cvmfs/cms.cern.ch/cmsset_default.sh
n=EVENTCOUNT
HOME="$PWD"

if [ ! -r CMSSW_10_6_30/src ]; then
  scram p CMSSW CMSSW_10_6_30
fi
cd CMSSW_10_6_30/src
mkdir -p Configuration/GenProduction/python/
cp $HOME/fragment.py Configuration/GenProduction/python/fragment.py
cp $HOME/random.py Configuration/GenProduction/python/random.py
eval `scram runtime -sh`
scram b

cmsDriver.py Configuration/GenProduction/python/fragment.py --python_filename LHEGEN-cfg.py --eventcontent RAWSIM,LHE --customise Configuration/DataProcessing/Utils.addMonitoring --datatier GEN,LHE --fileout file:LHEGEN.root --conditions 106X_upgrade2018_realistic_v4 --beamspot Realistic25ns13TeVEarly2018Collision --step LHE,GEN --geometry DB:Extended --era Run2_2018 --no_exec --mc --customise Configuration/GenProduction/random.random -n $n

cmsDriver.py  --python_filename SIM-cfg.py --eventcontent RAWSIM --customise Configuration/DataProcessing/Utils.addMonitoring --datatier GEN-SIM --fileout file:SIM.root --conditions 106X_upgrade2018_realistic_v11_L1v1 --beamspot Realistic25ns13TeVEarly2018Collision --step SIM --geometry DB:Extended --filein file:LHEGEN.root --era Run2_2018 --runUnscheduled --no_exec --mc -n $n

cmsDriver.py  --python_filename PREMIX-cfg.py --eventcontent PREMIXRAW --customise Configuration/DataProcessing/Utils.addMonitoring --datatier GEN-SIM-DIGI --fileout file:PREMIX.root --pileup_input "dbs:/Neutrino_E-10_gun/RunIISummer20ULPrePremix-UL18_106X_upgrade2018_realistic_v11_L1v1-v2/PREMIX" --conditions 106X_upgrade2018_realistic_v11_L1v1 --step DIGI,DATAMIX,L1,DIGI2RAW --procModifiers premix_stage2 --geometry DB:Extended --filein file:SIM.root --datamix PreMix --era Run2_2018 --runUnscheduled --no_exec --mc -n $n

cd ../..
if [ ! -r CMSSW_10_2_16_UL/src ]; then
  scram p CMSSW CMSSW_10_2_16_UL
fi
cd CMSSW_10_2_16_UL/src
eval `scram runtime -sh`
scram b

cmsDriver.py  --python_filename HLT-cfg.py --eventcontent RAWSIM --customise Configuration/DataProcessing/Utils.addMonitoring --datatier GEN-SIM-RAW --fileout file:HLT.root --conditions 102X_upgrade2018_realistic_v15 --customise_commands 'process.source.bypassVersionCheck = cms.untracked.bool(True)' --step HLT:2018v32 --geometry DB:Extended --filein file:PREMIX.root --era Run2_2018 --no_exec --mc -n $n

cd ../..
cd CMSSW_10_6_30/src
eval `scramv1 runtime -sh`

cmsDriver.py  --python_filename AODSIM-cfg.py --eventcontent AODSIM --customise Configuration/DataProcessing/Utils.addMonitoring --datatier AODSIM --fileout file:AODSIM.root --conditions 106X_upgrade2018_realistic_v11_L1v1 --step RAW2DIGI,L1Reco,RECO,RECOSIM,EI --geometry DB:Extended --filein file:HLT.root --era Run2_2018 --runUnscheduled --no_exec --mc -n $n

cmsDriver.py  --python_filename MINIAODSIM-cfg.py --eventcontent MINIAODSIM --customise Configuration/DataProcessing/Utils.addMonitoring --datatier MINIAODSIM --fileout file:MINIAODSIM.root --conditions 106X_upgrade2018_realistic_v16_L1v1 --step PAT --procModifiers run2_miniAOD_UL --geometry DB:Extended --filein file:AODSIM.root --era Run2_2018 --runUnscheduled --no_exec --mc -n $n

cmsDriver.py  --python_filename NANOAODSIM-cfg.py --eventcontent NANOAODSIM --customise Configuration/DataProcessing/Utils.addMonitoring --datatier NANOAODSIM --fileout file:NANOAODSIM.root --conditions 106X_upgrade2018_realistic_v16_L1v1 --step NANO --filein file:MINIAODSIM.root --era Run2_2018 --no_exec --mc -n $n

cd $HOME

cp CMSSW_10_6_30/src/LHEGEN-cfg.py LHEGEN-cfg.py
cp CMSSW_10_6_30/src/SIM-cfg.py SIM-cfg.py
cp CMSSW_10_6_30/src/PREMIX-cfg.py PREMIX-cfg.py
cp CMSSW_10_2_16_UL/src/HLT-cfg.py HLT-cfg.py
cp CMSSW_10_6_30/src/AODSIM-cfg.py AODSIM-cfg.py
cp CMSSW_10_6_30/src/AODSIM-cfg.py AODSIM-IVF1-cfg.py
config_content=$(cat <<EOL
#####################################

process.inclusiveVertexFinder.minPt = cms.double(0.5)
process.inclusiveVertexFinder.minHits = cms.uint32(6)
process.inclusiveVertexFinder.maximumLongitudinalImpactParameter = cms.double(20.)
process.inclusiveVertexFinder.vertexMinAngleCosine = cms.double(0.00001)

process.trackVertexArbitrator.dRCut = cms.double(1.57)
process.trackVertexArbitrator.distCut = cms.double(0.1)
process.trackVertexArbitrator.trackMinPixels = cms.int32(0)

#####################################
EOL
)
echo "$config_content" >> "AODSIM-IVF1-cfg.py"
cp CMSSW_10_6_30/src/MINIAODSIM-cfg.py MINIAODSIM-cfg.py
cp CMSSW_10_6_30/src/NANOAODSIM-cfg.py NANOAODSIM-cfg.py

rm -r CMSSW_10_6_30
rm -r CMSSW_10_2_16_UL