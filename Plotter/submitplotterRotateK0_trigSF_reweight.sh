set -e
# RotateK0 plots with MET trigger SF + D-mass (RotateVtx_mass_before) shape weights on bkg MC,
# ParTScore_D inputs, data + bkg MC 2017-2024 (configs *_RotateK0_reweight.yaml)
# usage: bash submitplotterRotateK0_trigSF_reweight.sh   (then submit the jobs_*.sh with submit_el8)

OUT=/scratch-cbe/users/ang.li/SoftDV/Histos/Histos_ParTScoreD_RotateK0_trigSF_reweight

declare -A LUMI=( [2017]=42070 [2018]=59560 [2022Pre]=7990 [2022Post]=26680 [2023Pre]=17960 [2023Post]=9680 [2024]=109820 )

for year in 2017 2018 2022Pre 2022Post 2023Pre 2023Post 2024
do
    if [[ $year == 201* ]]; then run=Run2; else run=Run3; fi
    tag=${year#20}

    ### DATA
    python3 autoplotter.py --sample met_${year} --output ${OUT} --config configs/plotconfig_${run}_RotateK0_reweight.yaml --lumi -1 --json scratch_data_ParTScore_D.json --datalabel CustomNanoAOD --data --year ${year} --nfiles 2 --submit
    cp jobs.sh jobs_RotateK0_trigSF_rw_data${tag}.sh

    ### BKG MC
    python3 autoplotter.py --sample znunu_${year} wlnu_${year} qcd_${year} top_${year} --output ${OUT} --config configs/plotconfig_${run}_RotateK0_reweight.yaml --lumi ${LUMI[$year]} --json scratch_MC_ParTScore_D.json --datalabel CustomNanoAOD --year ${year} --nfiles 5 --submit
    cp jobs.sh jobs_RotateK0_trigSF_rw_bkg${tag}.sh
done
