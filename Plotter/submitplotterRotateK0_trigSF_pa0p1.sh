set -e
# RotateK0 plots with MET trigger SF, NO object weights on bkg MC, extra RotateVtx selections
# all_pa0p2 / tight_pa0p2 and all_pa0p1 / tight_pa0p1 (pointing angle before rotation < 0.2 / < 0.1), plus the score-category 2D histograms,
# ParTScore_D inputs, data + bkg MC 2017-2024 (configs *_RotateK0_pa0p1.yaml)
# usage: bash submitplotterRotateK0_trigSF_pa0p1.sh   (then submit the jobs_*.sh with submit_el8_cbe)

OUT=/groups/hephy/cms/ang.li/SoftDV/Histos/Histos_ParTScoreD_RotateK0_trigSF_pa0p1

declare -A LUMI=( [2017]=42070 [2018]=59560 [2022Pre]=7990 [2022Post]=26680 [2023Pre]=17960 [2023Post]=9680 [2024]=109820 )

for year in 2017 2018 2022Pre 2022Post 2023Pre 2023Post 2024
do
    if [[ $year == 201* ]]; then run=Run2; else run=Run3; fi
    tag=${year#20}

    ### DATA
    python3 autoplotter.py --sample met_${year} --output ${OUT} --config configs/plotconfig_${run}_RotateK0_pa0p1.yaml --lumi -1 --json eos_data_ParTScore_D.json --datalabel CustomNanoAOD --data --year ${year} --nfiles 2 --submit
    cp jobs.sh jobs_RotateK0_trigSF_pa0p1_data${tag}.sh

    ### BKG MC
    python3 autoplotter.py --sample znunu_${year} wlnu_${year} qcd_${year} top_${year} --output ${OUT} --config configs/plotconfig_${run}_RotateK0_pa0p1.yaml --lumi ${LUMI[$year]} --json eos_MC_ParTScore_D.json --datalabel CustomNanoAOD --year ${year} --nfiles 5 --submit
    cp jobs.sh jobs_RotateK0_trigSF_pa0p1_bkg${tag}.sh
done
