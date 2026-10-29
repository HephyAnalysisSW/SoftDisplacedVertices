for y in 2017 2018
do
    python3 deriveWeights.py --numerator /scratch-cbe/users/ang.li/SoftDV/Histos/Histos_RotateD_dxydz_3/met${y}_hist.root:All_RotateVtx_all/RotateVtx_mass_before --denominator /scratch-cbe/users/ang.li/SoftDV/Histos/Histos_RotateD_dxydz_3/background_${y}_hist.root:All_RotateVtx_all/RotateVtx_mass_before --name w_mass --normalize  --output massweights_all_${y}.root 
done

for y in 2022pre 2022post 2023pre 2023post
do
    python3 deriveWeights.py --numerator /scratch-cbe/users/ang.li/SoftDV/Histos/Histos_RotateD_dxydz_3/jetmet_${y}_hist.root:All_RotateVtx_all/RotateVtx_mass_before --denominator /scratch-cbe/users/ang.li/SoftDV/Histos/Histos_RotateD_dxydz_3/background_${y}_hist.root:All_RotateVtx_all/RotateVtx_mass_before --name w_mass --normalize  --output massweights_all_${y}.root 
done
