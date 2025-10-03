#!/bin/bash -x

# DATA
# ------------------------------------------------------------------------


declare -A DATA_GT
DATA_GT["Run2024"]="150X_dataRun3_v2"

declare -A DATA_ERA
DATA_ERA["Run2024"]="Run3_2024"



for era in "Run2024"
do
    cmsDriver.py --python_filename "Data_${era}mu_CustomMiniAOD.py" \
        --filein "file:AOD.root" \
        --fileout "MiniAOD.root" \
        --step PAT \
        --processName MINI \
        --eventcontent MINIAOD \
        --datatier MINIAOD \
        --customise Configuration/DataProcessing/RecoTLR.customisePostEra_Run3 \
        --customise Configuration/DataProcessing/Utils.addMonitoring \
        --customise SoftDisplacedVertices/CustomMiniAOD/miniAOD_cff.miniAOD_customise_SoftDisplacedVertices \
        --customise SoftDisplacedVertices/CustomMiniAOD/miniAOD_cff.miniAOD_trigger_isomu \
        --customise_commands="process.add_(cms.Service('InitRootHandlers', EnableIMT = cms.untracked.bool(False)));process.MessageLogger.cerr.FwkReport.reportEvery=1000" \
        --conditions "${DATA_GT[$era]}" \
        --era "${DATA_ERA[$era]}" \
        --scenario pp \
        --no_exec \
        -n -1 \
        --nThreads 2 \
        --data
done