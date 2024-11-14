#include "ROOT/RDataFrame.hxx"
#include "ROOT/RVec.hxx"
#include "TCanvas.h"
#include "TH1D.h"
#include "TLatex.h"
#include "Math/Vector4D.h"
#include "TStyle.h"
#include <algorithm> 
#include "correction.h"

float dPhi(float phi1, float phi2) {
  float x = phi1-phi2;
  float o2pi = 1. / (2. * M_PI);
  if (std::abs(x) <= float(M_PI))
    return x;
  float n = std::round(x * o2pi);
  return x - n * float(2. * M_PI);
}

float dR(float phi1, float phi2, float eta1, float eta2) {
    float dp = std::abs(dPhi(phi1, phi2));
    return sqrt(dp*dp+(eta1-eta2)*(eta1-eta2));
}

template<typename T>
void printVec(T v) {

    for (size_t i=0; i<v.size(); ++i) {
        std::cout << v[i] << ", ";
    }
    std::cout << std::endl;
    return;
}

//This function removes duplicated elements in a vector
template<typename T>
T removeDuplicate(T v) {
    //printVec(v);
    v = ROOT::VecOps::Sort(v);
    v.erase( std::unique( v.begin(), v.end() ), v.end() );
    //printVec(v);
    
    return v;
}

float EGamma_weight(correction::Correction::Ref sf, ROOT::RVecF pt, ROOT::RVecF eta, std::string mode, std::string wp, std::string year, std::string kind) {
  float weight = 1;
  for (size_t i=0; i<pt.size(); ++i) {
    float newpt = pt[i];
    if (kind=="photon" && newpt<20)
      newpt = 20.0;
    float isf = sf->evaluate({year, mode, wp, std::abs(eta[i]), newpt});
    weight *= isf;
  }
  return weight;
}

float Muon_weight(correction::Correction::Ref sf, ROOT::RVecF pt, ROOT::RVecF eta, std::string mode) {
  float weight = 1;
  for (size_t i=0; i<pt.size(); ++i) {
    float newpt = pt[i];
    if (newpt<15)
      newpt = 15.0;
    float isf = sf->evaluate({std::abs(eta[i]), newpt, mode});
    weight *= isf;
  }
  return weight;
}

int Leading_Vtx_Idx(ROOT::RVecI Vertex_nGoodTracks, ROOT::RVecF Vertex_LxySig) {
  float max_lxysig = -1;
  int leading_idx = -1;
  int max_nGoodTracks = ROOT::VecOps::Max(Vertex_nGoodTracks);
  //std::cout << "Max ngoodtrack " << max_nGoodTracks << std::endl;
  for (int i=0; i<Vertex_nGoodTracks.size(); ++i) {
    if (max_nGoodTracks>=2){
      //std::cout << "max 2 loop " << i << " ngoodtrack " << Vertex_nGoodTracks[i] << " lxysig " << Vertex_LxySig[i] << std::endl;
      if ((Vertex_nGoodTracks[i]>=2) && (Vertex_LxySig[i]>max_lxysig) ){
        max_lxysig = Vertex_LxySig[i];
        leading_idx = i;
        //std::cout << "Best " << max_lxysig << " " << leading_idx << std::endl;
      }
    }
    else {
      //std::cout << "max" << max_nGoodTracks << "loop " << i << " ngoodtrack " << Vertex_nGoodTracks[i] << " lxysig " << Vertex_LxySig[i] << std::endl;
      if ((Vertex_nGoodTracks[i]==max_nGoodTracks) && (Vertex_LxySig[i]>max_lxysig) ){
        max_lxysig = Vertex_LxySig[i];
        leading_idx = i;
        //std::cout << "Best " << max_lxysig << " " << leading_idx << std::endl;
      }
    }
  }
  return leading_idx;
}

std::vector<ROOT::RVecF> SDVGenPart_fourvec(ROOT::RVecF SDVGenPart_pt, ROOT::RVecF SDVGenPart_eta, ROOT::RVecF SDVGenPart_phi, ROOT::RVecF SDVGenPart_mass) {
  size_t nGenPart = SDVGenPart_mass.size();
  ROOT::RVecF SDVGenPart_E(nGenPart, -1);
  ROOT::RVecF SDVGenPart_px(nGenPart, -1);
  ROOT::RVecF SDVGenPart_py(nGenPart, -1);
  ROOT::RVecF SDVGenPart_pz(nGenPart, -1);


  for(size_t i=0; i<nGenPart; ++i){
    const ROOT::Math::PtEtaPhiMVector p4(SDVGenPart_pt[i], SDVGenPart_eta[i], SDVGenPart_phi[i], SDVGenPart_mass[i]);
    SDVGenPart_E[i]  = p4.E();
    SDVGenPart_px[i] = p4.px();
    SDVGenPart_py[i] = p4.py();
    SDVGenPart_pz[i] = p4.pz();
  }

  std::vector<ROOT::RVecF> SDVGenPart_p = {SDVGenPart_E, SDVGenPart_px, SDVGenPart_py, SDVGenPart_pz};
  return SDVGenPart_p;
}

ROOT::RVecF SDVGenPart_Dmeson_inv_mass(ROOT::RVecI SDVGenPart_pdgId, ROOT::RVecI SDVGenPart_status, ROOT::RVecI SDVGenPart_genPartIdxMother, 
                                       ROOT::RVecI SDVGenPart_charge, ROOT::RVecF SDVGenPart_pt, ROOT::RVecF SDVGenPart_eta, ROOT::RVecF SDVGenPart_phi, ROOT::RVecF SDVGenPart_mass){
  size_t nGenPart = SDVGenPart_mass.size();
  ROOT::RVecB is_mother_Dmeson      = (abs(ROOT::VecOps::Take(SDVGenPart_pdgId, SDVGenPart_genPartIdxMother))==411);
  ROOT::RVecI Dmeson_dau_pdgId      = SDVGenPart_pdgId[is_mother_Dmeson];
  ROOT::RVecI Dmeson_dau_IdxMother  = SDVGenPart_genPartIdxMother[is_mother_Dmeson];
  ROOT::RVecI Dmeson_dau_status     = SDVGenPart_status[is_mother_Dmeson];
  ROOT::RVecF Dmeson_dau_pt         = SDVGenPart_pt[is_mother_Dmeson];
  ROOT::RVecF Dmeson_dau_eta        = SDVGenPart_eta[is_mother_Dmeson];
  ROOT::RVecF Dmeson_dau_phi        = SDVGenPart_phi[is_mother_Dmeson];
  ROOT::RVecF Dmeson_dau_mass       = SDVGenPart_mass[is_mother_Dmeson];
  ROOT::RVecF Dmeson_dau_charge     = SDVGenPart_charge[is_mother_Dmeson];

  std::set<int> s(Dmeson_dau_IdxMother.begin(), Dmeson_dau_IdxMother.end());
  ROOT::RVecF Dmeson_Idx;
  Dmeson_Idx.assign(s.begin(), s.end());
  ROOT::RVecF Dmeson_vtx_mass(Dmeson_Idx.size(), -1);

  size_t nDmeson = Dmeson_Idx.size();
  size_t nDmeson_dau = Dmeson_dau_status.size();
  
  ROOT::RVecF Dmeson_vtx_obs_mass(nDmeson, -1);
  for(size_t i=0; i<nDmeson; i++){
    ROOT::Math::PtEtaPhiMVector Dmeson_vtx_p4(0,0,0,0);
    int nDau;
    for(size_t j=0; j<nDmeson_dau; j++){
      bool isMyMother   = (Dmeson_Idx[i]==Dmeson_dau_IdxMother[j]);
      bool isCharged    = (Dmeson_dau_charge[j] != 0);
      bool passesPtCut  = (Dmeson_dau_pt[j] > 0.5);
      if( isMyMother && isCharged && passesPtCut ){
        // ROOT::Math::PtEtaPhiMVector Dmeson_dau_p4(Dmeson_dau_pt[j], Dmeson_dau_eta[j], Dmeson_dau_phi[j], Dmeson_dau_mass[j]);
        ROOT::Math::PtEtaPhiMVector Dmeson_dau_p4(Dmeson_dau_pt[j], Dmeson_dau_eta[j], Dmeson_dau_phi[j], 0.13957);
        Dmeson_vtx_p4 += Dmeson_dau_p4;
        nDau++;
      }
    }
    if(nDau!=0){
      Dmeson_vtx_obs_mass[i] = Dmeson_vtx_p4.M();
    }
    else{
      Dmeson_vtx_obs_mass[i] = -1;
    }
    
  }
  return Dmeson_vtx_obs_mass;
}

// This function calculates the closest jet for each vertex by looking for the smallest dR
// Then it calculated the dR, dphi, and deta between the vertex and the closest jet
// It returns an array of 3 arrays, each array has the length of the number of vertices
// The first array is the dR between vertex displacement vector and the closest jet
// The second array is the dphi, and the third array is the deta
std::vector<ROOT::VecOps::RVec<float>> Vertex_mindRdetadphi(ROOT::RVecF Vertex_phi, ROOT::RVecF Vertex_eta, ROOT::RVecF Jet_phi, ROOT::RVecF Jet_eta) {
  size_t nVertex = Vertex_phi.size();
  ROOT::RVecF minJetdR(nVertex,999);
  ROOT::RVecF minJetdphi(nVertex,999);
  ROOT::RVecF minJetdeta(nVertex,999);
  if (Jet_phi.size()>0){
      for (size_t i=0; i<nVertex; ++i) {
        ROOT::RVecF jet_dphi = ROOT::VecOps::abs(ROOT::VecOps::DeltaPhi(Jet_phi,Vertex_phi[i]));
        ROOT::RVecF jet_deta = ROOT::VecOps::abs(Jet_eta-Vertex_eta[i]);
        ROOT::RVecF jet_dR = ROOT::VecOps::hypot(jet_dphi,jet_deta);
    
        size_t jetidx = ROOT::VecOps::ArgMin(jet_dR);
        minJetdR[i]   = jet_dR[jetidx];
        minJetdphi[i] = jet_dphi[jetidx];
        minJetdeta[i] = jet_deta[jetidx];
      }
  }
  std::vector<ROOT::VecOps::RVec<float>> mindRdetadphi = {minJetdR,minJetdphi,minJetdeta};
  return mindRdetadphi;
}

ROOT::RVecI vtx_jetidx_at_mindR(ROOT::RVecF Vertex_phi, ROOT::RVecF Vertex_eta, ROOT::RVecF Jet_phi, ROOT::RVecF Jet_eta) {
  bool debug = false;

  size_t nVertex = Vertex_phi.size();
  ROOT::RVecF minJetdR(nVertex,999);
  ROOT::RVecF minJetdphi(nVertex,999);
  ROOT::RVecF minJetdeta(nVertex,999);
  ROOT::RVecI jetidx_at_minJetdR(nVertex,999);
  if(debug){
    std::cout << "--------------------------------------------------------" << std::endl;
    std::cout << "Jet_phi.size(): " << Jet_phi.size() << std::endl;
  }
  if (Jet_phi.size()>0){
      for (size_t i=0; i<nVertex; ++i) {
        ROOT::RVecF jet_dphi = ROOT::VecOps::abs(ROOT::VecOps::DeltaPhi(Jet_phi,Vertex_phi[i]));
        ROOT::RVecF jet_deta = ROOT::VecOps::abs(Jet_eta-Vertex_eta[i]);
        ROOT::RVecF jet_dR = ROOT::VecOps::hypot(jet_dphi,jet_deta);
    
        size_t jetidx = ROOT::VecOps::ArgMin(jet_dR);
        if(debug){
          std::cout << "vtx: " << i<< std::endl;
          std::cout << "jetidx: " << jetidx<< std::endl;
        }
        jetidx_at_minJetdR[i] = jetidx;
        minJetdR[i]   = jet_dR[jetidx];
        minJetdphi[i] = jet_dphi[jetidx];
        minJetdeta[i] = jet_deta[jetidx];
      }
  }
  if(debug){
    std::cout << "--------------------------------------------------------" << std::endl;
  }
  return jetidx_at_minJetdR;
}

ROOT::RVecF tmp_func(ROOT::RVecF myvec, ROOT::RVecI myidx){
    ROOT::RVecF return_vec = ROOT::VecOps::Take(myvec, myidx);
    for(size_t i=0; i<myidx.size(); ++i){
      if(return_vec[i] > 0 && return_vec[i] < 0.98){
        std::cout << "myidx[" << i << "]: " << myidx[i] << std::endl;
        std::cout << "return_vec[" << i << "]: " << return_vec[i] << std::endl;
      }
    }
    // if(myidx.size() == 0){
    //   std::cout << "return_vec: " << return_vec << std::endl;
    // }
    return return_vec;
}

// This function returns the modified PFIsolation
ROOT::VecOps::RVec<float> Track_modifiedIsolation_new(ROOT::RVecF Track_AbsIso_chg, ROOT::RVecF Track_AbsIso_neu, ROOT::RVecF Track_AbsIso_pho, ROOT::RVecF Track_AbsIso_pu, ROOT::RVecI SDVIdxLUT_TrackIdx, ROOT::RVecF Track_pt, ROOT::RVecF Track_eta, ROOT::RVecF Track_phi, ROOT::RVecF Track_dz, ROOT::RVecF Track_fromPV, ROOT::RVecF Track_AbsIso_all) {
  ROOT::RVecF Track_AbsIso_chg_new = Track_AbsIso_chg;
  ROOT::RVecF Track_AbsIso_pu_new = Track_AbsIso_pu;
  ROOT::RVecI TrackIdx_InSV = removeDuplicate(SDVIdxLUT_TrackIdx);
  for (size_t i=0;i<TrackIdx_InSV.size();++i){
    int idxi = TrackIdx_InSV[i];
    //std::cout << "Track " << idxi << " chg iso " << Track_AbsIso_chg_new[idxi] << " pu iso " << Track_AbsIso_pu_new[idxi] << " eta " << Track_eta[idxi] << " phi " << Track_phi[idxi] << std::endl;
    for (size_t j=0; j<TrackIdx_InSV.size();++j){
      int idxj = TrackIdx_InSV[j];
      if (idxi==idxj) continue;
      double dr = ROOT::VecOps::DeltaR(Track_eta[idxi],Track_eta[idxj],Track_phi[idxi],Track_phi[idxj]);

      if (dr>0.3) continue;
      //std::cout << "  Track pt" << Track_pt[idxj]  << " eta " << Track_eta[idxj] << " phi " << Track_phi[idxj] << std::endl;
      //std::cout << "   dR " << dr << " dz " << abs(Track_dz[idxj]) << " fromPV " << Track_fromPV[idxj] << std::endl;
      if ( (abs(Track_dz[idxj])<0.1) || (Track_fromPV[idxj]>1) ){
        Track_AbsIso_chg_new[idxi] -= Track_pt[idxj];
      }
      else{
        Track_AbsIso_pu_new[idxi] -= Track_pt[idxj];
      }
    }
  }
  ROOT::RVecF Track_AbsIso_all_new(Track_AbsIso_chg.size(),-1);
  for (size_t i=0; i<Track_AbsIso_all_new.size(); ++i){
    Track_AbsIso_all_new[i] = Track_AbsIso_chg_new[i] + std::max<double>(Track_AbsIso_neu[i]+Track_AbsIso_pho[i]-Track_AbsIso_pu_new[i]/2,0.0);
  }
  //std::cout << "After :" << std::endl;
  //for (size_t i=0; i<TrackIdx_InSV.size();++i){
  //  int tkidx = TrackIdx_InSV[i];
  //  std::cout << "For tk " << tkidx << " before all " << Track_AbsIso_all[tkidx] << " chg " << Track_AbsIso_chg[tkidx] << " pu " << Track_AbsIso_pu[tkidx] << " neu " << Track_AbsIso_neu[tkidx] << " pho " << Track_AbsIso_pho[tkidx] << std::endl;
  //  std::cout << "       after all " << Track_AbsIso_all_new[tkidx] << " chg " << Track_AbsIso_chg_new[tkidx] << " pu " << Track_AbsIso_pu_new[tkidx] << std::endl;
  //}
  return Track_AbsIso_all_new;
}

// This function returns the modified PFIsolation
ROOT::VecOps::RVec<float> Track_modifiedIsolation_chg_new(ROOT::RVecF Track_AbsIso_chg, ROOT::RVecI SDVIdxLUT_TrackIdx, ROOT::RVecF Track_pt, ROOT::RVecF Track_eta, ROOT::RVecF Track_phi, ROOT::RVecF Track_dz, ROOT::RVecF Track_fromPV) {
  ROOT::RVecF Track_AbsIso_chg_new = Track_AbsIso_chg;
  ROOT::RVecI TrackIdx_InSV = removeDuplicate(SDVIdxLUT_TrackIdx);
  for (size_t i=0;i<TrackIdx_InSV.size();++i){
    int idxi = TrackIdx_InSV[i];
    for (size_t j=0; j<TrackIdx_InSV.size();++j){
      int idxj = TrackIdx_InSV[j];
      if (idxi==idxj) continue;
      double dr = ROOT::VecOps::DeltaR(Track_eta[idxi],Track_eta[idxj],Track_phi[idxi],Track_phi[idxj]);

      if (dr>0.3) continue;
      if ( (abs(Track_dz[idxj])<0.1) || (Track_fromPV[idxj]>1) ){
        Track_AbsIso_chg_new[idxi] -= Track_pt[idxj];
      }
    }
  }
  return Track_AbsIso_chg_new;
}

// This function returns the modified PFIsolation
ROOT::VecOps::RVec<float> Track_ntk_dRcone_new(ROOT::RVecI SDVIdxLUT_TrackIdx, ROOT::RVecF Track_pt, ROOT::RVecF Track_eta, ROOT::RVecF Track_phi, ROOT::RVecF Track_dz, ROOT::RVecF Track_fromPV) {
  ROOT::RVecI ntkdRcone(Track_pt.size(),-1);
  ROOT::RVecI TrackIdx_InSV = removeDuplicate(SDVIdxLUT_TrackIdx);
  for (size_t i=0;i<TrackIdx_InSV.size();++i){
    int idxi = TrackIdx_InSV[i];
    if (ntkdRcone[idxi]==-1)
      ntkdRcone[idxi]=0;
    for (size_t j=0; j<TrackIdx_InSV.size();++j){
      int idxj = TrackIdx_InSV[j];
      if (idxi==idxj) continue;
      double dr = ROOT::VecOps::DeltaR(Track_eta[idxi],Track_eta[idxj],Track_phi[idxi],Track_phi[idxj]);

      if (dr>0.3) continue;
      if ((abs(Track_dz[idxj])<0.1) || (Track_fromPV[idxj]>1) ){
        ntkdRcone[idxi] += 1;
      }
    }
  }
  return ntkdRcone;
}

// This function returns the modified PFIsolation
ROOT::VecOps::RVec<float> Track_sumpt_dRcone_new(ROOT::RVecI SDVIdxLUT_TrackIdx, ROOT::RVecF Track_pt, ROOT::RVecF Track_eta, ROOT::RVecF Track_phi, ROOT::RVecF Track_dz, ROOT::RVecF Track_fromPV) {
  ROOT::RVecI sumptdRcone(Track_pt.size(),-1);
  ROOT::RVecI TrackIdx_InSV = removeDuplicate(SDVIdxLUT_TrackIdx);
  for (size_t i=0;i<TrackIdx_InSV.size();++i){
    int idxi = TrackIdx_InSV[i];
    if (sumptdRcone[idxi]==-1)
      sumptdRcone[idxi]=0;
    for (size_t j=0; j<TrackIdx_InSV.size();++j){
      int idxj = TrackIdx_InSV[j];
      if (idxi==idxj) continue;
      double dr = ROOT::VecOps::DeltaR(Track_eta[idxi],Track_eta[idxj],Track_phi[idxi],Track_phi[idxj]);

      if (dr>0.3) continue;
      if ((abs(Track_dz[idxj])<0.1) || (Track_fromPV[idxj]>1) ){
        sumptdRcone[idxi] += Track_pt[idxj];
      }
      //else if (Track_AbsIso_all[idxi]!=Track_AbsIso_chg[idxi]){
      //  Track_AbsIso_all[idxi] += Track_pt[idxj]/2.0;
      //}
    }
  }
  return sumptdRcone;
}

// This function returns the modified PFIsolation
ROOT::VecOps::RVec<float> Track_modifiedIsolation(ROOT::RVecF Track_AbsIso, ROOT::RVecI SDVIdxLUT_TrackIdx, ROOT::RVecF Track_pt, ROOT::RVecF Track_eta, ROOT::RVecF Track_phi, ROOT::RVecF Track_dz, float dz_cut) {
  ROOT::RVecF Track_AbsIso_new = Track_AbsIso;
  ROOT::RVecI TrackIdx_InSV = removeDuplicate(SDVIdxLUT_TrackIdx);
  for (size_t i=0;i<TrackIdx_InSV.size();++i){
    int idxi = TrackIdx_InSV[i];
    for (size_t j=0; j<TrackIdx_InSV.size();++j){
      int idxj = TrackIdx_InSV[j];
      if (idxi==idxj) continue;
      double dr = ROOT::VecOps::DeltaR(Track_eta[idxi],Track_eta[idxj],Track_phi[idxi],Track_phi[idxj]);

      if (dr>0.3) continue;
      if (abs(Track_dz[idxj])<dz_cut){
        Track_AbsIso_new[idxi] -= Track_pt[idxj];
      }
      //else if (Track_AbsIso_all[idxi]!=Track_AbsIso_chg[idxi]){
      //  Track_AbsIso_all[idxi] += Track_pt[idxj]/2.0;
      //}
    }
  }
  for (size_t i=0; i<Track_AbsIso_new.size(); ++i){
    if(Track_AbsIso_new[i]<0)
      Track_AbsIso_new[i] = 0;
  }
  return Track_AbsIso_new;
}

// This function returns the modified PFIsolation
ROOT::VecOps::RVec<float> Track_ntk_dRcone(ROOT::RVecI SDVIdxLUT_TrackIdx, ROOT::RVecF Track_pt, ROOT::RVecF Track_eta, ROOT::RVecF Track_phi, ROOT::RVecF Track_dz, float dz_cut) {
  ROOT::RVecI ntkdRcone(Track_pt.size(),-1);
  ROOT::RVecI TrackIdx_InSV = removeDuplicate(SDVIdxLUT_TrackIdx);
  for (size_t i=0;i<TrackIdx_InSV.size();++i){
    int idxi = TrackIdx_InSV[i];
    if (ntkdRcone[idxi]==-1)
      ntkdRcone[idxi]=0;
    for (size_t j=0; j<TrackIdx_InSV.size();++j){
      int idxj = TrackIdx_InSV[j];
      if (idxi==idxj) continue;
      double dr = ROOT::VecOps::DeltaR(Track_eta[idxi],Track_eta[idxj],Track_phi[idxi],Track_phi[idxj]);

      if (dr>0.3) continue;
      if (abs(Track_dz[idxj])<dz_cut){
        ntkdRcone[idxi] += 1;
      }
      //else if (Track_AbsIso_all[idxi]!=Track_AbsIso_chg[idxi]){
      //  Track_AbsIso_all[idxi] += Track_pt[idxj]/2.0;
      //}
    }
  }
  return ntkdRcone;
}

// This function returns the modified PFIsolation
ROOT::VecOps::RVec<float> Track_sumpt_dRcone(ROOT::RVecI SDVIdxLUT_TrackIdx, ROOT::RVecF Track_pt, ROOT::RVecF Track_eta, ROOT::RVecF Track_phi, ROOT::RVecF Track_dz, float dz_cut) {
  ROOT::RVecI sumptdRcone(Track_pt.size(),-1);
  ROOT::RVecI TrackIdx_InSV = removeDuplicate(SDVIdxLUT_TrackIdx);
  for (size_t i=0;i<TrackIdx_InSV.size();++i){
    int idxi = TrackIdx_InSV[i];
    if (sumptdRcone[idxi]==-1)
      sumptdRcone[idxi]=0;
    for (size_t j=0; j<TrackIdx_InSV.size();++j){
      int idxj = TrackIdx_InSV[j];
      if (idxi==idxj) continue;
      double dr = ROOT::VecOps::DeltaR(Track_eta[idxi],Track_eta[idxj],Track_phi[idxi],Track_phi[idxj]);

      if (dr>0.3) continue;
      if (abs(Track_dz[idxj])<dz_cut){
        sumptdRcone[idxi] += Track_pt[idxj];
      }
      //else if (Track_AbsIso_all[idxi]!=Track_AbsIso_chg[idxi]){
      //  Track_AbsIso_all[idxi] += Track_pt[idxj]/2.0;
      //}
    }
  }
  return sumptdRcone;
}

// This function returns an array (with length of number of tracks) 
// Each element represent the minimum dphi between a given track and all selected jets
ROOT::VecOps::RVec<float> Track_minJetdphi(ROOT::RVecF Track_phi, ROOT::RVecF Jet_phi, int nTracks) {
  ROOT::RVecF minJetdphi(nTracks,999);
  for (size_t i=0; i<nTracks; ++i) {
    ROOT::RVecF jet_dphi = ROOT::VecOps::abs(ROOT::VecOps::DeltaPhi(Jet_phi,Track_phi[i]));
    minJetdphi[i] = ROOT::VecOps::Min(jet_dphi);
  }
  //printVec(minJetdphi);
  return minJetdphi;
}
// This function returns an array (with length of number of tracks) 
// Each element represent the minimum deta between a given track and all selected jets
ROOT::VecOps::RVec<float> Track_minJetdeta(ROOT::RVecF Track_eta, ROOT::RVecF Jet_eta, int nTracks) {
  //std::cout << "tracks : " << std::endl;
  //printVec(Track_eta);
  //std::cout << "jets: " << std::endl;
  //printVec(Jet_eta);
  ROOT::RVecF minJetdeta(nTracks,999);
  for (size_t i=0; i<nTracks; ++i) {
    ROOT::RVecF jet_deta = ROOT::VecOps::abs(Jet_eta-Track_eta[i]);
    //std::cout << "  For track " << i << std::endl;
    //printVec(jet_deta);
    minJetdeta[i] = ROOT::VecOps::Min(jet_deta);
  }
  //printVec(minJetdeta);
  return minJetdeta;
}

// This function returns an array (with length of number of tracks) 
// Each element represent the minimum dphi between a given track and all selected jets
ROOT::VecOps::RVec<float> Track_minJetdR(ROOT::RVecF Track_phi, ROOT::RVecF Track_eta, ROOT::RVecF Jet_phi, ROOT::RVecF Jet_eta, int nTracks) {
  //std::cout << "tracks : " << std::endl;
  //std::cout << "phi ";
  //printVec(Track_phi);
  //std::cout << "eta ";
  //printVec(Track_eta);
  //std::cout << "jets: " << std::endl;
  //std::cout << "phi ";
  //printVec(Jet_phi);
  //std::cout << "eta ";
  //printVec(Jet_eta);
  ROOT::RVecF minJetdR(nTracks,999);
  for (size_t i=0; i<nTracks; ++i) {
    ROOT::RVecF jet_dphi = ROOT::VecOps::abs(ROOT::VecOps::DeltaPhi(Jet_phi,Track_phi[i]));
    ROOT::RVecF jet_deta = ROOT::VecOps::abs(Jet_eta-Track_eta[i]);
    ROOT::RVecF jet_dR = ROOT::VecOps::hypot(jet_dphi,jet_deta);

    //std::cout << "  For track " << i << std::endl;
    //std::cout << "  dphi: ";
    //printVec(jet_dphi);
    //std::cout << "  deta: ";
    //printVec(jet_deta);
    //std::cout << "  dR: ";
    //printVec(jet_dR);
    minJetdR[i] = ROOT::VecOps::Min(jet_dR);
  }
  //printVec(minJetdphi);
  return minJetdR;
}

// This function returns an array (with length of number of tracks) 
// Each element represent the minimum dphi between a given track and all selected jets
ROOT::VecOps::RVec<float> Track_minJetdR_pt(ROOT::RVecF Track_phi, ROOT::RVecF Track_eta, ROOT::RVecF Jet_phi, ROOT::RVecF Jet_eta, ROOT::RVecF Jet_pt, int nTracks) {
  //std::cout << "tracks : " << std::endl;
  //std::cout << "phi ";
  //printVec(Track_phi);
  //std::cout << "eta ";
  //printVec(Track_eta);
  //std::cout << "jets: " << std::endl;
  //std::cout << "phi ";
  //printVec(Jet_phi);
  //std::cout << "eta ";
  //printVec(Jet_eta);
  ROOT::RVecF min_pt(nTracks,999);
  for (size_t i=0; i<nTracks; ++i) {
    ROOT::RVecF jet_dphi = ROOT::VecOps::abs(ROOT::VecOps::DeltaPhi(Jet_phi,Track_phi[i]));
    ROOT::RVecF jet_deta = ROOT::VecOps::abs(Jet_eta-Track_eta[i]);
    ROOT::RVecF jet_dR = ROOT::VecOps::hypot(jet_dphi,jet_deta);
    size_t min_idx = ROOT::VecOps::ArgMin(jet_dR);
    float jet_dR_min = jet_dR[min_idx];
    float jet_pt_min = Jet_pt[min_idx];

    min_pt[i] = jet_pt_min;
  }
  //printVec(min_pt);
  return min_pt;
}
// This function returns a list with the length of nTracks, each element labels whether the track is included in a SV or not
ROOT::VecOps::RVec<int> Track_isInSV(ROOT::RVecI SDVIdxLUT_TrackIdx, int nTracks){
  ROOT::RVecI isInSV(nTracks,0);
  for (auto& idx : SDVIdxLUT_TrackIdx){
    isInSV[idx] = 1;
  }
  return isInSV;
}

// This function returns a list with the length of nTracks, each element shows the weight of the track in the SV fit
ROOT::VecOps::RVec<float> Track_WeightInSV(ROOT::RVecI SDVIdxLUT_TrackIdx, ROOT::RVecF SDVIdxLUT_TrackWeight, int nTracks){
  ROOT::RVecF tkweight(nTracks,-1);
  for (int i=0; i<SDVIdxLUT_TrackIdx.size(); ++i){
    tkweight[SDVIdxLUT_TrackIdx[i]] = SDVIdxLUT_TrackWeight[i];
  }
  return tkweight;
}

//This function helps to get the list of track indices that are included in the SDV (using LUT)
ROOT::VecOps::RVec<int> TracksinSDV(ROOT::RVecI SDVIdxLUT_SecVtxIdx, ROOT::RVecI SDVIdxLUT_TrackIdx, int iSDV)
{
    return SDVIdxLUT_TrackIdx[SDVIdxLUT_SecVtxIdx==iSDV];
}

ROOT::VecOps::RVec<int> GetTracksinSDVs(ROOT::RVecI SDVIdxLUT_SecVtxIdx, ROOT::RVecI SDVIdxLUT_TrackIdx, ROOT::RVecB SDVSecVtx_selected)
{
    ROOT::RVecI alltks;
    for (int i=0; i<SDVSecVtx_selected.size(); ++i){
        if (SDVSecVtx_selected[i]) {
            ROOT::RVecI tks = TracksinSDV(SDVIdxLUT_SecVtxIdx,SDVIdxLUT_TrackIdx,i);
            alltks = ROOT::VecOps::Concatenate(alltks,tks);
        }
    }
    return alltks;
}

//This function returns the number of good tracks in SDV
//It requires the input of SDVTrack_isGoodTrack, which is an array of 0 or 1 that indicates whether a track is good or not
ROOT::VecOps::RVec<int> SDVSecVtx_nGoodTrack(ROOT::RVecI SDVIdxLUT_SecVtxIdx, ROOT::RVecI SDVIdxLUT_TrackIdx, ROOT::RVecI SDVTrack_isGoodTrack, int nSDV)
{
    ROOT::VecOps::RVec<int> nGoodTracks;
    for (int i=0; i<nSDV; ++i){
        auto tkIdx = SDVIdxLUT_TrackIdx[SDVIdxLUT_SecVtxIdx==i];
        auto SDVTrack_isGoodTrack_filtered = ROOT::VecOps::Take(SDVTrack_isGoodTrack,tkIdx);
        auto SDVTrack_isGoodTrack_GoodTrack = SDVTrack_isGoodTrack_filtered[SDVTrack_isGoodTrack_filtered==1];
        nGoodTracks.push_back(SDVTrack_isGoodTrack_GoodTrack.size());
    }
    return nGoodTracks;
}

ROOT::VecOps::RVec<int> SDVSecVtx_nGoodRefitTrack(ROOT::RVecI SDVRefitTrack_svIdx, ROOT::RVecI SDVRefitTrack_isGoodTrack, int nSDV)
{
    ROOT::VecOps::RVec<int> nGoodTracks;
    for (int i=0; i<nSDV; ++i){
        auto ntk = ROOT::VecOps::Sum(SDVRefitTrack_isGoodTrack[SDVRefitTrack_svIdx==i]);
        nGoodTracks.push_back(ntk);
    }
    return nGoodTracks;
}

//This function returns a vector if the number of reco tracks in SDV that match with gen particles from the LLP decay (using LUT)
ROOT::VecOps::RVec<int> NMatchedTracksinSDV(ROOT::RVecI SDVTrack_LLPIdx, int nSDV, ROOT::RVecI SDVIdxLUT_SecVtxIdx, ROOT::RVecI SDVIdxLUT_TrackIdx)
{
    ROOT::VecOps::RVec<int> ntracks;
    for (int i=0; i<nSDV; ++i){
        //Get a list of track indices included in the SDV
        //std::cout << "1" << std::endl;
        auto tkIdx = SDVIdxLUT_TrackIdx[SDVIdxLUT_SecVtxIdx==i];
        //std::cout << "2" << std::endl;
        auto SDVTrack_LLPIdx_filtered = ROOT::VecOps::Take(SDVTrack_LLPIdx,tkIdx);
        //std::cout << "3" << std::endl;
        auto selectedTracks = SDVTrack_LLPIdx_filtered[SDVTrack_LLPIdx_filtered!=-1];
        //std::cout << "4" << std::endl;
        ntracks.push_back(selectedTracks.size());
    }
    return ntracks;
}

//This function returns a vector if the number of reco tracks in SDV that match with gen particles from the LLP decay (not using LUT)
ROOT::VecOps::RVec<int> NMatchedTracksinSDVnoLUT(ROOT::RVecI SDVTrack_LLPIdx, int nSDV, ROOT::RVecI SDVTrack_SecVtxIdx)
{
    ROOT::VecOps::RVec<int> ntracks;
    for (int i=0; i<nSDV; ++i){
        //Get a list of track indices included in the SDV
        //auto tkIdx = SDVIdxLUT_TrackIdx[SDVIdxLUT_SecVtxIdx==i];
        //auto SDVTrack_LLPIdx_filtered = ROOT::VecOps::Take(SDVTrack_LLPIdx,tkIdx);
        auto SDVTrack_LLPIdx_filtered = SDVTrack_LLPIdx[SDVTrack_SecVtxIdx==i];
        auto selectedTracks = SDVTrack_LLPIdx_filtered[SDVTrack_LLPIdx_filtered!=-1];
        ntracks.push_back(selectedTracks.size());
    }
    return ntracks;
}


//This function returns 
ROOT::VecOps::RVec<int> NMatchedTracksinLLP(ROOT::RVecI SDVTrack_LLPIdx, int nLLP)
{
    ROOT::VecOps::RVec<int> ntracks;
    for (int i=0; i<nLLP; ++i){
        auto selectedTracks = SDVTrack_LLPIdx[SDVTrack_LLPIdx==i];
        ntracks.push_back(selectedTracks.size());
    }
    return ntracks;
}

ROOT::VecOps::RVec<int> SDVIdxinLLP(ROOT::RVecI SDVTrack_LLPIdx, ROOT::RVecI SDVIdxLUT_SecVtxIdx, ROOT::RVecI SDVIdxLUT_TrackIdx, int nLLP, int nSDV, ROOT::RVecF SDVTrack_pt, ROOT::RVecF SDVTrack_eta, ROOT::RVecF SDVTrack_phi)
{
    ROOT::VecOps::RVec<int> SDVIdx(nLLP,-1);
    for (int illp=0; illp<nLLP; ++illp) {
        int Matched_SDV = -1;
        for (int isdv=0; isdv<nSDV; ++isdv){
            //Get a list of track indices included in the SDV
            auto tkIdx = SDVIdxLUT_TrackIdx[SDVIdxLUT_SecVtxIdx==isdv];
            auto SDVTrack_LLPIdx_filtered = ROOT::VecOps::Take(SDVTrack_LLPIdx,tkIdx);
            auto selectedTracks = SDVTrack_LLPIdx_filtered[SDVTrack_LLPIdx_filtered==illp];
            // DEBUG check
            //auto SDVTrack_pt_filtered = ROOT::VecOps::Take(SDVTrack_pt,tkIdx);
            //auto selected_pt = SDVTrack_pt_filtered[SDVTrack_LLPIdx_filtered==illp];
            //auto SDVTrack_eta_filtered = ROOT::VecOps::Take(SDVTrack_eta,tkIdx);
            //auto selected_eta = SDVTrack_eta_filtered[SDVTrack_LLPIdx_filtered==illp];
            //auto SDVTrack_phi_filtered = ROOT::VecOps::Take(SDVTrack_phi,tkIdx);
            //auto selected_phi = SDVTrack_phi_filtered[SDVTrack_LLPIdx_filtered==illp];
            //std::cout << "LLP " << illp << " vtx " << isdv << std::endl;
            //for (size_t i=0; i<selected_pt.size(); ++i){
            //    std::cout << "    pt " << selected_pt[i] << " eta " << selected_eta[i] << " phi " << selected_phi[i] << std::endl;
            //}
            if (selectedTracks.size()>0){
                Matched_SDV = isdv;
            }
        }
        SDVIdx[illp] = Matched_SDV;
    }
    return SDVIdx;
}


ROOT::VecOps::RVec<int> SDVIdxinLLP_dist(ROOT::RVecF LLP_decay_x, ROOT::RVecF LLP_decay_y, ROOT::RVecF LLP_decay_z, ROOT::RVecF SDVSecVtx_x, ROOT::RVecF SDVSecVtx_y, ROOT::RVecF SDVSecVtx_z, int nLLP, int nSDV)
{
    ROOT::VecOps::RVec<int> SDVIdx(nLLP,-1);
    for (int illp=0; illp<nLLP; ++illp) {
        int Matched_SDV = -1;
        for (int isdv=0; isdv<nSDV; ++isdv){
            double dist = sqrt((LLP_decay_x[illp]-SDVSecVtx_x[isdv])*(LLP_decay_x[illp]-SDVSecVtx_x[isdv]) + (LLP_decay_y[illp]-SDVSecVtx_y[isdv])*(LLP_decay_y[illp]-SDVSecVtx_y[isdv]) + (LLP_decay_z[illp]-SDVSecVtx_z[isdv])*(LLP_decay_z[illp]-SDVSecVtx_z[isdv]));
            if (dist<0.01)
                Matched_SDV = isdv;
        }
        SDVIdx[illp] = Matched_SDV;
    }
    return SDVIdx;
}

ROOT::VecOps::RVec<int> GenPartIdx_tkmatched(ROOT::RVecI SDVTrack_GenPartIdx, ROOT::RVecI SDVGenPart_isGentk, ROOT::RVecI SDVGenPart_LLPIdx)
{
    ROOT::RVecI SDVTrack_GenPartIdx_matched = SDVTrack_GenPartIdx[SDVTrack_GenPartIdx>=0];
    ROOT::RVecI SDVTrack_SDVGenPart_isGentk = ROOT::VecOps::Take(SDVGenPart_isGentk,SDVTrack_GenPartIdx_matched);
    ROOT::RVecI SDVTrack_SDVGenPart_LLPIdx = ROOT::VecOps::Take(SDVGenPart_LLPIdx,SDVTrack_GenPartIdx_matched);
    
    ROOT::RVecI idx = SDVTrack_GenPartIdx_matched[SDVTrack_SDVGenPart_isGentk==1 & SDVTrack_SDVGenPart_LLPIdx>=0];
    
    idx.erase( std::unique( idx.begin(), idx.end() ), idx.end() );
    
    return idx;
    
}

ROOT::RVecF LLP_GenTkSumpT(ROOT::RVecI SDVGenPart_isGentk, ROOT::RVecI SDVGenPart_LLPIdx, int nLLP, ROOT::RVecF SDVGenPart_pt, ROOT::RVecF SDVGenPart_eta, ROOT::RVecF SDVGenPart_phi, ROOT::RVecF SDVGenPart_mass)
{
    ROOT::VecOps::RVec<float> LLP_gtkpTsum(nLLP,0);
    for (size_t illp=0; illp<nLLP; ++illp){
        ROOT::Math::PtEtaPhiMVector p4_llp;
        ROOT::RVecF pts = SDVGenPart_pt[SDVGenPart_isGentk==1 & SDVGenPart_LLPIdx==illp];
        ROOT::RVecF etas = SDVGenPart_eta[SDVGenPart_isGentk==1 & SDVGenPart_LLPIdx==illp];
        ROOT::RVecF phis = SDVGenPart_phi[SDVGenPart_isGentk==1 & SDVGenPart_LLPIdx==illp];
        ROOT::RVecF masses = SDVGenPart_mass[SDVGenPart_isGentk==1 & SDVGenPart_LLPIdx==illp];
        for (size_t igtk=0; igtk<pts.size(); ++igtk){
            p4_llp += ROOT::Math::PtEtaPhiMVector(pts[igtk],etas[igtk],phis[igtk],masses[igtk]);
        }
        LLP_gtkpTsum[illp] = p4_llp.pt();
    }
    return LLP_gtkpTsum;
}


ROOT::RVecF LLP_GenTkMinpT(ROOT::RVecI SDVGenPart_isGentk, ROOT::RVecI SDVGenPart_LLPIdx, int nLLP, ROOT::RVecF SDVGenPart_pt, ROOT::RVecF SDVGenPart_eta, ROOT::RVecF SDVGenPart_phi, ROOT::RVecF SDVGenPart_mass)
{
    ROOT::VecOps::RVec<float> LLP_gtkpTmin(nLLP,0);
    for (size_t illp=0; illp<nLLP; ++illp){
        ROOT::RVecF pts = SDVGenPart_pt[SDVGenPart_isGentk==1 & SDVGenPart_LLPIdx==illp];
        LLP_gtkpTmin[illp] = ROOT::VecOps::Min(pts);
    }
    return LLP_gtkpTmin;
}


ROOT::RVecF LLP_GenTkMaxpT(ROOT::RVecI SDVGenPart_isGentk, ROOT::RVecI SDVGenPart_LLPIdx, int nLLP, ROOT::RVecF SDVGenPart_pt, ROOT::RVecF SDVGenPart_eta, ROOT::RVecF SDVGenPart_phi, ROOT::RVecF SDVGenPart_mass)
{
    ROOT::VecOps::RVec<float> LLP_gtkpTmax(nLLP,0);
    for (size_t illp=0; illp<nLLP; ++illp){
        ROOT::RVecF pts = SDVGenPart_pt[SDVGenPart_isGentk==1 & SDVGenPart_LLPIdx==illp];
        LLP_gtkpTmax[illp] = ROOT::VecOps::Max(pts);
    }
    return LLP_gtkpTmax;
}


ROOT::RVecF SDV_TkMaxdphi(ROOT::RVecI SDVIdxLUT_TrackIdx, ROOT::RVecI SDVIdxLUT_SecVtxIdx, int nSDV, ROOT::RVecF SDVTrack_phi)
{
    ROOT::RVecF SDVSecVtx_maxdphi(nSDV,-1);
    for (size_t iSDV=0; iSDV<nSDV; ++iSDV){
        auto tkIdx = SDVIdxLUT_TrackIdx[SDVIdxLUT_SecVtxIdx==iSDV];
        ROOT::RVecF dphis;
        for (size_t i=0; i<tkIdx.size(); ++i){
            for (size_t j=i+1; j<tkIdx.size();++j){
                dphis.push_back(abs(dPhi(SDVTrack_phi[tkIdx[i]],SDVTrack_phi[tkIdx[j]])));
            }
        }
        SDVSecVtx_maxdphi[iSDV] = ROOT::VecOps::Max(dphis);
    }
    return SDVSecVtx_maxdphi;
}

ROOT::RVecF SDV_TkMindphi(ROOT::RVecI SDVIdxLUT_TrackIdx, ROOT::RVecI SDVIdxLUT_SecVtxIdx, int nSDV, ROOT::RVecF SDVTrack_phi)
{
    ROOT::RVecF SDVSecVtx_mindphi(nSDV,-1);
    for (size_t iSDV=0; iSDV<nSDV; ++iSDV){
        auto tkIdx = SDVIdxLUT_TrackIdx[SDVIdxLUT_SecVtxIdx==iSDV];
        ROOT::RVecF dphis;
        for (size_t i=0; i<tkIdx.size(); ++i){
            for (size_t j=i+1; j<tkIdx.size();++j){
                dphis.push_back(abs(dPhi(SDVTrack_phi[tkIdx[i]],SDVTrack_phi[tkIdx[j]])));
            }
        }
        SDVSecVtx_mindphi[iSDV] = ROOT::VecOps::Min(dphis);
    }
    return SDVSecVtx_mindphi;
}

ROOT::RVecF SDV_TkMaxdeta(ROOT::RVecI SDVIdxLUT_TrackIdx, ROOT::RVecI SDVIdxLUT_SecVtxIdx, int nSDV, ROOT::RVecF SDVTrack_eta)
{
    ROOT::RVecF SDVSecVtx_maxdeta(nSDV,-1);
    for (size_t iSDV=0; iSDV<nSDV; ++iSDV){
        auto tkIdx = SDVIdxLUT_TrackIdx[SDVIdxLUT_SecVtxIdx==iSDV];
        ROOT::RVecF dphis;
        for (size_t i=0; i<tkIdx.size(); ++i){
            for (size_t j=i+1; j<tkIdx.size();++j){
                dphis.push_back(abs(SDVTrack_eta[tkIdx[i]]-SDVTrack_eta[tkIdx[j]]));
            }
        }
        SDVSecVtx_maxdeta[iSDV] = ROOT::VecOps::Max(dphis);
    }
    return SDVSecVtx_maxdeta;
}

ROOT::RVecF SDV_TkMindeta(ROOT::RVecI SDVIdxLUT_TrackIdx, ROOT::RVecI SDVIdxLUT_SecVtxIdx, int nSDV, ROOT::RVecF SDVTrack_eta)
{
    ROOT::RVecF SDVSecVtx_mindeta(nSDV,-1);
    for (size_t iSDV=0; iSDV<nSDV; ++iSDV){
        auto tkIdx = SDVIdxLUT_TrackIdx[SDVIdxLUT_SecVtxIdx==iSDV];
        ROOT::RVecF dphis;
        for (size_t i=0; i<tkIdx.size(); ++i){
            for (size_t j=i+1; j<tkIdx.size();++j){
                dphis.push_back(abs(SDVTrack_eta[tkIdx[i]]-SDVTrack_eta[tkIdx[j]]));
            }
        }
        SDVSecVtx_mindeta[iSDV] = ROOT::VecOps::Min(dphis);
    }
    return SDVSecVtx_mindeta;
}

ROOT::RVecF SDV_TkMaxdR(ROOT::RVecI SDVIdxLUT_TrackIdx, ROOT::RVecI SDVIdxLUT_SecVtxIdx, int nSDV, ROOT::RVecF SDVTrack_eta, ROOT::RVecF SDVTrack_phi)
{
    ROOT::RVecF SDVSecVtx_maxdR(nSDV,-1);
    for (size_t iSDV=0; iSDV<nSDV; ++iSDV){
        auto tkIdx = SDVIdxLUT_TrackIdx[SDVIdxLUT_SecVtxIdx==iSDV];
        ROOT::RVecF dphis;
        for (size_t i=0; i<tkIdx.size(); ++i){
            for (size_t j=i+1; j<tkIdx.size();++j){
                dphis.push_back(dR(SDVTrack_phi[tkIdx[i]],SDVTrack_phi[tkIdx[j]],SDVTrack_eta[tkIdx[i]],SDVTrack_eta[tkIdx[j]]));
            }
        }
        SDVSecVtx_maxdR[iSDV] = ROOT::VecOps::Max(dphis);
    }
    return SDVSecVtx_maxdR;
}

ROOT::RVecF SDV_TkMindR(ROOT::RVecI SDVIdxLUT_TrackIdx, ROOT::RVecI SDVIdxLUT_SecVtxIdx, int nSDV, ROOT::RVecF SDVTrack_eta, ROOT::RVecF SDVTrack_phi)
{
    ROOT::RVecF SDVSecVtx_mindR(nSDV,-1);
    for (size_t iSDV=0; iSDV<nSDV; ++iSDV){
        auto tkIdx = SDVIdxLUT_TrackIdx[SDVIdxLUT_SecVtxIdx==iSDV];
        ROOT::RVecF dphis;
        for (size_t i=0; i<tkIdx.size(); ++i){
            for (size_t j=i+1; j<tkIdx.size();++j){
                dphis.push_back(dR(SDVTrack_phi[tkIdx[i]],SDVTrack_phi[tkIdx[j]],SDVTrack_eta[tkIdx[i]],SDVTrack_eta[tkIdx[j]]));
            }
        }
        SDVSecVtx_mindR[iSDV] = ROOT::VecOps::Min(dphis);
    }
    return SDVSecVtx_mindR;
}

std::vector<ROOT::RVecF> SDV_TkMinMaxdxy(ROOT::RVecI SDVIdxLUT_TrackIdx, ROOT::RVecI SDVIdxLUT_SecVtxIdx, int nSDV, ROOT::RVecF SDVTrack_dxy)
{
    ROOT::RVecF SDVSecVtx_maxdxy(nSDV, -1);
    ROOT::RVecF SDVSecVtx_mindxy(nSDV, -1);
    for (size_t iSDV=0; iSDV<nSDV; ++iSDV){
        auto tkIdx = SDVIdxLUT_TrackIdx[SDVIdxLUT_SecVtxIdx==iSDV];
        ROOT::RVecF dxys;
        for (size_t i=0; i<tkIdx.size(); ++i){
                dxys.push_back(abs(SDVTrack_dxy[i]));
        }
        SDVSecVtx_mindxy[iSDV] = ROOT::VecOps::Min(dxys);
        SDVSecVtx_maxdxy[iSDV] = ROOT::VecOps::Max(dxys);
    }

    std::vector<ROOT::RVecF> minmaxdxy = {SDVSecVtx_mindxy, SDVSecVtx_maxdxy};
    return minmaxdxy;
}

/* ROOT::RVecF SDV_BJetMindR(int nSDV, int nJet, ROOT::RVecF SDVSecVtx_phi, ROOT::RVecF SDVSecVtx_eta, ROOT::RVecF Jet_phi, ROOT::RVecF Jet_eta)
{
    ROOT::RVecF SDV_bjetmindR(nSDV,-1);
    for (size_t iSDV=0; iSDV<nSDV; ++iSDV){
        
        ROOT::RVecF dRs;
        for (size_t iJet=0; i<nJet; ++iJet){
                dRs.push_back(dR(SDVSecVtx_phi[iSDV], Jet_phi[iJet], SDVSecVtx_eta[iSDV], Jet_eta[iJet]));
        }
        SDV_bjetmindR[iSDV] = ROOT::VecOps::Min(dRs);
    }
    return SDV_bjetmindR;
} */