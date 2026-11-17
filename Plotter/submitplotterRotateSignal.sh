set -e
# Gen-matched C1N2 signal vertices (benchmark points C1N2_M400_{395,390,380}_ct{2,20}, all Run 3 eras)
# for the rotated-D vs signal comparison, Run 3 ParTScore_K inputs. xsec=-1 -> --lumi -1 (shapes only).
# usage: bash submitplotterRotateSignal.sh   (then submit the jobs_*.sh with submit_el8)

OUT=/scratch-cbe/users/ang.li/SoftDV/Histos/Histos_C1N2Run3_RotateSignal

for year in 2022Pre 2022Post 2023Pre 2023Post 2024
do
    tag=${year#20}
    era=${year,,}   # sample-name suffix: 2022pre, ..., 2024
    samples=""
    for m2 in 395 390 380
    do
        for ct in 2 20
        do
            samples="${samples} C1N2_M400_${m2}_ct${ct}_${era}"
        done
    done
    python3 autoplotter.py --sample ${samples} --output ${OUT} --config configs/plotconfig_Run3_RotateSignal.yaml --lumi -1 --json scratch_C1N2Run3_ParTScore_K.json --datalabel CustomNanoAOD --year ${year} --nfiles 1 --submit
    cp jobs.sh jobs_RotateSignal_sig${tag}.sh
done
