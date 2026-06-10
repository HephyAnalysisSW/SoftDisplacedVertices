#hadd ${1}/met2017_hist.root ${1}/met2017*_hist.root
#hadd ${1}/wjets_2017_hist.root ${1}/wjetstolnuht*2017_hist.root 
#hadd ${1}/zjets_2017_hist.root ${1}/zjetstonunuht*2017_hist.root 
#hadd ${1}/qcd_2017_hist.root ${1}/qcdht*2017_hist.root 
#hadd ${1}/st_2017_hist.root ${1}/st_*_2017_hist.root
#hadd ${1}/background_2017_hist.root ${1}/wjets_2017_hist.root ${1}/zjets_2017_hist.root ${1}/qcd_2017_hist.root ${1}/st_2017_hist.root ${1}/ttbar_2017_hist.root
#
hadd ${1}/met2018_hist.root ${1}/met2018*_hist.root
hadd ${1}/wjets_2018_hist.root ${1}/wjetstolnuht*2018_hist.root 
hadd ${1}/zjets_2018_hist.root ${1}/zjetstonunuht*2018_hist.root 
hadd ${1}/qcd_2018_hist.root ${1}/qcdht*2018_hist.root 
hadd ${1}/st_2018_hist.root ${1}/st_*_2018_hist.root
hadd ${1}/background_2018_hist.root ${1}/wjets_2018_hist.root ${1}/zjets_2018_hist.root ${1}/qcd_2018_hist.root ${1}/st_2018_hist.root ${1}/ttbar_2018_hist.root

#hadd ${1}/met2017_hist.root ${1}/met2017*_hist.root
#hadd ${1}/wjets_2017_hist.root ${1}/wjetstolnuht*2017_hist.root 
#hadd ${1}/zjets_2017_hist.root ${1}/zjetstonunuht*2017_hist.root 
#hadd ${1}/qcd_2017_hist.root ${1}/qcdht*2017_hist.root 
#hadd ${1}/st_2017_hist.root ${1}/st_*_2017_hist.root
#hadd ${1}/background_2017_hist.root ${1}/wjets_2017_hist.root ${1}/zjets_2017_hist.root ${1}/qcd_2017_hist.root ${1}/st_2017_hist.root ${1}/ttbar_2017_hist.root
#
#for n in background_  zjets_ wjets_ ttbar_ st_ qcd_  met #stop_M600_588_ct200_ stop_M600_585_ct20_ stop_M600_580_ct2_ #stop_M600_575_ct0p2_ background_partial_
#do
#  hadd ${1}/${n}run2_hist.root ${1}/${n}2017_hist.root ${1}/${n}2018_hist.root
#done
