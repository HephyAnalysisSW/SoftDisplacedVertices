set -e

### DATA
#python3 autoplotter.py --sample met_2018 --output /scratch-cbe/users/ang.li/SoftDV/Histos/Histos_${1} --config configs/plotconfig_${2}.yaml --lumi -1 --json scratch_data18.json --datalabel CustomNanoAOD --data --year 2018 --nfiles 2 --submit
python3 resubmit.py --sample met_2018 --jobdir /scratch-cbe/users/ang.li/SoftDV/Histos/Histos_${1} --config configs/plotconfig_${2}.yaml --lumi -1 --json scratch_data18.json --datalabel CustomNanoAOD --data --year 2018
cp jobs.sh jobs_data18.sh
#submit jobs.sh --nCPUs=4

### BKG MC
#python3 autoplotter.py --sample znunu_2018 wlnu_2018 qcd_2018 top_2018 --output /scratch-cbe/users/ang.li/SoftDV/Histos/Histos_${1} --config configs/plotconfig_${2}.yaml --lumi 59683. --json scratch_sig18.json --datalabel CustomNanoAOD --year 2018 --nfiles 5 --submit
python3 resubmit.py --sample znunu_2018 wlnu_2018 qcd_2018 top_2018 --jobdir /scratch-cbe/users/ang.li/SoftDV/Histos/Histos_${1} --config configs/plotconfig_${2}.yaml --lumi 59683. --json scratch_sig18.json --datalabel CustomNanoAOD --year 2018 
cp jobs.sh jobs_bkg18.sh
#submit jobs.sh --title={3}
#
#python3 autoplotter.py --sample stop_2018 --output /eos/vbc/group/cms/ang.li/Histos_${1} --config configs/plotconfig_${2}.yaml --lumi 59683. --json MC_RunIISummer20UL18.json --datalabel CustomNanoAOD --year 2018 --submit
#submit jobs.sh 
#
#python3 autoplotter.py --sample stop_2018 --output /eos/vbc/group/cms/ang.li/Histos_${1}_HEM --config configs/plotconfig_${2}_HEM.yaml --lumi 59683. --json MC_RunIISummer20UL18.json --datalabel CustomNanoAOD --year 2018 --submit
#submit jobs.sh 

### SIG MC
#python3 autoplotter.py --sample stop_2018 --output /eos/vbc/group/cms/ang.li/HistosGen_${1} --config configs/plotconfig_${2}sig.yaml --lumi 59683. --json MC_RunIISummer20UL18.json --datalabel CustomNanoAOD --year 2018 --submit
#submit jobs.sh 
python3 autoplotter.py --sample C1N2ML_M200_195_ct20_2018 C1N2ML_M200_185_ct20_2018 stopML_M1000_988_ct200_2018 stopML_M1000_980_ct2_2018 --output /scratch-cbe/users/ang.li/SoftDV/Histos/Histos_${1} --config configs/plotconfig_${2}.yaml --lumi 59683. --json scratch_sig18.json --datalabel CustomNanoAOD --year 2018 --submit
cp jobs.sh jobs_sig18.sh

### DATA
python3 autoplotter.py --sample met_2017 --output /scratch-cbe/users/ang.li/SoftDV/Histos/Histos_${1} --config configs/plotconfig_${2}.yaml --lumi -1 --json scratch_data18.json --datalabel CustomNanoAOD --data --year 2017 --nfiles 2 --submit
cp jobs.sh jobs_data17.sh
#python3 resubmit.py --sample met_2017 --jobdir /scratch-cbe/users/ang.li/SoftDV/Histos/Histos_${1} --config nominal_configs/plotconfig_${2}.yaml --lumi -1 --json Data_MET2017.json --datalabel CustomNanoAOD --year 2017 
#submit jobs.sh --nCPUs=4

### MC
python3 autoplotter.py --sample znunu_2017 wlnu_2017 qcd_2017 top_2017 --output /scratch-cbe/users/ang.li/SoftDV/Histos/Histos_${1} --config configs/plotconfig_${2}.yaml --lumi 40610. --json scratch_MC18.json --datalabel CustomNanoAOD --year 2017 --nfiles 5 --submit
cp jobs.sh jobs_bkg17.sh
#submit jobs.sh --nCPUs=4
#
#python3 autoplotter.py --sample stop_2017 --output /eos/vbc/group/cms/ang.li/Histos_${1} --config configs/plotconfig_${2}_dm.yaml --lumi 162440. --json MC_RunIISummer20UL17.json --datalabel CustomNanoAOD --year 2017 --submit
#submit jobs.sh 

### SIG MC
#python3 autoplotter.py --sample stop_2017 --output /eos/vbc/group/cms/ang.li/Histos_${1}_2017_sig --config configs/plotconfig_${2}sig_dm.yaml --lumi 162440. --json MC_RunIISummer20UL17.json --datalabel CustomNanoAOD --year 2017 --nfiles 10 --submit
#python3 autoplotter.py --sample stop_2017 --output /eos/vbc/group/cms/ang.li/HistosGen_${1} --config configs/plotconfig_${2}sig.yaml --lumi 40610. --json MC_RunIISummer20UL17.json --datalabel CustomNanoAOD --year 2017 --nfiles 10 --submit
#submit jobs.sh 
