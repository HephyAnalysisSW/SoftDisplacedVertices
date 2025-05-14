#!/bin/bash -x

declare -A MC_GT
MC_GT["Run3Summer23"]="130X_mcRun3_2023_realistic_v14"
MC_GT["Run3Summer23BPix"]="130X_mcRun3_2023_realistic_postBPix_v2"


declare -A MC_ERA
MC_ERA["Run3Summer23"]="Run3_2023"
MC_ERA["Run3Summer23BPix"]="Run3_2023"


declare -A DATA_GT
DATA_GT["Run2023"]="130X_dataRun3_Prompt_HcalSiPM_v1"

declare -A DATA_ERA
DATA_ERA["Run2023"]="Run3"

for era in "Run3Summer23" "Run3Summer23BPix"
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
        --conditions "${MC_GT[$era]}" \
        --geometry DB:Extended \
        --era "${MC_ERA[$era]}" \
        --no_exec \
        --mc
done

era="Run2023"
cmsDriver.py --python_filename "Data_${era}_CustomMiniAOD.py" \
    --filein "file:AOD.root" \
    --fileout "MiniAOD.root" \
    --step PAT,NANO \
    --eventcontent MINIAOD,NANOAOD \
    --datatier MINIAOD,NANOAOD \
    --customise Configuration/DataProcessing/RecoTLR.customisePostEra_Run3 \
    --customise Configuration/DataProcessing/Utils.addMonitoring \
    --customise PhysicsTools/NanoAOD/nano_cff.nanoL1TrigObjCustomize \
    --customise SoftDisplacedVertices/CustomMiniAOD/miniAOD_cff.miniAOD_customise_SoftDisplacedVertices \
    --customise SoftDisplacedVertices/CustomMiniAOD/miniAOD_cff.miniAOD_filter_SoftDisplacedVertices \
    --conditions "${DATA_GT[$era]}" \
    --era "${DATA_ERA[$era]}" \
    --scenario pp \
    --no_exec \
    --data
