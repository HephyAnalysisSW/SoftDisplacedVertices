#!/bin/bash -x
declare -A DATA_GT
DATA_GT["Run2022"]="130X_dataRun3_v2"
DATA_GT["Run2023"]="130X_dataRun3_PromptAnalysis_v1"

declare -A DATA_ERA
DATA_ERA["Run2022"]="Run3,run3_miniAOD_12X"
DATA_ERA["Run2023"]="Run3"



era="Run2022"
cmsDriver.py --python_filename "Data_${era}mu_CustomMiniAOD.py" \
    --filein "file:AOD.root" \
    --fileout "MiniAOD.root" \
    --step PAT \
    --processName MINI \
    --eventcontent MINIAOD \
    --datatier MINIAOD \
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


era="Run2023"
cmsDriver.py --python_filename "Data_${era}mu_CustomMiniAOD.py" \
    --filein "file:AOD.root" \
    --fileout "MiniAOD.root" \
    --step PAT \
    --processName MINI \
    --eventcontent MINIAOD \
    --datatier MINIAOD \
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