#!/bin/bash
#SBATCH --time=24:00:00
#SBATCH --qos=medium

export SCRAM_ARCH=slc7_amd64_gcc700
source /cvmfs/cms.cern.ch/cmsset_default.sh
n=EVENTCOUNT
HOME="$PWD"
#STORE="/scratch/ang.li/GenOutput_4_2bodystop"
STORE="/scratch/ang.li/GenOutput_stop_MLtraining_lowdm_2018"
RUN_NUMBER=$RUN_NUMBER
FIRST_EVENT=$FIRST_EVENT
#EVENT_NUMBER=$EVENT_NUMBER

if [ ! -d $STORE ]; then
  mkdir $STORE
fi

if [ ! -r CMSSW_10_6_45/src ]; then
  scram p CMSSW CMSSW_10_6_45
fi
cd CMSSW_10_6_45/src
eval `scram runtime -sh`
#git cms-merge-topic 46834
mkdir -p Configuration/GenProduction/python/
cp $HOME/random.py Configuration/GenProduction/python/random.py
mkdir -p Configuration/GenProduction/data/
cp /scratch/ang.li/Configuration-Generator/* Configuration/GenProduction/data/.
cp /scratch/ang.li/SLHA/* Configuration/GenProduction/data/.
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
#cp $HOME/drivers/SIM-cfg.py SIM-cfg.py
#cmsRun SIM-cfg.py

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

cp $HOME/CMSSW_10_6_45/src/PREMIX.root .

#HLT
cp $HOME/drivers/HLT-cfg.py HLT-cfg.py
cmsRun HLT-cfg.py

cd $HOME/CMSSW_10_6_45/src
eval `scramv1 runtime -sh`

cp $HOME/CMSSW_10_2_16_UL/src/HLT.root .

#AODSIM (with IVF1)
cp $HOME/drivers/AODSIM-IVF1-cfg.py AODSIM-IVF1-cfg.py
cmsRun AODSIM-IVF1-cfg.py

##MINIAOD
#cp $HOME/drivers/MINIAODSIM-cfg.py MINIAODSIM-cfg.py
#cmsRun MINIAODSIM-cfg.py
#
##NANOAOD
#cp $HOME/drivers/NANOAODSIM-cfg.py NANOAODSIM-cfg.py
#cmsRun NANOAODSIM-cfg.py

#COPY FILES
cd $STORE

directories=("PROCESS_LLPMASS_LSPMASS_CTAUVALUE" "PROCESS_LLPMASS_LSPMASS_CTAUVALUE/AODSIM" "PROCESS_LLPMASS_LSPMASS_CTAUVALUE/MINIAODSIM" "PROCESS_LLPMASS_LSPMASS_CTAUVALUE/NANOAODSIM")

for dir in "${directories[@]}"; do
  if [ ! -d "$dir" ]; then
    mkdir -p "$dir"
  fi
done

cp $HOME/CMSSW_10_6_45/src/AODSIM.root PROCESS_LLPMASS_LSPMASS_CTAUVALUE/AODSIM/$RUN_NUMBER-testIVF1_AODSIM_PROCESS_LLPMASS_LSPMASS_CTAUVALUE_Standard_EVENTCOUNT.root
#cp $HOME/CMSSW_10_6_45/src/MINIAODSIM.root PROCESS_LLPMASS_LSPMASS_CTAUVALUE/MINIAODSIM/$RUN_NUMBER-testIVF1_MINIAODSIM_PROCESS_LLPMASS_LSPMASS_CTAUVALUE_Standard_EVENTCOUNT.root
#cp $HOME/CMSSW_10_6_45/src/NANOAODSIM.root PROCESS_LLPMASS_LSPMASS_CTAUVALUE/NANOAODSIM/$RUN_NUMBER-testIVF1_NANOAODSIM_PROCESS_LLPMASS_LSPMASS_CTAUVALUE_Standard_EVENTCOUNT.root

rm -rf $HOME/CMSSW_10_6_45
rm -rf $HOME/CMSSW_10_2_16_UL
