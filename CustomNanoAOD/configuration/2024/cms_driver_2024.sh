#!/bin/bash -x

# MC
# ------------------------------------------------------------------------


declare -A MC_GT
MC_GT["Run3Summer24"]="150X_mcRun3_2024_realistic_v2"


declare -A MC_ERA
MC_ERA["Run3Summer24"]="Run3_2024"


for era in "Run3Summer24"
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


# DATA
# ------------------------------------------------------------------------

declare -A DATA_GT
DATA_GT["Run2024"]="150X_dataRun3_v2"

declare -A DATA_ERA
DATA_ERA["Run2024"]="Run3_2024"

for era in "Run2024"
do
    cmsDriver.py --python_filename "Data_${era}_CustomNanoAOD.py" \
        --filein "file:MiniAOD.root" \
        --fileout "NanoAOD.root" \
        --step NANO \
        --eventcontent NANOAOD \
        --datatier NANOAOD \
        --customise Configuration/DataProcessing/RecoTLR.customisePostEra_Run3 \
        --customise Configuration/DataProcessing/Utils.addMonitoring           \
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