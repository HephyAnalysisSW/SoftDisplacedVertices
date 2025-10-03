#!/bin/bash -x

# MC
# ------------------------------------------------------------------------


declare -A MC_GT
MC_GT["Run3Summer22"]="130X_mcRun3_2022_realistic_v5"
MC_GT["Run3Summer22EE"]="130X_mcRun3_2022_realistic_postEE_v6"
MC_GT["Run3Summer23"]="130X_mcRun3_2023_realistic_v14"
MC_GT["Run3Summer23BPix"]="130X_mcRun3_2023_realistic_postBPix_v2"


declare -A MC_ERA
MC_ERA["Run3Summer22"]="Run3,run3_miniAOD_12X"
MC_ERA["Run3Summer22EE"]="Run3,run3_miniAOD_12X"
MC_ERA["Run3Summer23"]="Run3_2023"
MC_ERA["Run3Summer23BPix"]="Run3_2023"





# for era in "Run3Summer22" "Run3Summer22EE" "Run3Summer23" "Run3Summer23BPix"
# do
#     cmsDriver.py CustomMiniAOD --python_filename "MC_${era}_CustomMiniAOD.py" \
#         --filein "file:AOD.root" \
#         --fileout "MiniAOD.root" \
#         --step PAT \
#         --eventcontent MINIAODSIM \
#         --datatier MINIAODSIM \
#         --customise Configuration/DataProcessing/Utils.addMonitoring \
#         --customise SoftDisplacedVertices/CustomMiniAOD/miniAOD_cff.miniAOD_customise_SoftDisplacedVerticesMC \
#         --customise SoftDisplacedVertices/CustomMiniAOD/miniAOD_cff.miniAOD_filter_SoftDisplacedVertices \
#         --customise_commands="process.add_(cms.Service('InitRootHandlers', EnableIMT = cms.untracked.bool(False)));process.MessageLogger.cerr.FwkReport.reportEvery=1000" \
#         --conditions "${MC_GT[$era]}" \
#         --geometry DB:Extended \
#         --era "${MC_ERA[$era]}" \
#         --no_exec \
#         -n -1 \
#         --nThreads 2 \
#         --mc
# done




# DATA
# ------------------------------------------------------------------------


declare -A DATA_GT
DATA_GT["Run2022CDE"]="130X_dataRun3_v2"
DATA_GT["Run2022FG"]="130X_dataRun3_PromptAnalysis_v1"
DATA_GT["Run2023"]="130X_dataRun3_PromptAnalysis_v1"

declare -A DATA_ERA
DATA_ERA["Run2022CDE"]="Run3,run3_miniAOD_12X"
DATA_ERA["Run2022FG"]="Run3,run3_miniAOD_12X"
DATA_ERA["Run2023"]="Run3"



for era in "Run2022CDE" "Run2022FG" "Run2023"
do
    cmsDriver.py \
        --python_filename "Data_${era}_CustomMiniAOD.py" \
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