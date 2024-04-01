#!/bin/bash

export SCRAM_ARCH=slc7_amd64_gcc700
source /cvmfs/cms.cern.ch/cmsset_default.sh
n=EVENTCOUNT
HOME="$PWD"
STORE="/scratch/felix.lang/SignalProduction"
RUN_NUMBER=$RUN_NUMBER
FIRST_EVENT=$FIRST_EVENT
#EVENT_NUMBER=$EVENT_NUMBER

if [ ! -r CMSSW_10_6_30/src ]; then
  scram p CMSSW CMSSW_10_6_30
fi
cd CMSSW_10_6_30/src
mkdir -p Configuration/GenProduction/python/
cp $HOME/random.py Configuration/GenProduction/python/random.py
eval `scram runtime -sh`
scram b

#GEN
cp $HOME/drivers/LHEGEN-cfg.py LHEGEN-cfg.py
config_content=$(cat <<EOL
#####################################

process.source.firstEvent = cms.untracked.uint32($FIRST_EVENT)

#####################################
EOL
)
echo "$config_content" >> "LHEGEN-cfg.py"

cmsRun LHEGEN-cfg.py

#SIM
cp $HOME/drivers/SIM-cfg.py SIM-cfg.py
cmsRun SIM-cfg.py

#PREMIX
cp $HOME/drivers/PREMIX-cfg.py PREMIX-cfg.py
cmsRun PREMIX-cfg.py

cd $HOME
if [ ! -r CMSSW_10_2_16_UL/src ]; then
  scram p CMSSW CMSSW_10_2_16_UL
fi
cd CMSSW_10_2_16_UL/src
eval `scram runtime -sh`
scram b

cp $HOME/CMSSW_10_6_30/src/PREMIX.root .

#HLT
cp $HOME/drivers/HLT-cfg.py HLT-cfg.py
cmsRun HLT-cfg.py

cd $HOME/CMSSW_10_6_30/src
eval `scramv1 runtime -sh`

cp $HOME/CMSSW_10_2_16_UL/src/HLT.root .

#AODSIM (with IVF1)
cp $HOME/drivers/AODSIM-IVF1-cfg.py AODSIM-IVF1-cfg.py
cmsRun AODSIM-IVF1-cfg.py

#MINIAOD
cp $HOME/drivers/MINIAODSIM-cfg.py MINIAODSIM-cfg.py
cmsRun MINIAODSIM-cfg.py

#NANOAOD
cp $HOME/drivers/NANOAODSIM-cfg.py NANOAODSIM-cfg.py
cmsRun NANOAODSIM-cfg.py

#COPY FILES
cd $STORE

directories=("samplesNewSeedNoDuplicates" "samplesNewSeedNoDuplicates/AODSIM" "samplesNewSeedNoDuplicates/MINIAODSIM" "samplesNewSeedNoDuplicates/NANOAODSIM")

for dir in "${directories[@]}"; do
  if [ ! -d "$dir" ]; then
    mkdir -p "$dir"
  fi
done

cp $HOME/CMSSW_10_6_30/src/AODSIM.root samplesNewSeedNoDuplicates/AODSIM/$RUN_NUMBER-testIVF1_AODSIM_PROCESS_LLPMASS_LSPMASS_CTAUVALUE_Standard_EVENTCOUNT.root
cp $HOME/CMSSW_10_6_30/src/MINIAODSIM.root samplesNewSeedNoDuplicates/MINIAODSIM/$RUN_NUMBER-testIVF1_MINIAODSIM_PROCESS_LLPMASS_LSPMASS_CTAUVALUE_Standard_EVENTCOUNT.root
cp $HOME/CMSSW_10_6_30/src/NANOAODSIM.root samplesNewSeedNoDuplicates/NANOAODSIM/$RUN_NUMBER-testIVF1_NANOAODSIM_PROCESS_LLPMASS_LSPMASS_CTAUVALUE_Standard_EVENTCOUNT.root

rm -r $HOME/CMSSW_10_6_30
rm -r $HOME/CMSSW_10_2_16_UL
