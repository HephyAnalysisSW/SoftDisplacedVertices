# Per-year shape weights (data/MC, both normalised) for background MC on the vertex Lxy (cm) of the
# rotation candidates, from the UNWEIGHTED ParTScore_D RotateK0_trigSF histograms (selection 'all').
# Variable bins; the last bin [10, 1000] cm includes the histogram overflow (Lxy > 10 cm).
# Outputs lxyweights_ParTScoreD_<year>.root (hist w_Lxy). Not to be combined with the mass weights.
IN=/scratch-cbe/users/ang.li/SoftDV/Histos/Histos_ParTScoreD_RotateK0_trigSF
HIST=All_RotateVtx_all/RotateVtx_Lxy
EDGES="0 0.02 0.05 0.1 0.2 0.3 0.5 1 2 3 5 10 1000"

for y in 2017 2018
do
    python3 deriveWeights.py --numerator ${IN}/met${y}_hist.root:${HIST} --denominator ${IN}/background_${y}_hist.root:${HIST} --name w_Lxy --normalize --edges ${EDGES} --output lxyweights_ParTScoreD_${y}.root
done

for y in 2022pre 2022post 2023pre 2023post 2024
do
    python3 deriveWeights.py --numerator ${IN}/jetmet_${y}_hist.root:${HIST} --denominator ${IN}/background_${y}_hist.root:${HIST} --name w_Lxy --normalize --edges ${EDGES} --output lxyweights_ParTScoreD_${y}.root
done
