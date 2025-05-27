#!/bin/bash -x

declare -A MC_GT
MC_GT["UL16preVFP"]="106X_mcRun2_asymptotic_preVFP_v11"
MC_GT["UL16"]="106X_mcRun2_asymptotic_v17"
MC_GT["UL17"]="106X_mc2017_realistic_v9"
MC_GT["UL18"]="106X_upgrade2018_realistic_v16_L1v1"

declare -A MC_ERA
MC_ERA["UL16preVFP"]="Run2_2016_HIPM"
MC_ERA["UL16"]="Run2_2016"
MC_ERA["UL17"]="Run2_2017"
MC_ERA["UL18"]="Run2_2018"

declare -A DATA_GT
DATA_GT["UL16preVFP"]="106X_dataRun2_v35"
DATA_GT["UL16"]="106X_dataRun2_v35"
DATA_GT["UL17"]="106X_dataRun2_v35"
DATA_GT["UL18"]="106X_dataRun2_v35"

declare -A DATA_ERA
DATA_ERA["UL16preVFP"]="Run2_2016_HIPM"
DATA_ERA["UL16"]="Run2_2016"
DATA_ERA["UL17"]="Run2_2017"
DATA_ERA["UL18"]="Run2_2018"

for era in "UL16preVFP" "UL16" "UL17" "UL18"
do
    cmsDriver.py NANO -s NANO \
        --python_filename "MC_${era}_CustomNanoAOD.py" \
        --filein "file:MiniAOD.root" \
        --fileout "NanoAOD.root" \
        --mc \
        --conditions ${MC_GT[$era]} \
        --era "${MC_ERA[$era]},run2_nanoAOD_106Xv2" \
        --eventcontent NANOAODSIM \
        --datatier NANOAODSIM \
        --customise_commands="process.add_(cms.Service('InitRootHandlers', EnableIMT = cms.untracked.bool(False)));process.MessageLogger.cerr.FwkReport.reportEvery=1000" \
        --customise SoftDisplacedVertices/CustomNanoAOD/nanoAOD_cff.nanoAOD_customise_SoftDisplacedVerticesMC \
        -n -1 \
        --no_exec \
        --nThreads 4

    cmsDriver.py NANO -s NANO \
        --python_filename "Data_${era}_CustomNanoAOD.py" \
        --filein "file:MiniAOD.root" \
        --fileout "NanoAOD.root" \
        --data \
        --conditions ${DATA_GT[$era]} \
        --era "${DATA_ERA[$era]},run2_nanoAOD_106Xv2" \
        --eventcontent NANOAOD \
        --datatier NANOAOD \
        --customise_commands="process.add_(cms.Service('InitRootHandlers', EnableIMT = cms.untracked.bool(False)));process.MessageLogger.cerr.FwkReport.reportEvery=1000" \
        --customise SoftDisplacedVertices/CustomNanoAOD/nanoAOD_cff.nanoAOD_customise_SoftDisplacedVertices \
        -n -1 \
        --no_exec \
        --nThreads 4
done
