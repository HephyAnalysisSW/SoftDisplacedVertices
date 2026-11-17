set -e
# Gen-matched C1N2 signal vertices (benchmark points C1N2_M400_{395,390,380}_ct{2,20}, all Run 3 eras)
# with the material veto (selections matched_mapveto / matched3tk_mapveto), for the rotated-D vs signal comparison, Run 3 ParTScore_K inputs from EOS (xrootd). xsec=-1 -> --lumi -1 (shapes only).
# usage: bash submitplotterRotateSignal_mapveto.sh   (then submit the jobs_*.sh with submit_el8_cbe)

OUT=/groups/hephy/cms/ang.li/SoftDV/Histos/Histos_C1N2Run3_RotateSignal_mapveto

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
    python3 autoplotter.py --sample ${samples} --output ${OUT} --config configs/plotconfig_Run3_RotateSignal_mapveto.yaml --lumi -1 --json eos_C1N2Run3_ParTScore_K.json --datalabel CustomNanoAOD --year ${year} --nfiles 1 --submit
    cp jobs.sh jobs_RotateSignal_mapveto_sig${tag}.sh
done

# never read EOS through the FUSE mount: autoplotter writes bare /eos paths into the file lists, add the xrootd redirector
sed -i 's#^/eos/#root://eos.grid.vbc.ac.at//eos/#' ${OUT}/*/input/*_fn*.txt
if grep -L '^root://eos.grid.vbc.ac.at//eos/' ${OUT}/*/input/*_fn*.txt | grep -q .; then echo "ERROR: file lists without redirector"; exit 1; fi
if grep -hv '^root://eos.grid.vbc.ac.at//eos/' ${OUT}/*/input/*_fn*.txt | grep -q .; then echo "ERROR: input lines without redirector"; exit 1; fi
echo "all file lists use root://eos.grid.vbc.ac.at/"
