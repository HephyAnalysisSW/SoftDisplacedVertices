for s in 'All' 'GT0' 'GT1' 'GT2' 'GTgt2' 'GTgt3'
do
  #for o in '_evt' '_SDVSecVtx_all' '_SDVSecVtx_ML0p99' '_SDVSecVtx_ML0p999' '_SDVSecVtx_dphiMET' '_SDVSecVtx_SR' '_SDVSecVtx_leading' '_SDVSecVtx_leading_A' '_SDVSecVtx_leading_B' '_SDVSecVtx_leading_C' '_SDVSecVtx_leading_D'
  for o in '_evt' '_SDVSecVtx_all' '_SDVSecVtx_leading' '_SDVSecVtx_leading_A' '_SDVSecVtx_leading_B' '_SDVSecVtx_leading_C' '_SDVSecVtx_leading_D'
  do
    #python3 compare.py --input /eos/vbc/group/cms/ang.li/DataHistos_VRCR2/met2018_hist.root /eos/vbc/group/cms/ang.li/MCHistos_VRCR2/background_2018_hist.root --dirs "$s$o" --nice "Data" "Simulation" --output /groups/hephy/cms/ang.li/SDV/DataMCComp2_$s$o --commands "h.Rebin(5) if ('LxySig' in h.GetName()) else None" --datamc --ratio
    python3 compare_data_new.py --data ${1}/met2018_hist.root --bkg ${1}/st_2018_hist.root ${1}/ttbar_2018_hist.root ${1}/qcd_2018_hist.root ${1}/wjets_2018_hist.root ${1}/zjets_2018_hist.root  --bkgnice "Single top" "TTbar" "QCD" "WJets" "ZJets" --signal ${1}/C1N2ML_M200_195_ct20_2018_hist.root ${1}/C1N2ML_M200_185_ct20_2018_hist.root --signice "dm=5GeV" "dm=15GeV" --output /groups/hephy/cms/ang.li/SDV/HistComp_2018_run23_VR_${1}_$s$o --dirs "$s$o" --commands "h.Rebin(5) if ('LxySig' in h.GetName()) else h.GetXaxis().SetRangeUser(0,20) if ('pfRel' in  h.GetName()) else None" --ratio 
  done
done

for s in 'All' 'GT0' 'GT1' 'GT2' 'GTgt2' 'GTgt3'
do
  #for o in '_evt' '_SDVSecVtx_all' '_SDVSecVtx_ML0p99' '_SDVSecVtx_ML0p999' '_SDVSecVtx_dphiMET' '_SDVSecVtx_SR' '_SDVSecVtx_leading' '_SDVSecVtx_leading_A' '_SDVSecVtx_leading_B' '_SDVSecVtx_leading_C' '_SDVSecVtx_leading_D'
  for o in '_evt' '_SDVSecVtx_all' '_SDVSecVtx_leading' '_SDVSecVtx_leading_A' '_SDVSecVtx_leading_B' '_SDVSecVtx_leading_C' '_SDVSecVtx_leading_D'
  do
    python3 compare_data_new.py  --bkg ${1}/st_2018_hist.root ${1}/ttbar_2018_hist.root ${1}/qcd_2018_hist.root ${1}/wjets_2018_hist.root ${1}/zjets_2018_hist.root  --bkgnice "Single top" "TTbar" "QCD" "WJets" "ZJets" --signal ${1}/C1N2ML_M200_195_ct20_2018_hist.root ${1}/C1N2ML_M200_185_ct20_2018_hist.root --signice "dm=5GeV" "dm=15GeV" --output /groups/hephy/cms/ang.li/SDV/SigBkgComp_2018_run23_VR_${2}_$s$o --dirs "$s$o" --commands "h.Rebin(5) if ('LxySig' in h.GetName()) else h.GetXaxis().SetRangeUser(0,20) if ('pfRel' in  h.GetName()) else None" --norm
  done
done

