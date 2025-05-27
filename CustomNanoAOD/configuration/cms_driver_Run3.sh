#!/bin/bash -x

declare -A MC_GT
MC_GT["Run3Summer22"]="130X_mcRun3_2022_realistic_v5"
MC_GT["Run3Summer22EE"]="130X_mcRun3_2022_realistic_postEE_v6"
MC_GT["Run3Summer23"]="130X_mcRun3_2023_realistic_v14"
MC_GT["Run3Summer23BPix"]="130X_mcRun3_2023_realistic_postBPix_v2"


declare -A MC_ERA
MC_ERA["Run3Summer22"]="Run3"
MC_ERA["Run3Summer22EE"]="Run3"
MC_ERA["Run3Summer23"]="Run3_2023"
MC_ERA["Run3Summer23BPix"]="Run3_2023"


declare -A DATA_GT
DATA_GT["Run2022"]="130X_dataRun3_HcalSiPM_v1"
DATA_GT["Run2023"]="130X_dataRun3_Prompt_HcalSiPM_v1"

declare -A DATA_ERA
DATA_ERA["Run2022"]="Run3"
DATA_ERA["Run2023"]="Run3"

for era in "Run3Summer22" "Run3Summer22EE" # "Run3Summer23" "Run3Summer23BPix"
do
    cmsDriver.py CustomNanoAOD --python_filename "MC_${era}_CustomNanoAOD.py" \
        --filein "file:MiniAOD.root" \
        --fileout "NanoAOD.root" \
        --step NANO \
        --scenario pp \
        --eventcontent NANOAODSIM \
        --datatier NANOAODSIM \
        --customise Configuration/DataProcessing/Utils.addMonitoring           \
        --customise SoftDisplacedVertices/CustomNanoAOD/nanoAOD_cff.nanoAOD_customise_SoftDisplacedVerticesMC \
        --customise_commands="process.add_(cms.Service('InitRootHandlers', EnableIMT = cms.untracked.bool(False)));process.MessageLogger.cerr.FwkReport.reportEvery=1000" \
        --conditions "${MC_GT[$era]}" \
        --geometry DB:Extended \
        --era "${MC_ERA[$era]}" \
        --no_exec \
        -n -1 \
        --nThreads 2 \
        --mc
done

for era in "Run2022" # "Run2023"
do
    cmsDriver.py --python_filename "Data_${era}_CustomNanoAOD.py" \
        --filein "file:MiniAOD.root" \
        --fileout "NanoAOD.root" \
        --step NANO \
        --eventcontent NANOAOD \
        --datatier NANOAOD \
        --customise Configuration/DataProcessing/RecoTLR.customisePostEra_Run3 \
        --customise Configuration/DataProcessing/Utils.addMonitoring           \
        --customise PhysicsTools/NanoAOD/nano_cff.nanoL1TrigObjCustomize       \
        --customise SoftDisplacedVertices/CustomNanoAOD/nanoAOD_cff.nanoAOD_customise_SoftDisplacedVertices \
        --customise_commands="process.add_(cms.Service('InitRootHandlers', EnableIMT = cms.untracked.bool(False)));process.MessageLogger.cerr.FwkReport.reportEvery=1000" \
        --conditions "${DATA_GT[$era]}" \
        --era "${DATA_ERA[$era]}" \
        --scenario pp \
        --no_exec \
        -n -1 \
        --nThreads 2 \
        --data
done