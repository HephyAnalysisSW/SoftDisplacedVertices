for sel in all tight
do
    for y in 2017 2018 #run2
    do
        python3 compare_data_new.py --data ${1}/met${y}_hist.root --bkg ${1}/st_${y}_hist.root ${1}/ttbar_${y}_hist.root ${1}/qcd_${y}_hist.root ${1}/wjets_${y}_hist.root ${1}/zjets_${y}_hist.root  --bkgnice "Single top" "TTbar" "QCD" "WJets" "ZJets" --output /groups/hephy/cms/ang.li/SDV/${2}/${y}/${sel}/MLlow0 --dirs "All_RotateVtx_${sel}" --ratio --commands "(h.GetXaxis().SetRangeUser(0.0,1),h.Rebin(10)) if ('MLScore' in h.GetName()) else h.GetXaxis().SetRangeUser(1.5,2.3) if ('mass_before' in h.GetName()) else (h.GetXaxis().SetRangeUser(0,1)) if ('Lxy' in h.GetName()) else None"
        #for MLlow in 0 8 99
        for MLlow in  8 99
        do
            python3 compare_data_new.py --data ${1}/met${y}_hist.root --bkg ${1}/st_${y}_hist.root ${1}/ttbar_${y}_hist.root ${1}/qcd_${y}_hist.root ${1}/wjets_${y}_hist.root ${1}/zjets_${y}_hist.root  --bkgnice "Single top" "TTbar" "QCD" "WJets" "ZJets" --output /groups/hephy/cms/ang.li/SDV/${2}/${y}/${sel}/MLlow${MLlow} --dirs "All_RotateVtx_${sel}" --ratio --commands "(h.GetXaxis().SetRangeUser(0.${MLlow},1)) if ('MLScore' in h.GetName()) else h.GetXaxis().SetRangeUser(1.5,2.3) if ('mass_before' in h.GetName()) else (h.GetXaxis().SetRangeUser(0,1)) if ('Lxy' in h.GetName())  else None"
        done
    done
    
    for y in 2022pre 2022post 2023pre 2023post
    do
        python3 compare_data_new.py --data ${1}/jetmet_${y}_hist.root --bkg ${1}/ttbar_${y}_hist.root ${1}/qcd_${y}_hist.root ${1}/wjets_${y}_hist.root ${1}/zjets_${y}_hist.root  --bkgnice "TTbar" "QCD" "WJets" "ZJets" --output /groups/hephy/cms/ang.li/SDV/${2}/${y}/${sel}/MLlow0 --dirs "All_RotateVtx_${sel}" --ratio --commands "(h.GetXaxis().SetRangeUser(0,1),h.Rebin(10)) if ('MLScore' in h.GetName()) else (h.GetXaxis().SetRangeUser(0,1)) if ('Lxy' in h.GetName())  else None"
        for MLlow in 8 99
        do
            python3 compare_data_new.py --data ${1}/jetmet_${y}_hist.root --bkg ${1}/ttbar_${y}_hist.root ${1}/qcd_${y}_hist.root ${1}/wjets_${y}_hist.root ${1}/zjets_${y}_hist.root  --bkgnice "TTbar" "QCD" "WJets" "ZJets" --output /groups/hephy/cms/ang.li/SDV/${2}/${y}/${sel}/MLlow${MLlow} --dirs "All_RotateVtx_${sel}" --ratio --commands "h.GetXaxis().SetRangeUser(0.${MLlow},1) if ('MLScore' in h.GetName())  else (h.GetXaxis().SetRangeUser(0,1)) if ('Lxy' in h.GetName()) else None"
        done
    done
done
