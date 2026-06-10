for gt in 0 1 2 gt3
do
    for r in A B C D
    do
        python3 compare.py --input /scratch-cbe/users/ang.li/SoftDV/Histos/Histos_Run2_VRs_ntkfirst_regions/background_2018_hist.root --dirs "MET200GT${gt}${r}_evt" "MET250GT${gt}${r}_evt" "MET300GT${gt}${r}_evt" "MET350GT${gt}${r}_evt" --nice "200<MET<250" "250<MET<300" "300<MET<350" "350<MET"  --output /groups/hephy/cms/ang.li/SDV/CompHistos_METevt_bkg_2018_GT${gt}${r} --command "h.GetXaxis().SetRangeUser(0,20) if ('nSDVTrack' in h.GetName()) or ('nGoodTrack' in h.GetName()) else None" --scale 
    done
done

for MET in "" "MET200" "MET250" "MET300" "MET350"
do
    for r in A B C D
    do
        python3 compare.py --input /scratch-cbe/users/ang.li/SoftDV/Histos/Histos_Run2_VRs_ntkfirst_regions/background_2018_hist.root --dirs "${MET}GT0${r}_evt" "${MET}GT1${r}_evt" "${MET}GT2${r}_evt" "${MET}GTgt3${r}_evt" --nice "GT0" "GT1" "GT2" "GT>=3"  --output /groups/hephy/cms/ang.li/SDV/CompHistos_GTevt_bkg_2018_${MET}${r} --command "h.GetXaxis().SetRangeUser(0,20) if ('nSDVTrack' in h.GetName()) or ('nGoodTrack' in h.GetName()) else None" --scale
    done
done

#for s in 'GT0' 'GT1' 'GT2' 'GTgt3'
#do
#    python3 compare.py --input ${1}/background_2018_hist.root --dirs "MET${m}${s}_SDVSecVtx_leading_ML0p5" "MET${m}${s}_SDVSecVtx_leading_ML0p8" "MET${m}${s}_SDVSecVtx_leading_ML0p9" "MET${m}${s}_SDVSecVtx_leading_ML0p95" "MET${m}${s}_SDVSecVtx_leading_ML0p99" "MET${m}${s}_SDVSecVtx_leading_ML0p995" "MET${m}${s}_SDVSecVtx_leading_ML0p999" "MET${m}${s}_SDVSecVtx_leading_ML1" --nice "0.2<ML<0.5" "0.5<ML<0.8" "0.8<ML<0.9" "0.9<ML<0.95" "0.95<ML<0.99" "0.99<ML<0.995" "0.995<ML<0.999" "0.999<ML<1" --output /groups/hephy/cms/ang.li/SDV/CompHistos_${2}_MET${m}${s} --command "h.Rebin(4) if h.GetName()=='SDVSecVtx_dphiMET' else None" --scale
#done
