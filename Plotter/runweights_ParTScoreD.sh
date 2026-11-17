# Per-year shape weights (data/MC, both normalised) for background MC on the pre-rotation
# K pi pi mass, from the ParTScore_D RotateK0_trigSF histograms (selection 'all').
# Same recipe as runweights.sh; outputs massweights_ParTScoreD_<year>.root (hist w_mass).
IN=/scratch-cbe/users/ang.li/SoftDV/Histos/Histos_ParTScoreD_RotateK0_trigSF
HIST=All_RotateVtx_all/RotateVtx_mass_before

for y in 2017 2018
do
    python3 deriveWeights.py --numerator ${IN}/met${y}_hist.root:${HIST} --denominator ${IN}/background_${y}_hist.root:${HIST} --name w_mass --normalize --output massweights_ParTScoreD_${y}.root
done

for y in 2022pre 2022post 2023pre 2023post 2024
do
    python3 deriveWeights.py --numerator ${IN}/jetmet_${y}_hist.root:${HIST} --denominator ${IN}/background_${y}_hist.root:${HIST} --name w_mass --normalize --output massweights_ParTScoreD_${y}.root
done
