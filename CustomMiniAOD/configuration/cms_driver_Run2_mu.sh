#!/bin/bash -x


declare -A DATA_GT
DATA_GT["UL17"]="106X_dataRun2_v36"
DATA_GT["UL18"]="106X_dataRun2_v36"

declare -A DATA_ERA
DATA_ERA["UL17"]="Run2_2017"
DATA_ERA["UL18"]="Run2_2018"

for era in "UL17" "UL18"
do
    cmsDriver.py --python_filename "Data_${era}mu_CustomMiniAOD.py" \
        --filein "file:AOD.root" \
        --fileout "MiniAOD.root" \
        --step PAT \
        --eventcontent MINIAOD \
        --datatier MINIAOD \
        --customise Configuration/DataProcessing/Utils.addMonitoring \
        --customise SoftDisplacedVertices/CustomMiniAOD/miniAOD_cff.miniAOD_customise_SoftDisplacedVertices \
        --customise SoftDisplacedVertices/CustomMiniAOD/miniAOD_cff.miniAOD_trigger_isomu \
        --conditions "${DATA_GT[$era]}" \
        --procModifiers run2_miniAOD_UL \
        --era "${DATA_ERA[$era]}" \
        --scenario pp             \
        --runUnscheduled          \
        --no_exec                 \
        --data                    \
        --nThreads 2
done
