#!/bin/bash -x

declare -A MC_GT
MC_GT["Run3Summer22"]="130X_mcRun3_2022_realistic_v5"
MC_GT["Run3Summer22EE"]="130X_mcRun3_2022_realistic_postEE_v6"


declare -A MC_ERA
MC_ERA["Run3Summer22"]="Run3,run3_miniAOD_12X"
MC_ERA["Run3Summer22EE"]="Run3,run3_miniAOD_12X"


declare -A DATA_GT
DATA_GT["Run2022"]="130X_dataRun3_v2"

declare -A DATA_ERA
DATA_ERA["Run2022"]="Run3,run3_miniAOD_12X"

for era in "Run3Summer22" "Run3Summer22EE"
do
    cmsDriver.py CustomMiniAOD --python_filename "MC_${era}_CustomMiniAOD.py" \
        --filein "file:AOD.root" \
        --fileout "MiniAOD.root" \
        --step PAT \
        --eventcontent MINIAODSIM \
        --datatier MINIAODSIM \
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

era="Run2022"
cmsDriver.py --python_filename "Data_${era}_CustomMiniAOD.py" \
    --filein "file:AOD.root" \
    --fileout "MiniAOD.root" \
    --step PAT \
    --eventcontent MINIAOD \
    --datatier MINIAOD \
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
