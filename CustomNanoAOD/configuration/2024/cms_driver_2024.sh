#!/bin/bash -x

declare -A MC_GT
MC_GT["Run3Summer24"]="150X_mcRun3_2024_realistic_v2"


declare -A MC_ERA
MC_ERA["Run3Summer24"]="Run3_2024"

# declare -A DATA_GT
# DATA_GT[""]=""
# 
# declare -A DATA_ERA
# DATA_ERA[""]=""

for era in "Run3Summer24"
do
    cmsDriver.py CustomNanoAOD --python_filename "MC_${era}_CustomNanoAOD.py" \
        --filein "file:MiniAOD.root" \
        --fileout "NanoAOD.root" \
        --step NANO \
        --scenario pp \
        --eventcontent NANOAODSIM1 \
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

# for era in ""
# do
#     cmsDriver.py --python_filename "Data_${era}_CustomNanoAOD.py" \
#         --filein "file:MiniAOD.root" \
#         --fileout "NanoAOD.root" \
#         --step NANO \
#         --eventcontent NANOAOD \
#         --datatier NANOAOD \
#         --customise Configuration/DataProcessing/RecoTLR.customisePostEra_Run3 \
#         --customise Configuration/DataProcessing/Utils.addMonitoring           \
#         --customise PhysicsTools/NanoAOD/nano_cff.nanoL1TrigObjCustomize       \
#         --customise SoftDisplacedVertices/CustomNanoAOD/nanoAOD_cff.nanoAOD_customise_SoftDisplacedVertices \
#         --customise_commands="process.add_(cms.Service('InitRootHandlers', EnableIMT = cms.untracked.bool(False)));process.MessageLogger.cerr.FwkReport.reportEvery=1000" \
#         --conditions "${DATA_GT[$era]}" \
#         --era "${DATA_ERA[$era]}" \
#         --scenario pp \
#         --no_exec \
#         -n -1 \
#         --nThreads 2 \
#         --data
# done