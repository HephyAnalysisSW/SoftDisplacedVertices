#include "TTree.h"
#include "CommonTools/UtilAlgos/interface/TFileService.h"
#include "DataFormats/Math/interface/deltaR.h"
#include "DataFormats/Math/interface/deltaPhi.h"
#include "DataFormats/PatCandidates/interface/Jet.h"
#include "DataFormats/PatCandidates/interface/MET.h"
#include "DataFormats/METReco/interface/METFwd.h"
#include "DataFormats/METReco/interface/PFMET.h"
#include "DataFormats/METReco/interface/PFMETFwd.h"
#include "DataFormats/VertexReco/interface/Vertex.h"
#include "DataFormats/VertexReco/interface/VertexFwd.h"
#include "FWCore/Framework/interface/one/EDAnalyzer.h"
#include "FWCore/Framework/interface/Event.h"
#include "FWCore/Framework/interface/MakerMacros.h"
#include "FWCore/ServiceRegistry/interface/Service.h"
#include "RecoVertex/VertexTools/interface/VertexDistance3D.h"
#include "RecoVertex/VertexTools/interface/VertexDistanceXY.h"
#include "TrackingTools/IPTools/interface/IPTools.h"
#include "TrackingTools/Records/interface/TransientTrackRecord.h"
#include "TrackingTools/TransientTrack/interface/TransientTrack.h"
#include "TrackingTools/TransientTrack/interface/TransientTrackBuilder.h"
#include "SoftDisplacedVertices/SoftDVDataFormats/interface/GenInfo.h"

struct MLInfo
{
  int vtx_match;
  int vtx_nmatchtks;
  int label_llp;
  double vtx_x;
  double vtx_y;
  double vtx_z;
  double vtx_ntracks;
  double vtx_normchi2;
  double vtx_ndof;
  double vtx_lxy;
  double vtx_lxy_err;
  double vtx_dphi_jet1;
  double vtx_dphi_met;
  double vtx_acollinearity;
  double vtx_E;
  double vtx_pt;
  std::vector<double> vtx_tk_px;
  std::vector<double> vtx_tk_py;
  std::vector<double> vtx_tk_pz;
  std::vector<double> vtx_tk_pt;
  std::vector<double> vtx_tk_eta;
  std::vector<double> vtx_tk_phi;
  std::vector<double> vtx_tk_E;
  std::vector<double> vtx_tk_normchi2;
  std::vector<double> vtx_tk_dxy;
  std::vector<double> vtx_tk_dxyerr;
  std::vector<double> vtx_tk_dz;
  std::vector<double> vtx_tk_dzerr;
  std::vector<double> vtx_tk_nvalidhits;
  std::vector<double> vtx_tk_dphi_jet1;
  std::vector<double> vtx_tk_dphi_met;
  std::vector<double> vtx_tk_dphi_Lvtx;
  std::vector<double> vtx_tk_deta_Lvtx;
  std::vector<double> vtx_tk_dphi_pvtx;
  std::vector<double> vtx_tk_deta_pvtx;
  std::vector<double> vtx_tk_pterr;
  std::vector<double> vtx_tk_weight;
  std::vector<double> vtx_tk_dist2d;
  std::vector<double> vtx_tk_dist2derr;
  std::vector<double> vtx_tk_dist3d;
  std::vector<double> vtx_tk_dist3derr;
};

class MLTree : public edm::one::EDAnalyzer<edm::one::SharedResources> {
  public:
    explicit MLTree(const edm::ParameterSet&);
    void analyze(const edm::Event&, const edm::EventSetup&);

  private:
    virtual void beginJob() override;
    virtual void endJob() override;
    void initEventStructure();
    
    const edm::EDGetTokenT<reco::BeamSpot> beamspot_token;
    const edm::EDGetTokenT<reco::VertexCollection> primary_vertex_token;
    const edm::EDGetTokenT<pat::JetCollection> jet_token;
    const edm::EDGetTokenT<pat::METCollection> met_token;
    const edm::EDGetTokenT<reco::VertexCollection> vtx_token;
    const edm::EDGetTokenT<std::vector<reco::GenParticle>> gen_token;
    const edm::EDGetTokenT<reco::TrackCollection> tk_token;

    const std::vector<int> LLPid_;
    const int LSPid_;
    
    bool debug;

    TTree *mlTree;
    MLInfo *mlInfo;

    VertexDistanceXY distcalc_2d;
    VertexDistance3D distcalc_3d;
};

MLTree::MLTree(const edm::ParameterSet& cfg)
  : beamspot_token(consumes<reco::BeamSpot>(cfg.getParameter<edm::InputTag>("beamspot_token"))),
    primary_vertex_token(consumes<reco::VertexCollection>(cfg.getParameter<edm::InputTag>("primary_vertex_token"))),
    jet_token(consumes<pat::JetCollection>(cfg.getParameter<edm::InputTag>("jet_token"))),
    met_token(consumes<pat::METCollection>(cfg.getParameter<edm::InputTag>("met_token"))),
    vtx_token(consumes<reco::VertexCollection>(cfg.getParameter<edm::InputTag>("vtx_token"))),
    gen_token(consumes<std::vector<reco::GenParticle>>(cfg.getParameter<edm::InputTag>("gen_token"))),
    tk_token(consumes<reco::TrackCollection>(cfg.getParameter<edm::InputTag>("tk_token"))),
    LLPid_(cfg.getParameter<std::vector<int>>("LLPid_")),
    LSPid_(cfg.getParameter<int>("LSPid_")),
    debug(cfg.getParameter<bool>("debug"))
{
  mlInfo = new MLInfo;
}

void MLTree::analyze(const edm::Event& event, const edm::EventSetup& setup) {
  initEventStructure();
  edm::Handle<pat::JetCollection> jets;
  event.getByToken(jet_token, jets);

  edm::Handle<pat::METCollection> mets;
  event.getByToken(met_token, mets);

  edm::Handle<reco::BeamSpot> beamspot;
  event.getByToken(beamspot_token, beamspot);

  const reco::Vertex fake_bs_vtx(beamspot->position(), beamspot->covariance3D());

  edm::Handle<reco::VertexCollection> primary_vertices;
  event.getByToken(primary_vertex_token, primary_vertices);
  const reco::Vertex* primary_vertex = 0;
  if (primary_vertices->size())
    primary_vertex = &primary_vertices->at(0);

  edm::Handle<reco::VertexCollection> vertices;
  event.getByToken(vtx_token, vertices);

  edm::Handle<reco::GenParticleCollection> genParticles;
  event.getByToken(gen_token, genParticles);

  edm::Handle<reco::TrackCollection> tracks;
  event.getByToken(tk_token, tracks);

  edm::ESHandle<TransientTrackBuilder> tt_builder;
  setup.get<TransientTrackRecord>().get("TransientTrackBuilder", tt_builder);

  std::map<int,std::pair<int,int>> vtxllpmatch = SoftDV::VtxLLPMatch( genParticles, vertices, tracks, primary_vertex->position(), debug);

  int jet_leading_idx = -1;
  double jet_pt_max = -1;
  for(size_t ijet=0; ijet<jets->size(); ++ijet){
    const auto& jet = jets->at(ijet);
    if (jet.pt()>jet_pt_max) {
      jet_leading_idx = ijet;
      jet_pt_max = jet.pt();
    }
  }

  const auto& met = mets->at(0);
  if (met.pt()<200)
    return;

  //const reco::PFJet& leading_jet = jets->at(jet_leading_idx);
  const auto& leading_jet = jets->at(jet_leading_idx);

  for(size_t ivtx=0; ivtx<vertices->size(); ++ivtx) {
    initEventStructure();
    const reco::Vertex& vtx = vertices->at(ivtx);
    math::XYZVector l_vector = vtx.position() - primary_vertex->position();
    //const auto d = distcalc_2d.distance(vtx, fake_bs_vtx);
    const auto d = distcalc_2d.distance(vtx, *primary_vertex);

    if (vtxllpmatch.find(ivtx) != vtxllpmatch.end()){
      mlInfo->vtx_nmatchtks = vtxllpmatch[ivtx].second;
      mlInfo->label_llp = vtxllpmatch[ivtx].second>1?1:0;
    }
    else {
      mlInfo->vtx_nmatchtks = 0;
      mlInfo->label_llp = 0;
    }
    mlInfo->vtx_x = vtx.x();
    mlInfo->vtx_y = vtx.y();
    mlInfo->vtx_z = vtx.z();
    mlInfo->vtx_ntracks = vtx.tracksSize();
    mlInfo->vtx_normchi2 = vtx.normalizedChi2();
    mlInfo->vtx_ndof = vtx.ndof();
    mlInfo->vtx_lxy = d.value();
    mlInfo->vtx_lxy_err = d.error();
    mlInfo->vtx_dphi_jet1 = reco::deltaPhi(l_vector, leading_jet);
    mlInfo->vtx_dphi_met = reco::deltaPhi(l_vector, met);
    mlInfo->vtx_acollinearity = reco::deltaPhi(l_vector, vtx.p4());
    mlInfo->vtx_E = vtx.p4().E();
    mlInfo->vtx_pt = vtx.p4().pt();

    std::vector<double> tk_px;
    std::vector<double> tk_py;
    std::vector<double> tk_pz;
    std::vector<double> tk_pt;
    std::vector<double> tk_eta;
    std::vector<double> tk_phi;
    std::vector<double> tk_E;
    std::vector<double> tk_normchi2;
    std::vector<double> tk_dxy;
    std::vector<double> tk_dxyerr;
    std::vector<double> tk_dz;
    std::vector<double> tk_dzerr;
    std::vector<double> tk_nvalidhits;
    std::vector<double> tk_dphi_jet1;
    std::vector<double> tk_dphi_met;
    std::vector<double> tk_dphi_Lvtx;
    std::vector<double> tk_deta_Lvtx;
    std::vector<double> tk_dphi_pvtx;
    std::vector<double> tk_deta_pvtx;
    std::vector<double> tk_pterr;
    std::vector<double> tk_weight;
    std::vector<double> tk_dist2d;
    std::vector<double> tk_dist2derr;
    std::vector<double> tk_dist3d;
    std::vector<double> tk_dist3derr;

    const double mass = 0.13957018;
    for (auto v_tk = vtx.tracks_begin(), vtke = vtx.tracks_end(); v_tk != vtke; ++v_tk){
      tk_px.push_back((*v_tk)->px());
      tk_py.push_back((*v_tk)->py());
      tk_pz.push_back((*v_tk)->pz());
      tk_pt.push_back((*v_tk)->pt());
      tk_eta.push_back((*v_tk)->eta());
      tk_phi.push_back((*v_tk)->phi());
      ROOT::Math::LorentzVector<ROOT::Math::PxPyPzM4D<double> > vec;
      vec.SetPx((*v_tk)->px());
      vec.SetPy((*v_tk)->py());
      vec.SetPz((*v_tk)->pz());
      vec.SetM(mass);
      tk_E.push_back(vec.E());
      tk_normchi2.push_back((*v_tk)->normalizedChi2());
      tk_dxy.push_back((*v_tk)->dxy(primary_vertex->position()));
      tk_dxyerr.push_back((*v_tk)->dxyError(primary_vertex->position(), primary_vertex->covariance()));
      tk_dz.push_back((*v_tk)->dz(primary_vertex->position()));
      tk_dzerr.push_back((*v_tk)->dzError());
      tk_nvalidhits.push_back((*v_tk)->numberOfValidHits());
      tk_dphi_jet1.push_back(reco::deltaPhi((**v_tk),leading_jet));
      tk_dphi_met.push_back(reco::deltaPhi((**v_tk),met));
      tk_dphi_Lvtx.push_back(reco::deltaPhi((**v_tk),l_vector));
      tk_deta_Lvtx.push_back(fabs((**v_tk).eta()-l_vector.eta()));
      tk_dphi_pvtx.push_back(reco::deltaPhi((**v_tk),vtx.p4()));
      tk_deta_pvtx.push_back(fabs((**v_tk).eta()-vtx.p4().eta()));
      tk_pterr.push_back((*v_tk)->ptError());
      tk_weight.push_back(vtx.trackWeight((*v_tk)));

      reco::TransientTrack ttk = tt_builder->build(**v_tk);
      auto dist2d = IPTools::absoluteTransverseImpactParameter(ttk, vtx);
      auto dist3d = IPTools::absoluteImpactParameter3D(ttk, vtx);
      if (dist2d.first) {
        tk_dist2d.push_back(dist2d.second.value());
        tk_dist2derr.push_back(dist2d.second.error());
      }
      else {
        tk_dist2d.push_back(-1);
        tk_dist2derr.push_back(-1);
      }
      if (dist3d.first) {
        tk_dist3d.push_back(dist3d.second.value());
        tk_dist3derr.push_back(dist3d.second.error());
      }
      else {
        tk_dist3d.push_back(-1);
        tk_dist3derr.push_back(-1);
      }
    }
    mlInfo->vtx_tk_px = tk_px;
    mlInfo->vtx_tk_py = tk_py;
    mlInfo->vtx_tk_pz = tk_pz;
    mlInfo->vtx_tk_pt = tk_pt;
    mlInfo->vtx_tk_eta = tk_eta;
    mlInfo->vtx_tk_phi = tk_phi;
    mlInfo->vtx_tk_E = tk_E;
    mlInfo->vtx_tk_normchi2 = tk_normchi2;
    mlInfo->vtx_tk_dxy = tk_dxy;
    mlInfo->vtx_tk_dxyerr = tk_dxyerr;
    mlInfo->vtx_tk_dz = tk_dz;
    mlInfo->vtx_tk_dzerr = tk_dzerr;
    mlInfo->vtx_tk_nvalidhits = tk_nvalidhits;
    mlInfo->vtx_tk_dphi_jet1 = tk_dphi_jet1;
    mlInfo->vtx_tk_dphi_met = tk_dphi_met;
    mlInfo->vtx_tk_dphi_Lvtx = tk_dphi_Lvtx;
    mlInfo->vtx_tk_deta_Lvtx = tk_deta_Lvtx;
    mlInfo->vtx_tk_dphi_pvtx = tk_dphi_pvtx;
    mlInfo->vtx_tk_deta_pvtx = tk_deta_pvtx;
    mlInfo->vtx_tk_pterr = tk_pterr;
    mlInfo->vtx_tk_weight = tk_weight;
    mlInfo->vtx_tk_dist2d = tk_dist2d;
    mlInfo->vtx_tk_dist2derr = tk_dist2derr;
    mlInfo->vtx_tk_dist3d = tk_dist3d;
    mlInfo->vtx_tk_dist3derr = tk_dist3derr;

    mlTree->Fill();

  }

}

void MLTree::beginJob()
{
  edm::Service<TFileService> fs;
  mlTree = fs->make<TTree>( "tree", "tree" );

  mlTree->Branch("vtx_match",      &mlInfo->vtx_match);
  mlTree->Branch("vtx_nmatchtks",      &mlInfo->vtx_nmatchtks);
  mlTree->Branch("label_llp",      &mlInfo->label_llp);
  mlTree->Branch("vtx_x",      &mlInfo->vtx_x);
  mlTree->Branch("vtx_y",      &mlInfo->vtx_y);
  mlTree->Branch("vtx_z",      &mlInfo->vtx_z);
  mlTree->Branch("vtx_ntracks",&mlInfo->vtx_ntracks);
  mlTree->Branch("vtx_normchi2",   &mlInfo->vtx_normchi2);
  mlTree->Branch("vtx_ndof",   &mlInfo->vtx_ndof);
  mlTree->Branch("vtx_lxy",    &mlInfo->vtx_lxy);
  mlTree->Branch("vtx_lxy_err",&mlInfo->vtx_lxy_err);
  mlTree->Branch("vtx_dphi_jet1", &mlInfo->vtx_dphi_jet1);
  mlTree->Branch("vtx_dphi_met",  &mlInfo->vtx_dphi_met);
  mlTree->Branch("vtx_acollinearity", &mlInfo->vtx_acollinearity);
  mlTree->Branch("vtx_E", &mlInfo->vtx_E);
  mlTree->Branch("vtx_pt",  &mlInfo->vtx_pt);
  mlTree->Branch("vtx_tk_px", &mlInfo->vtx_tk_px);
  mlTree->Branch("vtx_tk_py", &mlInfo->vtx_tk_py);
  mlTree->Branch("vtx_tk_pz", &mlInfo->vtx_tk_pz);
  mlTree->Branch("vtx_tk_pt", &mlInfo->vtx_tk_pt);
  mlTree->Branch("vtx_tk_eta", &mlInfo->vtx_tk_eta);
  mlTree->Branch("vtx_tk_phi", &mlInfo->vtx_tk_phi);
  mlTree->Branch("vtx_tk_E", &mlInfo->vtx_tk_E);
  mlTree->Branch("vtx_tk_normchi2", &mlInfo->vtx_tk_normchi2);
  mlTree->Branch("vtx_tk_dxy",  &mlInfo->vtx_tk_dxy);
  mlTree->Branch("vtx_tk_dxyerr", &mlInfo->vtx_tk_dxyerr);
  mlTree->Branch("vtx_tk_dz", &mlInfo->vtx_tk_dz);
  mlTree->Branch("vtx_tk_dzerr",  &mlInfo->vtx_tk_dzerr);
  mlTree->Branch("vtx_tk_nvalidhits", &mlInfo->vtx_tk_nvalidhits);
  mlTree->Branch("vtx_tk_dphi_jet1",  &mlInfo->vtx_tk_dphi_jet1);
  mlTree->Branch("vtx_tk_dphi_met", &mlInfo->vtx_tk_dphi_met);
  mlTree->Branch("vtx_tk_dphi_Lvtx", &mlInfo->vtx_tk_dphi_Lvtx);
  mlTree->Branch("vtx_tk_deta_Lvtx", &mlInfo->vtx_tk_deta_Lvtx);
  mlTree->Branch("vtx_tk_dphi_pvtx", &mlInfo->vtx_tk_dphi_pvtx);
  mlTree->Branch("vtx_tk_deta_pvtx", &mlInfo->vtx_tk_deta_pvtx);
  mlTree->Branch("vtx_tk_pterr",  &mlInfo->vtx_tk_pterr);
  mlTree->Branch("vtx_tk_weight", &mlInfo->vtx_tk_weight);
  mlTree->Branch("vtx_tk_dist2d", &mlInfo->vtx_tk_dist2d);
  mlTree->Branch("vtx_tk_dist2derr",  &mlInfo->vtx_tk_dist2derr);
  mlTree->Branch("vtx_tk_dist3d", &mlInfo->vtx_tk_dist3d);
  mlTree->Branch("vtx_tk_dist3derr",  &mlInfo->vtx_tk_dist3derr);
}

void MLTree::endJob()
{}

void MLTree::initEventStructure()
{
  mlInfo->vtx_match = -1;
  mlInfo->vtx_nmatchtks = -1;
  mlInfo->label_llp = 0;
  mlInfo->vtx_x = -999;
  mlInfo->vtx_y = -999;
  mlInfo->vtx_z = -999;
  mlInfo->vtx_ntracks = -1;
  mlInfo->vtx_ndof = -1;
  mlInfo->vtx_normchi2 = -1;
  mlInfo->vtx_lxy = -1;
  mlInfo->vtx_lxy_err = -1;
  mlInfo->vtx_dphi_jet1 = -999;
  mlInfo->vtx_dphi_met = -999;
  mlInfo->vtx_acollinearity = -999;
  mlInfo->vtx_E = -1;
  mlInfo->vtx_pt = -1;
  mlInfo->vtx_tk_px.clear();
  mlInfo->vtx_tk_py.clear();
  mlInfo->vtx_tk_pz.clear();
  mlInfo->vtx_tk_pt.clear();
  mlInfo->vtx_tk_eta.clear();
  mlInfo->vtx_tk_phi.clear();
  mlInfo->vtx_tk_E.clear();
  mlInfo->vtx_tk_normchi2.clear();
  mlInfo->vtx_tk_dxy.clear();
  mlInfo->vtx_tk_dxyerr.clear();
  mlInfo->vtx_tk_dz.clear();
  mlInfo->vtx_tk_dzerr.clear();
  mlInfo->vtx_tk_nvalidhits.clear();
  mlInfo->vtx_tk_dphi_jet1.clear();
  mlInfo->vtx_tk_dphi_met.clear();
  mlInfo->vtx_tk_dphi_Lvtx.clear();
  mlInfo->vtx_tk_deta_Lvtx.clear();
  mlInfo->vtx_tk_dphi_pvtx.clear();
  mlInfo->vtx_tk_deta_pvtx.clear();
  mlInfo->vtx_tk_pterr.clear();
  mlInfo->vtx_tk_weight.clear();
  mlInfo->vtx_tk_dist2d.clear();
  mlInfo->vtx_tk_dist2derr.clear();
  mlInfo->vtx_tk_dist3d.clear();
  mlInfo->vtx_tk_dist3derr.clear();
}

DEFINE_FWK_MODULE(MLTree);
