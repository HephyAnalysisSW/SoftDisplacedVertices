# Per-year, per-selection shape weights (data/MC, both normalised) for background MC on the vertex LxySig of the
# rotation candidates, from the UNWEIGHTED ParTScore_D RotateK0_trigSF_pa0p1 histograms (ttbar normalisation fixed 2026-11-10).
# Variable bins; the last bin [100, 1000] includes the histogram overflow (LxySig > 100).
# Outputs lxysigweights_ParTScoreD_<year>.root with one hist per selection: w_LxySig_<sel>.
IN=/groups/hephy/cms/ang.li/SoftDV/Histos/Histos_ParTScoreD_RotateK0_trigSF_pa0p1
EDGES="0 2 4 6 8 10 15 20 30 40 50 70 100 1000"

for sel in all tight all_pa0p1 tight_pa0p1
do
    HIST=All_RotateVtx_${sel}/RotateVtx_LxySig
    for y in 2017 2018
    do
        python3 deriveWeights.py --numerator ${IN}/met${y}_hist.root:${HIST} --denominator ${IN}/background_${y}_hist.root:${HIST} --name w_LxySig_${sel} --normalize --edges ${EDGES} --output lxysigweights_ParTScoreD_${y}.root
    done

    for y in 2022pre 2022post 2023pre 2023post 2024
    do
        python3 deriveWeights.py --numerator ${IN}/jetmet_${y}_hist.root:${HIST} --denominator ${IN}/background_${y}_hist.root:${HIST} --name w_LxySig_${sel} --normalize --edges ${EDGES} --output lxysigweights_ParTScoreD_${y}.root
    done
done
