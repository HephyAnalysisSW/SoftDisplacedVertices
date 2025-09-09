#!/bin/bash -x


declare -A DATA_GT
DATA_GT["UL17"]="106X_dataRun2_v36"
DATA_GT["UL18"]="106X_dataRun2_v36"

declare -A DATA_ERA
DATA_ERA["UL17"]="Run2_2017,run2_nanoAOD_106Xv2"
DATA_ERA["UL18"]="Run2_2018,run2_nanoAOD_106Xv2"

for era in "UL17" "UL18"
do
    cmsDriver.py --python_filename "Data_${era}mu_CustomNanoAOD.py" \
        --filein "file:MiniAOD.root" \
        --fileout "NanoAOD.root" \
        --step NANO \
        --eventcontent NANOAOD \
        --datatier NANOAOD \
        --customise Configuration/DataProcessing/Utils.addMonitoring \
        --customise_commands="process.add_(cms.Service('InitRootHandlers', EnableIMT = cms.untracked.bool(False)));process.MessageLogger.cerr.FwkReport.reportEvery=1000" \
        --customise SoftDisplacedVertices/CustomNanoAOD/nanoAOD_cff.nanoAOD_customise_SoftDisplacedVerticesMC \
        -n -1 \
        --conditions "${DATA_GT[$era]}" \
        --era "${DATA_ERA[$era]}" \
        --scenario pp             \
        --runUnscheduled          \
        --no_exec                 \
        --data                    \
        --nThreads 2
done
