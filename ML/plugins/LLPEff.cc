#include <memory>
#include <vector>
#include <set>
#include <algorithm>
#include <iostream>

#include "TTree.h"
#include "TMath.h"

#include "FWCore/Framework/interface/Event.h"
#include "FWCore/Framework/interface/Frameworkfwd.h"
#include "FWCore/Framework/interface/MakerMacros.h"
#include "FWCore/ServiceRegistry/interface/Service.h"
#include "CommonTools/UtilAlgos/interface/TFileService.h"
#include "FWCore/Framework/interface/stream/EDAnalyzer.h"
#include "FWCore/Framework/interface/one/EDAnalyzer.h"
#include "FWCore/ParameterSet/interface/ParameterSet.h"
#include "DataFormats/TrackReco/interface/Track.h"
#include "DataFormats/TrackReco/interface/TrackFwd.h"
#include "DataFormats/VertexReco/interface/Vertex.h"
#include "DataFormats/VertexReco/interface/VertexFwd.h"
#include "SoftDisplacedVertices/SoftDVDataFormats/interface/PFIsolation.h"
#include "TrackingTools/Records/interface/TransientTrackRecord.h"
#include "TrackingTools/TransientTrack/interface/TransientTrack.h"
#include "TrackingTools/TransientTrack/interface/TransientTrackBuilder.h"
#include "RecoVertex/VertexPrimitives/interface/TransientVertex.h"
#include "RecoVertex/ConfigurableVertexReco/interface/ConfigurableVertexReconstructor.h"
#include "RecoVertex/KalmanVertexFit/interface/KalmanVertexFitter.h"
#include "DataFormats/HepMCCandidate/interface/GenParticle.h"
#include "SoftDisplacedVertices/SoftDVDataFormats/interface/GenInfo.h"

#include "PhysicsTools/ONNXRuntime/interface/ONNXRuntime.h"

struct eventInfo
{
  int ntk;
  int ntk_llp;
  std::vector<int> llp_ntk;
  std::vector<int> llp_ntk_match;
  std::vector<float> llp_lxy;
  std::vector<float> llp_closest_genv_dist;
  std::vector<float> llp_closest_genv_dist_z;
  std::vector<float> llp_closest_genv_dist_2d;
  std::vector<float> llp_min_vtx_normchi2;
  std::vector<int> llp_matched;
  std::vector<int> vtx_matched;
  std::vector<float> vtx_chi2;
  std::vector<float> vtx_normchi2;
  std::vector<float> vtx_genvdist;
  std::vector<float> vtx_genvdist_z;
  std::vector<float> vtx_genvdist_2d;
};

class LLPEff: public edm::one::EDAnalyzer<edm::one::SharedResources> {
  public:
    explicit LLPEff(const edm::ParameterSet &);

  private:
    void beginJob();
    void analyze(const edm::Event&, const edm::EventSetup&) override;

    void initEventStructure();

    std::vector<float> track_input(reco::TrackRef tk, const reco::Vertex* pv, SoftDV::PFIsolation isoDR03);
    bool v_pass(const reco::Vertex& v, const reco::Vertex* pv);
    bool isGoodTrack(reco::TrackRef tk, const reco::Vertex* pv, SoftDV::PFIsolation isoDR03);

    const edm::EDGetTokenT<reco::VertexCollection> primary_vertex_token;
    const edm::EDGetTokenT<reco::VertexCollection> secondary_vertex_token;
    const edm::EDGetTokenT<reco::TrackCollection> tracks_token;
    edm::EDGetTokenT<std::vector<SoftDV::PFIsolation>> isoDR03Token_;

    const edm::EDGetTokenT<std::vector<reco::GenParticle>> genToken_;

    std::unique_ptr<VertexReconstructor> vtxReco;

    TTree *eventTree;
    eventInfo *evInfo;
};

LLPEff::LLPEff(const edm::ParameterSet &iConfig)
  : primary_vertex_token(consumes<reco::VertexCollection>(iConfig.getParameter<edm::InputTag>("primary_vertex_token"))),
    secondary_vertex_token(consumes<reco::VertexCollection>(iConfig.getParameter<edm::InputTag>("secondary_vertex_token"))),
    tracks_token(consumes<reco::TrackCollection>(iConfig.getParameter<edm::InputTag>("tracks"))),
    isoDR03Token_(consumes<std::vector<SoftDV::PFIsolation>>(iConfig.getParameter<edm::InputTag>("isoDR03"))),
    genToken_(consumes<std::vector<reco::GenParticle>>(iConfig.getParameter<edm::InputTag>("gen"))),
    vtxReco(new ConfigurableVertexReconstructor(iConfig.getParameter<edm::ParameterSet>("vtx_params"))){
    usesResource("TFileService");
    evInfo = new eventInfo;
    }

void LLPEff::analyze(const edm::Event &iEvent, const edm::EventSetup &iSetup) {
  initEventStructure();

  std::unique_ptr<reco::VertexCollection> vertices(new reco::VertexCollection);

  edm::Handle<reco::TrackCollection> tracks;
  iEvent.getByToken(tracks_token, tracks);

  edm::Handle<reco::VertexCollection> primary_vertices;
  iEvent.getByToken(primary_vertex_token, primary_vertices);
  const reco::Vertex* primary_vertex = &primary_vertices->at(0);
  if (primary_vertices->size()==0)
    throw cms::Exception("LLPEff") << "No Primary Vertices available!";

  edm::Handle<reco::VertexCollection> svs;
  iEvent.getByToken(secondary_vertex_token, svs);

  edm::Handle<std::vector<SoftDV::PFIsolation>> tracks_isoDR03;
  iEvent.getByToken(isoDR03Token_, tracks_isoDR03);
  if (tracks->size() != tracks_isoDR03->size())
    throw cms::Exception("LLPEff") << "Tracks mismatch with track IsoDR03!";

  edm::Handle<reco::GenParticleCollection> genParticles;
  iEvent.getByToken(genToken_, genParticles);

  // Get Gen info
  const std::vector<int> LLPid_ = {1000006};
  const int LSPid_ = 1000022;
  std::vector<int> llp_idx = SoftDV::FindLLP(genParticles, LLPid_, LSPid_, false);
  std::vector<std::set<reco::TrackRef>> llp_track_refs;
  std::set<reco::TrackRef> llp_all_track;
  std::map<reco::TrackRef,std::vector<float>> tkref_genv_pos;
  for (auto& illp : llp_idx) {
    std::set<reco::TrackRef> tk_refs;
    std::set<int> matched_dau_idx;
    const reco::GenParticle& llp = genParticles->at(illp);
    auto decay_point = llp.daughter(0)->vertex();
    float llp_lxy = std::hypot(decay_point.x()-primary_vertex->x(), decay_point.y()-primary_vertex->y());
    std::vector<int> llp_daus = SoftDV::GetDaughters(illp, genParticles, false);
    for (int igen:llp_daus){
      const reco::GenParticle& idau = genParticles->at(igen);
      const auto matchres = SoftDV::matchtracks(idau, tracks, primary_vertex->position());
      if (matchres.first!=-1) {
        reco::TrackRef mtk(tracks, matchres.first);
        tk_refs.insert(mtk);
        llp_all_track.insert(mtk);
        matched_dau_idx.insert(igen);
        tkref_genv_pos[mtk] = std::vector<float>({(float)idau.vx(),(float)idau.vy(),(float)idau.vz()});
      }
    }
    std::vector<int> matched_dau_idx_v(matched_dau_idx.begin(),matched_dau_idx.end());
    double d_min = 999;
    double d_min_2d = 999;
    double d_min_z = 999;
    for (size_t ig=0;ig<matched_dau_idx_v.size();++ig){
      for(size_t jg=ig+1;jg<matched_dau_idx_v.size();++jg){
        const reco::GenParticle& idau = genParticles->at(matched_dau_idx_v[ig]);
        const reco::GenParticle& jdau = genParticles->at(matched_dau_idx_v[jg]);
        double tempd = std::hypot(idau.vx()-jdau.vx(),idau.vy()-jdau.vy(),idau.vz()-jdau.vz());
        if (d_min>tempd) {
          d_min = tempd;
          d_min_2d = std::hypot(idau.vx()-jdau.vx(),idau.vy()-jdau.vy());
          d_min_z = fabs(idau.vz()-jdau.vz());
        }
      }
    }
    llp_track_refs.push_back(tk_refs);
    evInfo->llp_ntk.push_back(tk_refs.size());
    evInfo->ntk_llp += tk_refs.size();
    evInfo->llp_lxy.push_back(llp_lxy);
    evInfo->llp_closest_genv_dist.push_back((float)d_min);
    evInfo->llp_closest_genv_dist_z.push_back((float)d_min_z);
    evInfo->llp_closest_genv_dist_2d.push_back((float)d_min_2d);
  }
  if (llp_track_refs.size()!=2){
    throw cms::Exception("LLPEff") << "llp_track_idx.size incorrect!";
  }
  int nllp =llp_track_refs.size(); 

  int ntks = tracks->size();
  evInfo->ntk = ntks;
  evInfo->llp_matched = std::vector<int>(nllp,0);

  evInfo->llp_min_vtx_normchi2 = std::vector<float>(nllp,std::numeric_limits<float>::infinity());

  for (auto& v:(*svs)) {
    bool matched = false;
    float d = std::numeric_limits<float>::infinity();
    float d_2d = std::numeric_limits<float>::infinity();
    float d_z = std::numeric_limits<float>::infinity();
    for (int illp=0; illp<nllp; ++illp) {
      std::vector<reco::TrackRef> matched_vtks_illp;
      float dist3d_min = std::numeric_limits<float>::infinity();
      float dist2d_min = std::numeric_limits<float>::infinity();
      float dz_min = std::numeric_limits<float>::infinity();
      for (auto ivtk = v.tracks_begin(); ivtk<v.tracks_end(); ++ivtk) {
        reco::TrackRef ivtk_ref = ivtk->castTo<reco::TrackRef>();
        if (llp_track_refs[illp].find(ivtk_ref)==llp_track_refs[illp].end())
          continue;
        matched_vtks_illp.push_back(ivtk_ref);
      }
      if (matched_vtks_illp.size()>1) {
        for (size_t ivtk=0; ivtk<matched_vtks_illp.size(); ++ivtk){
          for (size_t jvtk=ivtk+1; jvtk<matched_vtks_illp.size(); ++jvtk) {
            reco::TrackRef ivtk_ref = matched_vtks_illp[ivtk];
            reco::TrackRef jvtk_ref = matched_vtks_illp[jvtk];
            if (tkref_genv_pos.find(ivtk_ref)==tkref_genv_pos.end())
              throw cms::Exception("LLPEff") << "Track Refi not found in map!";
            if (tkref_genv_pos.find(jvtk_ref)==tkref_genv_pos.end())
              throw cms::Exception("LLPEff") << "Track Refj not found in map!";
            std::vector<float> ivtk_pos = tkref_genv_pos[ivtk_ref];
            std::vector<float> jvtk_pos = tkref_genv_pos[jvtk_ref];
            float dist3d = std::hypot(ivtk_pos[0]-jvtk_pos[0],ivtk_pos[1]-jvtk_pos[1],ivtk_pos[2]-jvtk_pos[2]);
            float dist2d = std::hypot(ivtk_pos[0]-jvtk_pos[0],ivtk_pos[1]-jvtk_pos[1]);
            float dz = fabs(ivtk_pos[2]-jvtk_pos[2]);
            if (dist3d<dist3d_min)
              dist3d_min = dist3d;
            if (dist2d<dist2d_min)
              dist2d_min = dist2d;
            if (dz<dz_min)
              dz_min = dz;
            if (dist3d<d){
              d = dist3d;
              d_2d = dist2d;
              d_z = dz;
            }
          }
        }
      }
      if (dist3d_min<0.005){
        evInfo->llp_matched[illp] = true;
        matched = true;
      }
    }
    evInfo->vtx_chi2.push_back(v.chi2());
    evInfo->vtx_matched.push_back(matched);
    evInfo->vtx_normchi2.push_back(v.normalizedChi2());
    evInfo->vtx_genvdist.push_back(d);
    evInfo->vtx_genvdist_2d.push_back(d_2d);
    evInfo->vtx_genvdist_z.push_back(d_z);
  }

  eventTree->Fill();
}

std::vector<float> LLPEff::track_input(reco::TrackRef tk, const reco::Vertex* pv, SoftDV::PFIsolation isoDR03) {
  float pt = tk->pt();
  float eta = tk->eta();
  float phi = tk->phi();
  float dxy = tk->dxy(pv->position());
  float dxyError = tk->dxyError(pv->position(), pv->covariance());
  float dz = tk->dz(pv->position());
  float dzError = tk->dzError();
  float ptError = tk->ptError();
  float normchi2 = tk->normalizedChi2();
  float nvalidhits = tk->numberOfValidHits();
  float pfRelIso03_all = (isoDR03.chargedHadronIso() +
                            std::max<double>(isoDR03.neutralHadronIso() +
                                             isoDR03.photonIso() -
                                             isoDR03.puChargedHadronIso()/2,0.0))
                          / tk->pt();

  std::vector<float> tk_vars = {pt,eta,phi,dxy,dxyError,dz,dzError,pfRelIso03_all,ptError,normchi2,nvalidhits};
  return tk_vars;
}

bool LLPEff::v_pass(const reco::Vertex& v, const reco::Vertex* pv) {
  if (!v.isValid())
    return false;
  if (v.normalizedChi2()>10)
    return false;
  double dx = (v.x() - pv->x());
  double dy = (v.y() - pv->y());
  double dz = (v.z() - pv->z());
  double pdotv = (dx * v.p4().Px() + dy * v.p4().Py() + dz * v.p4().Pz()) / sqrt(v.p4().P2()) / sqrt(dx * dx + dy * dy + dz * dz);
  if (std::acos(pdotv)>(TMath::Pi()/2))
    return false;
  return true;
}

bool LLPEff::isGoodTrack(reco::TrackRef tk, const reco::Vertex* pv, SoftDV::PFIsolation isoDR03) {
  float pt = tk->pt();
  float eta = tk->eta();
  float phi = tk->phi();
  float dxy = tk->dxy(pv->position());
  float dxyError = tk->dxyError(pv->position(), pv->covariance());
  float dz = tk->dz(pv->position());
  float dzError = tk->dzError();
  float ptError = tk->ptError();
  float normchi2 = tk->normalizedChi2();
  float nvalidhits = tk->numberOfValidHits();
  float pfRelIso03_all = (isoDR03.chargedHadronIso() +
                            std::max<double>(isoDR03.neutralHadronIso() +
                                             isoDR03.photonIso() -
                                             isoDR03.puChargedHadronIso()/2,0.0))
                          / tk->pt();

  if ( (abs(dxy/dxyError)>4 ) && (abs(dxy/dz)>0.25) && (pfRelIso03_all<5) && (normchi2<5) && (nvalidhits>13) && (ptError/pt <0.015) )
    return true;
  return false;
}

void LLPEff::beginJob()
{
  edm::Service<TFileService> fs;
  eventTree = fs->make<TTree>( "treeGNN", "treeGNN" );

  eventTree->Branch("ntk",  &evInfo->ntk);
  eventTree->Branch("ntk_llp",  &evInfo->ntk_llp);
  eventTree->Branch("llp_ntk",  &evInfo->llp_ntk);
  eventTree->Branch("llp_lxy",  &evInfo->llp_lxy);
  eventTree->Branch("llp_ntk_match",  &evInfo->llp_ntk_match);
  eventTree->Branch("llp_matched",  &evInfo->llp_matched);
  eventTree->Branch("llp_closest_genv_dist",  &evInfo->llp_closest_genv_dist);
  eventTree->Branch("llp_closest_genv_dist_z",  &evInfo->llp_closest_genv_dist_z);
  eventTree->Branch("llp_closest_genv_dist_2d",  &evInfo->llp_closest_genv_dist_2d);
  eventTree->Branch("llp_min_vtx_normchi2",  &evInfo->llp_min_vtx_normchi2);
  eventTree->Branch("vtx_chi2",  &evInfo->vtx_chi2);
  eventTree->Branch("vtx_matched",  &evInfo->vtx_matched);
  eventTree->Branch("vtx_normchi2",  &evInfo->vtx_normchi2);
  eventTree->Branch("vtx_genvdist",  &evInfo->vtx_genvdist);
  eventTree->Branch("vtx_genvdist_2d",  &evInfo->vtx_genvdist_2d);
  eventTree->Branch("vtx_genvdist_z",  &evInfo->vtx_genvdist_z);
}

void LLPEff::initEventStructure()
{
  evInfo->ntk = 0;
  evInfo->ntk_llp = 0;
  evInfo->llp_ntk.clear();
  evInfo->llp_lxy.clear();
  evInfo->llp_ntk_match.clear();
  evInfo->llp_matched.clear();
  evInfo->vtx_chi2.clear();
  evInfo->vtx_matched.clear();
  evInfo->vtx_normchi2.clear();
  evInfo->vtx_genvdist.clear();
  evInfo->vtx_genvdist_2d.clear();
  evInfo->vtx_genvdist_z.clear();
  evInfo->llp_closest_genv_dist.clear();
  evInfo->llp_closest_genv_dist_z.clear();
  evInfo->llp_closest_genv_dist_2d.clear();
  evInfo->llp_min_vtx_normchi2.clear();
}

DEFINE_FWK_MODULE(LLPEff);
