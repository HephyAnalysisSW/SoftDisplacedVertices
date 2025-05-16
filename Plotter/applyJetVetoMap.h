#ifndef applyJetVetoMap_h
#define applyJetVetoMap_h

#include "ROOT/RDataFrame.hxx"
#include "ROOT/RVec.hxx"
#include "TH2D.h"

ROOT::RVecB applyJetVetoMap(ROOT::RVecF Jet_pt, ROOT::RVecF Jet_eta, ROOT::RVecF Jet_phi,
                            ROOT::RVecI Jet_jetId, ROOT::RVecF Jet_chEmEF, ROOT::RVecF Jet_neEmEF,
                            ROOT::RVecI Jet_muonIdx1, ROOT::RVecI Jet_muonIdx2, 
                            TH2D* h_veto_map, std::string year){
    size_t nJet = Jet_pt.size();
    ROOT::RVecB jet_selection(nJet, false);

    // Define the years for which the veto map is applicable
    // .count() on unordered set will yield either 0, or 1.
    static const std::unordered_set<std::string> Run3_years = {
        "2023", "2023BPix"
    };

    for (size_t i=0; i<nJet; i++){
        if (Run3_years.count(year)){
                                                       // Ref: https://cms-jerc.web.cern.ch/Recommendations/#2023
            bool isTight = (Jet_jetId[i] & (1 << 2));  // check if bit 2 is set (shifting 1 to bit 2 0000001 -> 0000100)
            if ((Jet_pt[i] > 15) && (isTight) && ((Jet_chEmEF[i] + Jet_neEmEF[i]) < 0.9) && (Jet_muonIdx1[i] == -1) && (Jet_muonIdx2[i] == -1)){
                bool inVetoRegion = (h_veto_map->GetBinContent(h_veto_map->FindBin(Jet_eta[i], Jet_phi[i])) > 0.01);
                jet_selection[i] = inVetoRegion;
            }
        }
    }
    return jet_selection;
}

#endif