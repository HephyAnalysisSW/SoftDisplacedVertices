#include "ROOT/RDataFrame.hxx"
#include "ROOT/RVec.hxx"
#include "TCanvas.h"
#include "TH1D.h"
#include "TLatex.h"
#include "TString.h"
#include "Math/Vector4D.h"
#include "TStyle.h"
#include <algorithm> 
#include <string>
#include <map>
#include <assert.h>
#include <optional>
#include "correction.h"

inline bool hasPhiDependentL2(const std::string& year) {
    return (year == "2023Post" || year == "2024" || year == "2025");
}
inline bool requiresRunBasedResidual(const std::string& year) {
    return (year == "2023Pre" || year == "2023Post" || year == "2024" || year == "2025");
}

//inline double dummyRunNumber(const int& run, const std::string& year) {
//    if (year == "2023Pre")  return 367080.0;
//    if (year == "2023Post") return 369803.0;
//    if (year == "2024")     return 379412.0;
//    if (year == "2025")     return 392159.0;
//    return static_cast<double>(run);
//}

std::pair<std::string,std::string> getEra(double run_number) {
    std::vector<int> runs({352319, 355065, 355794, 357487, 359022, 360332, 362350, 367080, 369803, 378981});
    //std::vector<std::string> eras({"2022A","2022B","2022C","2022D","2022E","2022F","2022G","2023C","2023D","2024"});
    std::vector<std::pair<std::string,std::string>> eras = {
        {"2022Pre","Era2022A"}, //352319
        {"2022Pre","Era2022B"}, //355065
        {"2022Pre","Era2022C"}, //355794
        {"2022Pre","Era2022D"}, //357487
        {"2022Post","Era2022E"}, //359022
        {"2022Post","Era2022F"}, //360332
        {"2022Post","Era2022G"}, //362350
        {"2023Pre","Era2023PreAll"}, //367080
        {"2023Post","Era2023PostAll"}, //369803
        {"2024","Era2024All"} //378981
    };
    auto pos = std::upper_bound(runs.begin(),runs.end(),run_number)-runs.begin()-1;
    if (pos<0){
        return std::pair<std::string,std::string>({"NA","NA"});
    }
    if (static_cast<size_t>(pos)>(runs.size()-1)){
        throw std::runtime_error("Year: Run number out of run ranges!");
    }
    return eras[pos];
}

inline void validateYearEraMatch(const std::string& requested_year, const int& run, const std::pair<std::string,std::string>& era) {
    if (requested_year != era.first) {
        throw std::runtime_error(
            "JERC year/era mismatch: requested year '" + requested_year +
            "' but run " + std::to_string(run) + " belongs to '" + era.first +
            "' (" + era.second + "). Check that the input files match the --year setting."
        );
    }
}

// Returns std::pair: first -- new jet pt, second -- new jet mass
std::pair<ROOT::RVecF,ROOT::RVecF> JEC_jet(const std::vector<correction::Correction::Ref>& jes, const std::string& year, const bool& isData, const int& run, const ROOT::RVecF& jet_area, const ROOT::RVecF& jet_eta, const ROOT::RVecF& jet_phi, const ROOT::RVecF& jet_pt, const ROOT::RVecF& jet_mass, const ROOT::RVecF& jet_rawFactor, const float& rho) {
    //std::cout << "JEC year " << year << " run " << run << std::endl;
    // input: jes -- a vector of corrections in order: L1, L2, L2L3 (L2L3 is data only)
    //std::cout << "Before JEC ";
    //for (auto & ijp:jet_pt) {
    //    std::cout << ijp << ", ";
    //}
    //std::cout << std::endl;
    ROOT::RVecF jet_pt_corr;
    ROOT::RVecF jet_mass_corr;
    for (size_t i=0; i<jet_pt.size(); ++i) {
        // calculate the jes factor
        double pt_raw = jet_pt[i]*(1.0-jet_rawFactor[i]);
        double mass_raw = jet_mass[i]*(1.0-jet_rawFactor[i]);

        //std::cout << "jet " << i << " pt " << jet_pt[i] << " pt raw " << pt_raw << std::endl;

        double pt_corr = pt_raw;
        double mass_corr = mass_raw;

        // L1FastJet
        const double c1 = jes[0]->evaluate({jet_area[i],jet_eta[i],pt_corr,rho}); 
        pt_corr = pt_corr * c1;
        mass_corr = mass_corr * c1;
        //std::cout << "L1 c1 " << c1 << " pt " << pt_corr << std::endl;

        // L2Relative
        double c2 = 1.0;
        if (hasPhiDependentL2(year)) {
            c2 = jes[1]->evaluate({jet_eta[i],jet_phi[i],pt_corr});
        }
        else {
            c2 = jes[1]->evaluate({jet_eta[i],pt_corr});
        }

        pt_corr = pt_corr * c2;
        mass_corr = mass_corr * c2;
        //std::cout << "L2 c2 " << c2 << " pt " << pt_corr << std::endl;

        // L2L3Residual (Data only)
        if (isData) {
            if (jes.size()<3)
                throw std::runtime_error("Data requires L2L3Residual ref");
            double cRes = 1.0;
            if (requiresRunBasedResidual(year)) {
                cRes = jes[2]->evaluate({static_cast<float>(run),jet_eta[i],pt_corr});
            }
            else {
                cRes = jes[2]->evaluate({jet_eta[i],pt_corr});
            }
            pt_corr = pt_corr * cRes;
            mass_corr = mass_corr * cRes;
            //std::cout << "L2L3 cRes " << cRes << " pt " << pt_corr << std::endl;
        }
        //std::cout << "After corr " << pt_corr << std::endl;
        //std::cout << std::endl;
        jet_pt_corr.push_back(pt_corr);
        jet_mass_corr.push_back(mass_corr);
    }
    //std::cout << "After JEC ";
    //for (auto & ijp:jet_pt_corr) {
    //    std::cout << ijp << ", ";
    //}
    //std::cout << std::endl;
    return std::pair<ROOT::RVecF,ROOT::RVecF>({jet_pt_corr,jet_mass_corr});
}

// Returns std::pair: first -- new jet pt, second -- new jet mass
std::pair<ROOT::RVecF,ROOT::RVecF> JER_jet_MC(const std::vector<correction::Correction::Ref>& jer, const std::string& year, const int& event, const ROOT::RVecF& jet_area, const ROOT::RVecF& jet_eta, const ROOT::RVecF& jet_phi, const ROOT::RVecF& jet_pt, const ROOT::RVecF& jet_mass, const float& rho, const ROOT::RVecI& jet_genJetIdx, const ROOT::RVecF& genJet_pt, const ROOT::RVecF& genJet_eta, const ROOT::RVecF& genJet_phi) {
    // input: jer -- a vector of corrections in order: ptResolution, scaleFactor, smearing
    ROOT::RVecF jet_pt_jer;
    ROOT::RVecF jet_mass_jer;
    for(size_t i=0; i<jet_pt.size(); ++i) {
        //std::cout << "JER jet " << i << jet_pt[i] << std::endl;
        // calculate resolution and scale factor
        double reso = jer[0]->evaluate({jet_eta[i],jet_pt[i],rho});
        double sf = jer[1]->evaluate({jet_eta[i],jet_pt[i],"nom"});
        //std::cout << " sf " << sf << " reso " << reso << std::endl;

        // check gen jet
        double genPtForSmear = -1.0;
        int genIdx = jet_genJetIdx[i];
        if ( (genIdx > -1) && (static_cast<UInt_t>(genIdx) < genJet_pt.size()) ) {
            float genpt = genJet_pt[genIdx];
            float geneta = genJet_eta[genIdx];
            float genphi = genJet_phi[genIdx];

            double dR = ROOT::VecOps::DeltaR(jet_eta[i], geneta, jet_phi[i], genphi);
            if ( (dR<0.2) && (std::abs(jet_pt[i]-genpt) < 3.0 * reso * jet_pt[i]) ) {
                genPtForSmear = genpt;
                //std::cout << "Gen matched dr " << dR << std::endl;
            }
        }
        std::vector<correction::Variable::Type> vals;
        vals.reserve(7);
        vals.emplace_back(static_cast<double>(jet_pt[i]));   // JetPt
        vals.emplace_back(static_cast<double>(jet_eta[i]));  // JetEta
        vals.emplace_back(static_cast<double>(genPtForSmear));  // GenPt or -1
        vals.emplace_back(static_cast<double>(rho));  // Rho
        vals.emplace_back(static_cast<int>(event));         // EventID
        vals.emplace_back(static_cast<double>(reso));           // JER
        vals.emplace_back(static_cast<double>(sf));             // JERSF

        const double smear = jer[2]->evaluate(vals);
        const double corr = (std::isfinite(smear) && smear > 0.0) ? smear : 1.0;
        //std::cout << " JER corr input pt " << jet_pt[i] << " eta " << jet_eta[i] << " gen pt " << genPtForSmear << " rho " << rho << " event " << event << " reso " << reso << " sf " << sf << std::endl; 

        //std::cout << " JER corr " << corr << std::endl;

        jet_pt_jer.push_back(jet_pt[i]*corr);
        jet_mass_jer.push_back(jet_mass[i]*corr);
    }
    //std::cout << "After JER ";
    //for (auto & ijp:jet_pt_jer) {
    //    std::cout << ijp << ", ";
    //}
    //std::cout << std::endl;
    return std::pair<ROOT::RVecF,ROOT::RVecF>({jet_pt_jer,jet_mass_jer});
}

std::pair<ROOT::RVecF,ROOT::RVecF> JERC_jet_data(const std::map<std::string,correction::Correction::Ref>& jerc, const std::string& year, const int& run, const int& event, const ROOT::RVecF& jet_area, const ROOT::RVecF& jet_eta, const ROOT::RVecF& jet_phi, const ROOT::RVecF& jet_pt, const ROOT::RVecF& jet_mass, const ROOT::RVecF& jet_rawFactor, const float& rho) {
    // For Data
    // Determine the data-taking era
    auto era = getEra(run);
    validateYearEraMatch(year, run, era);
    std::vector<std::string> corrs_names = {"L1","L2","L2L3"};
    std::vector<correction::Correction::Ref> jes_refs = {};
    for (auto& n : corrs_names) {
        auto jerc_iter = jerc.find("data_jes_"+n+"_"+era.second);
        if (jerc_iter==jerc.end()) {
            throw std::runtime_error("Correction ref for "+n+" "+era.second+" not found!");
        }
        jes_refs.push_back(jerc_iter->second);
    }
    auto jets = JEC_jet(jes_refs, year, true, run, jet_area, jet_eta, jet_phi, jet_pt, jet_mass, jet_rawFactor, rho);
    return jets;
}

std::pair<ROOT::RVecF,ROOT::RVecF> JERC_jet_MC(const std::map<std::string,correction::Correction::Ref>& jerc, const std::string& year, const int& run, const int& event, const ROOT::RVecF& jet_area, const ROOT::RVecF& jet_eta, const ROOT::RVecF& jet_phi, const ROOT::RVecF& jet_pt, const ROOT::RVecF& jet_mass, const ROOT::RVecF& jet_rawFactor, const float& rho, const ROOT::RVecI& jet_genJetIdx, const ROOT::RVecF& genJet_pt, const ROOT::RVecF& genJet_eta, const ROOT::RVecF& genJet_phi) {
    // For MC
    std::vector<std::string> corrs_names = {"L1","L2"};
    std::vector<correction::Correction::Ref> jes_refs = {};
    for (auto& n : corrs_names) {
        auto jerc_iter = jerc.find("MC_jes_"+n);
        if (jerc_iter==jerc.end()) {
            throw std::runtime_error("Correction ref for "+n+" not found!");
        }
        jes_refs.push_back(jerc_iter->second);
    }
    auto jer_reso_iter = jerc.find("MC_jer_reso");
    auto jer_sf_iter = jerc.find("MC_jer_sf");
    auto jer_smear_iter = jerc.find("MC_jer_smear");
    if (jer_reso_iter==jerc.end()) {
        throw std::invalid_argument("Correction ref for MC jer resolution not found!");
    }
    if (jer_sf_iter==jerc.end()) {
        throw std::invalid_argument("Correction ref for MC jer scale factor not found!");
    }
    if (jer_smear_iter==jerc.end()) {
        throw std::invalid_argument("Correction ref for MC jer smear not found!");
    }
    auto jets_jec = JEC_jet(jes_refs, year, false, run, jet_area, jet_eta, jet_phi, jet_pt, jet_mass, jet_rawFactor, rho);
    std::vector<correction::Correction::Ref> jer_refs = {jer_reso_iter->second, jer_sf_iter->second, jer_smear_iter->second};
    auto jets_jecjer = JER_jet_MC(jer_refs, year, event, jet_area, jet_eta, jet_phi, jets_jec.first, jets_jec.second, rho, jet_genJetIdx, genJet_pt, genJet_eta, genJet_phi);
    return jets_jecjer;
}

//std::pair<ROOT::RVecF,ROOT::RVecF> JERC_jet(const std::map<std::string,correction::Correction::Ref>& jerc, const bool& isData, const std::string& year, const int& run, const int& event, const ROOT::RVecF& jet_area, const ROOT::RVecF& jet_eta, const ROOT::RVecF& jet_phi, const ROOT::RVecF& jet_pt, const ROOT::RVecF& jet_mass, const ROOT::RVecF& jet_rawFactor, const float& rho, const std::optional<ROOT::RVecI>& jet_genJetIdx, const std::optional<ROOT::RVecF>& genJet_pt, const std::optional<ROOT::RVecF>& genJet_eta, const std::optional<ROOT::RVecF>& genJet_phi) {
//std::pair<ROOT::RVecF,ROOT::RVecF> JERC_jet(const std::map<std::string,correction::Correction::Ref>& jerc, const bool& isData, const std::string& year, const int& run, const int& event, const ROOT::RVecF& jet_area, const ROOT::RVecF& jet_eta, const ROOT::RVecF& jet_phi, const ROOT::RVecF& jet_pt, const ROOT::RVecF& jet_mass, const ROOT::RVecF& jet_rawFactor, const float& rho, const ROOT::RVecI& jet_genJetIdx={}, const ROOT::RVecF& genJet_pt={}, const ROOT::RVecF& genJet_eta={}, const ROOT::RVecF& genJet_phi={}) {
//    if ( (!isData) && (jet_genJetIdx.size()==0 || genJet_pt.size()==0 || genJet_eta.size()==0 || genJet_phi.size()==0) ) {
//        throw std::invalid_argument("JERC_jet: Gen info not provided for MC!");
//    }
//    if (isData) {
//        return JERC_jet_data(jerc, year, run, event, jet_area, jet_eta, jet_phi, jet_pt, jet_mass, jet_rawFactor, rho);
//    }
//    else {
//        return JERC_jet_MC(jerc, year, run, event, jet_area, jet_eta, jet_phi, jet_pt, jet_mass, jet_rawFactor, rho, jet_genJetIdx, genJet_pt, genJet_eta, genJet_phi);
//    }
//}


ROOT::RVecI genJetIdx_CorrT1METJet(const ROOT::RVecF& CorrT1METJet_eta, const ROOT::RVecF& CorrT1METJet_phi, const ROOT::RVecF& genJet_eta, const ROOT::RVecF& genJet_phi) {
    ROOT::RVecI idx;
    for (size_t ij=0; ij<CorrT1METJet_eta.size(); ++ij){
        float eta = CorrT1METJet_eta[ij];
        float phi = CorrT1METJet_phi[ij];
        float bestdR = 1e9f;
        int bestid = -1;
        for (size_t ig=0; ig<genJet_eta.size(); ++ig) {
            double dR = ROOT::VecOps::DeltaR(eta, genJet_eta[ig], phi, genJet_phi[ig]);
            if (dR<0.2 && dR<bestdR) {
                bestdR = dR;
                bestid = static_cast<int>(ig);
            }
        }
        idx.push_back(bestid);
    }
    return idx;
}

//std::pair<float,float> JERC_MET(const std::map<std::string,correction::Correction::Ref>& jerc, const bool& isData, const std::string& year, const int& run, const int& event, const float& MET_pt, const float& MET_phi, const ROOT::RVecF& jet_area, const ROOT::RVecF& jet_eta, const ROOT::RVecF& jet_phi, const ROOT::RVecF& jet_pt, const ROOT::RVecF& jet_rawFactor, const ROOT::RVecF& jet_muonSubtrFactor, const ROOT::RVecF& jet_chEmEF, const ROOT::RVecF& jet_neEmEF, const float& rho, const std::optional<ROOT::RVecI>& jet_genJetIdx, const std::optional<ROOT::RVecF>& genJet_pt, const std::optional<ROOT::RVecF>& genJet_eta, const std::optional<ROOT::RVecF>& genJet_phi) {
std::pair<float,float> JERC_MET(const std::map<std::string,correction::Correction::Ref>& jerc, const bool& isData, const std::string& year, const int& run, const int& event, const float& MET_pt, const float& MET_phi, const ROOT::RVecF& jet_area, const ROOT::RVecF& jet_eta, const ROOT::RVecF& jet_phi, const ROOT::RVecF& jet_pt, const ROOT::RVecF& jet_rawFactor, const ROOT::RVecF& jet_muonSubtrFactor, const ROOT::RVecF& jet_chEmEF, const ROOT::RVecF& jet_neEmEF, const float& rho, const ROOT::RVecI& jet_genJetIdx, const ROOT::RVecF& genJet_pt, const ROOT::RVecF& genJet_eta, const ROOT::RVecF& genJet_phi) {
    //std::cout << "year " << year << " run " << run << " event " << event << std::endl;
    //std::cout << "MET pt" << MET_pt << " phi " << MET_phi << std::endl;

    assert( (jet_area.size()==jet_eta.size()==jet_phi.size()==jet_pt.size()==jet_rawFactor.size()==jet_muonSubtrFactor.size()==jet_chEmEF.size()==jet_neEmEF.size()) );

    std::vector<correction::Correction::Ref> jes = {};
    std::vector<correction::Correction::Ref> jer = {};
    if (isData) {
        auto era = getEra(run);
        validateYearEraMatch(year, run, era);
        std::vector<std::string> corrs_names = {"L1","L2","L2L3"};
        for (auto& n : corrs_names) {
            auto jerc_iter = jerc.find("data_jes_"+n+"_"+era.second);
            if (jerc_iter==jerc.end()) {
                throw std::runtime_error("Correction ref for "+n+" "+era.second+" not found!");
            }
            jes.push_back(jerc_iter->second);
        }
    }
    else {
        std::vector<std::string> corrs_names = {"L1","L2"};
        for (auto& n : corrs_names) {
            auto jerc_iter = jerc.find("MC_jes_"+n);
            if (jerc_iter==jerc.end()) {
                throw std::runtime_error("Correction ref for "+n+" not found!");
            }
            jes.push_back(jerc_iter->second);
        }
        auto jer_reso_iter = jerc.find("MC_jer_reso");
        auto jer_sf_iter = jerc.find("MC_jer_sf");
        auto jer_smear_iter = jerc.find("MC_jer_smear");
        if (jer_reso_iter==jerc.end()) {
            throw std::invalid_argument("Correction ref for MC jer resolution not found!");
        }
        if (jer_sf_iter==jerc.end()) {
            throw std::invalid_argument("Correction ref for MC jer scale factor not found!");
        }
        if (jer_smear_iter==jerc.end()) {
            throw std::invalid_argument("Correction ref for MC jer smear not found!");
        }
        jer = {jer_reso_iter->second, jer_sf_iter->second, jer_smear_iter->second};
    }

    float met_px = MET_pt * std::cos(MET_phi);
    float met_py = MET_pt * std::sin(MET_phi);
    //std::cout << "Before corr met px " << met_px << " py " << met_py << std::endl;

    for (size_t i=0; i<jet_pt.size(); ++i) {
        // raw jet pt 
        const double ptRaw = jet_pt[i]*(1.0-jet_rawFactor[i]);

        // Muon-subtracted raw pt
        const double ptRawMinusMuon = ptRaw * (1.0-jet_muonSubtrFactor[i]);
        //std::cout << "jet " << i << " pt " << jet_pt[i] << " ptraw " << ptRaw << "ptRawMinusMuon" << ptRawMinusMuon << std::endl;

        double pt_corr = ptRawMinusMuon;
        // L1
        const double c1 = jes[0]->evaluate({jet_area[i],jet_eta[i],pt_corr,rho});
        pt_corr = pt_corr * c1;
        //std::cout << "L1 c1 " << c1 << " ptcorr " << pt_corr << std::endl;
        const double pt_corrL1 = pt_corr;

        // L2
        double c2 = 1.0;
        if (hasPhiDependentL2(year)) {
            c2 = jes[1]->evaluate({jet_eta[i],jet_phi[i],pt_corr});
        }
        else {
            c2 = jes[1]->evaluate({jet_eta[i],pt_corr});
        }

        pt_corr = pt_corr * c2;
        //std::cout << "L2 c2 " << c2 << " ptcorr " << pt_corr << std::endl;

        // Residual (Data only)
        if (isData) {
            if (jes.size()<3)
                throw std::runtime_error("Data requires L2L3Residual ref");
            double cRes = 1.0;
            if (requiresRunBasedResidual(year)) {
                cRes = jes[2]->evaluate({static_cast<float>(run),jet_eta[i],pt_corr});
            }
            else {
                cRes = jes[2]->evaluate({jet_eta[i],pt_corr});
            }
            pt_corr = pt_corr * cRes;
            //std::cout << "L2L3 cRes " << cRes << " ptcorr " << pt_corr << std::endl;
        }

        // JER (MC Only)
        if (!isData) {
            // calculate resolution and scale factor
            double reso = jer[0]->evaluate({jet_eta[i],pt_corr,rho});
            double sf = jer[1]->evaluate({jet_eta[i],pt_corr,"nom"});

            // check gen jet
            double genPtForSmear = -1.0;
            int genIdx = jet_genJetIdx[i];
            if ( (genIdx > -1) && (static_cast<UInt_t>(genIdx) < genJet_pt.size()) ) {
                float genpt = genJet_pt[genIdx];
                float geneta = genJet_eta[genIdx];
                float genphi = genJet_phi[genIdx];

                double dR = ROOT::VecOps::DeltaR(jet_eta[i], geneta, jet_phi[i], genphi);
                if ( (dR<0.2) && (std::abs(pt_corr-genpt) < 3.0 * reso * pt_corr) ) {
                    genPtForSmear = genpt;
                }
            }
            std::vector<correction::Variable::Type> vals;
            vals.reserve(7);
            vals.emplace_back(static_cast<double>(pt_corr));   // JetPt
            vals.emplace_back(static_cast<double>(jet_eta[i]));  // JetEta
            vals.emplace_back(static_cast<double>(genPtForSmear));  // GenPt or -1
            vals.emplace_back(static_cast<double>(rho));  // Rho
            vals.emplace_back(static_cast<int>(event));         // EventID
            vals.emplace_back(static_cast<double>(reso));           // JER
            vals.emplace_back(static_cast<double>(sf));             // JERSF

            const double smear = jer[2]->evaluate(vals);
            const double cjer = (std::isfinite(smear) && smear > 0.0) ? smear : 1.0;

            pt_corr = pt_corr * cjer;
        }
        const bool passSel = (pt_corr > 15.0 && std::abs(jet_eta[i]) < 5.2 && (jet_chEmEF[i]+jet_neEmEF[i]) < 0.9) ;
        //std::cout << "jet pass " << passSel << std::endl;
        if (!passSel) continue;

        const double dpt = (pt_corr - pt_corrL1);
        met_px -= dpt * std::cos(jet_phi[i]);
        met_py -= dpt * std::sin(jet_phi[i]);
        //std::cout << "new met " << met_px << " " << met_py << std::endl;

    }
    //std::cout << "met pt " << std::hypot(met_px,met_py) << " phi " << std::atan2(met_py,met_px) << std::endl;
    return std::pair<float,float>({std::hypot(met_px,met_py),std::atan2(met_py,met_px)});
}

std::pair<float,float> JERC_MET_data(const std::map<std::string,correction::Correction::Ref>& jerc, const std::string& year, const int& run, const int& event, const float& MET_pt, const float& MET_phi, const ROOT::RVecF& jet_area, const ROOT::RVecF& jet_eta, const ROOT::RVecF& jet_phi, const ROOT::RVecF& jet_pt, const ROOT::RVecF& jet_rawFactor, const ROOT::RVecF& jet_muonSubtrFactor, const ROOT::RVecF& jet_chEmEF, const ROOT::RVecF& jet_neEmEF, const float& rho) {
    ROOT::RVecI empty_I({});
    ROOT::RVecF empty_F({});
    return JERC_MET(jerc, true, year, run, event, MET_pt, MET_phi, jet_area, jet_eta, jet_phi, jet_pt, jet_rawFactor, jet_muonSubtrFactor, jet_chEmEF, jet_neEmEF, rho, empty_I, empty_F, empty_F, empty_F);
}

std::pair<float,float> JERC_MET_MC(const std::map<std::string,correction::Correction::Ref>& jerc, const std::string& year, const int& run, const int& event, const float& MET_pt, const float& MET_phi, const ROOT::RVecF& jet_area, const ROOT::RVecF& jet_eta, const ROOT::RVecF& jet_phi, const ROOT::RVecF& jet_pt, const ROOT::RVecF& jet_rawFactor, const ROOT::RVecF& jet_muonSubtrFactor, const ROOT::RVecF& jet_chEmEF, const ROOT::RVecF& jet_neEmEF, const float& rho, const ROOT::RVecI& jet_genJetIdx, const ROOT::RVecF& genJet_pt, const ROOT::RVecF& genJet_eta, const ROOT::RVecF& genJet_phi) {
    return JERC_MET(jerc, false, year, run, event, MET_pt, MET_phi, jet_area, jet_eta, jet_phi, jet_pt, jet_rawFactor, jet_muonSubtrFactor, jet_chEmEF, jet_neEmEF, rho, jet_genJetIdx, genJet_pt, genJet_eta, genJet_phi);
}
