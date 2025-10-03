#!/bin/bash -x

# MC
# ------------------------------------------------------------------------


declare -A MC_GT
MC_GT["Run3Summer24"]="150X_mcRun3_2024_realistic_v2"


declare -A MC_ERA
MC_ERA["Run3Summer24"]="Run3_2024"



for era in "Run3Summer24"
do
    cmsDriver.py CustomMiniAOD --python_filename "MC_${era}_CustomMiniAOD.py" \
        --filein "file:AOD.root" \
        --fileout "MiniAOD.root" \
        --step PAT \
        --eventcontent MINIAODSIM \
        --datatier MINIAODSIM \
        --customise Configuration/DataProcessing/RecoTLR.customisePostEra_Run3 \
        --customise Configuration/DataProcessing/Utils.addMonitoring \
        --customise SoftDisplacedVertices/CustomMiniAOD/miniAOD_cff.miniAOD_customise_SoftDisplacedVerticesMC \
        --customise SoftDisplacedVertices/CustomMiniAOD/miniAOD_cff.miniAOD_filter_SoftDisplacedVertices \
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
    cmsDriver.py --python_filename "Data_${era}_CustomMiniAOD.py" \
        --filein "file:AOD.root" \
        --fileout "MiniAOD.root" \
        --step PAT \
        --processName MINI \
        --eventcontent MINIAOD \
        --datatier MINIAOD \
        --customise Configuration/DataProcessing/RecoTLR.customisePostEra_Run3 \
        --customise Configuration/DataProcessing/Utils.addMonitoring \
        --customise SoftDisplacedVertices/CustomMiniAOD/miniAOD_cff.miniAOD_customise_SoftDisplacedVertices \
        --customise SoftDisplacedVertices/CustomMiniAOD/miniAOD_cff.miniAOD_filter_SoftDisplacedVertices \
        --customise_commands="process.add_(cms.Service('InitRootHandlers', EnableIMT = cms.untracked.bool(False)));process.MessageLogger.cerr.FwkReport.reportEvery=1000" \
        --conditions "${DATA_GT[$era]}" \
        --era "${DATA_ERA[$era]}" \
        --scenario pp \
        --no_exec \
        -n -1 \
        --nThreads 2 \
        --data
done