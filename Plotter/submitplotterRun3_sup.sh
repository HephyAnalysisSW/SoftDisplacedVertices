set -e

### DATA
python3 autoplotter.py --sample met_2022Pre --output /scratch-cbe/users/ang.li/SoftDV/Histos/Histos_${1} --config configs/plotconfig_Run3_${2}.yaml --lumi -1 --json scratch_dataRun3.json --datalabel CustomNanoAOD --data --year 2022Pre --nfiles 2 --submit
#python3 resubmit.py --sample met_2018 --jobdir /scratch-cbe/users/ang.li/SoftDV/Histos/Histos_${1} --config configs/plotconfig_${2}.yaml --lumi -1 --json clip_IVF_data.json --datalabel CustomNanoAOD --data --year 2018
cp jobs.sh jobs_data22Pre.sh

### BKG MC
python3 autoplotter.py --sample wlnu_2022Pre znunu_2022Pre qcd_2022Pre top_2022Pre  --output /scratch-cbe/users/ang.li/SoftDV/Histos/Histos_${1} --config configs/plotconfig_Run3_${2}.yaml --lumi 7990. --json scratch_MCRun3.json --datalabel CustomNanoAOD --year 2022Pre --nfiles 5 --submit
cp jobs.sh jobs_bkg22Pre.sh
#python3 resubmit.py --sample znunu_2018 wlnu_2018 qcd_2018 top_2018 --jobdir /scratch-cbe/users/ang.li/SoftDV/Histos/Histos_${1} --config nominal_configs/plotconfig_${2}.yaml --lumi 59683. --json MC_RunIISummer20UL18.json --datalabel CustomNanoAOD --year 2018 

### SIG MC

### DATA
python3 autoplotter.py --sample met_2022Post --output /scratch-cbe/users/ang.li/SoftDV/Histos/Histos_${1} --config configs/plotconfig_Run3_${2}.yaml --lumi -1 --json scratch_dataRun3.json --datalabel CustomNanoAOD --data --year 2022Post --nfiles 2 --submit
#python3 resubmit.py --sample met_2018 --jobdir /scratch-cbe/users/ang.li/SoftDV/Histos/Histos_${1} --config configs/plotconfig_${2}.yaml --lumi -1 --json clip_IVF_data.json --datalabel CustomNanoAOD --data --year 2018
cp jobs.sh jobs_data22Post.sh

### BKG MC
python3 autoplotter.py --sample wlnu_2022Post znunu_2022Post qcd_2022Post top_2022Post  --output /scratch-cbe/users/ang.li/SoftDV/Histos/Histos_${1} --config configs/plotconfig_Run3_${2}.yaml --lumi 26680. --json scratch_MCRun3.json --datalabel CustomNanoAOD --year 2022Post --nfiles 5 --submit
cp jobs.sh jobs_bkg22Post.sh
#python3 resubmit.py --sample znunu_2018 wlnu_2018 qcd_2018 top_2018 --jobdir /scratch-cbe/users/ang.li/SoftDV/Histos/Histos_${1} --config nominal_configs/plotconfig_${2}.yaml --lumi 59683. --json MC_RunIISummer20UL18.json --datalabel CustomNanoAOD --year 2018 

### SIG MC

### DATA
python3 autoplotter.py --sample met_2023Pre --output /scratch-cbe/users/ang.li/SoftDV/Histos/Histos_${1} --config configs/plotconfig_Run3_${2}.yaml --lumi -1 --json scratch_dataRun3.json --datalabel CustomNanoAOD --data --year 2023Pre --nfiles 2 --submit
#python3 resubmit.py --sample met_2018 --jobdir /scratch-cbe/users/ang.li/SoftDV/Histos/Histos_${1} --config configs/plotconfig_${2}.yaml --lumi -1 --json clip_IVF_data.json --datalabel CustomNanoAOD --data --year 2018
cp jobs.sh jobs_data23Pre.sh

### BKG MC
python3 autoplotter.py --sample wlnu_2023Pre znunu_2023Pre qcd_2023Pre top_2023Pre  --output /scratch-cbe/users/ang.li/SoftDV/Histos/Histos_${1} --config configs/plotconfig_Run3_${2}.yaml --lumi 17960. --json scratch_MCRun3.json --datalabel CustomNanoAOD --year 2023Pre --nfiles 5 --submit
cp jobs.sh jobs_bkg23Pre.sh
#python3 resubmit.py --sample znunu_2018 wlnu_2018 qcd_2018 top_2018 --jobdir /scratch-cbe/users/ang.li/SoftDV/Histos/Histos_${1} --config nominal_configs/plotconfig_${2}.yaml --lumi 59683. --json MC_RunIISummer20UL18.json --datalabel CustomNanoAOD --year 2018 

### SIG MC

### DATA
python3 autoplotter.py --sample met_2023Post --output /scratch-cbe/users/ang.li/SoftDV/Histos/Histos_${1} --config configs/plotconfig_Run3_${2}.yaml --lumi -1 --json scratch_dataRun3.json --datalabel CustomNanoAOD --data --year 2023Post --nfiles 2 --submit
#python3 resubmit.py --sample met_2018 --jobdir /scratch-cbe/users/ang.li/SoftDV/Histos/Histos_${1} --config configs/plotconfig_${2}.yaml --lumi -1 --json clip_IVF_data.json --datalabel CustomNanoAOD --data --year 2018
cp jobs.sh jobs_data23Post.sh

### BKG MC
python3 autoplotter.py --sample wlnu_2023Post znunu_2023Post qcd_2023Post top_2023Post  --output /scratch-cbe/users/ang.li/SoftDV/Histos/Histos_${1} --config configs/plotconfig_Run3_${2}.yaml --lumi 9680. --json scratch_MCRun3.json --datalabel CustomNanoAOD --year 2023Post --nfiles 5 --submit
cp jobs.sh jobs_bkg23Post.sh
#python3 resubmit.py --sample znunu_2018 wlnu_2018 qcd_2018 top_2018 --jobdir /scratch-cbe/users/ang.li/SoftDV/Histos/Histos_${1} --config nominal_configs/plotconfig_${2}.yaml --lumi 59683. --json MC_RunIISummer20UL18.json --datalabel CustomNanoAOD --year 2018 

### SIG MC
