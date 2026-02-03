// This producer produces the table of LLP information
// Also, it makes the mapping between LLP and all the gen level decay products

// system include files
#include <memory>
#include <queue>
#include <vector>

// user include files
#include "FWCore/Framework/interface/Frameworkfwd.h"
#include "FWCore/Framework/interface/stream/EDProducer.h"

#include "FWCore/Framework/interface/Event.h"
#include "FWCore/Framework/interface/MakerMacros.h"

#include "FWCore/ParameterSet/interface/ParameterSet.h"
#include "FWCore/Utilities/interface/StreamID.h"

#include "DataFormats/TrackReco/interface/Track.h"
#include "DataFormats/TrackReco/interface/TrackFwd.h"
#include "DataFormats/VertexReco/interface/Vertex.h"
#include "DataFormats/VertexReco/interface/VertexFwd.h"
#include "DataFormats/NanoAOD/interface/FlatTable.h"
#include "DataFormats/HepMCCandidate/interface/GenParticle.h"
#include "SoftDisplacedVertices/SoftDVDataFormats/interface/GenInfo.h"

class LLPTableProducer : public edm::stream::EDProducer<> {
  public:
    explicit LLPTableProducer(const edm::ParameterSet&);
    ~LLPTableProducer() override;

    static void fillDescriptions(edm::ConfigurationDescriptions& descriptions);

  private:
    void beginStream(edm::StreamID) override;
    void produce(edm::Event&, const edm::EventSetup&) override;
    void endStream() override;

    const edm::EDGetTokenT<std::vector<reco::GenParticle>> genToken_;
    const std::string LLPName_;
    const std::string LLPDoc_;
    const edm::EDGetTokenT<reco::VertexCollection> pvToken_;
    const edm::EDGetTokenT<reco::TrackCollection> tkToken_;
    const edm::EDGetTokenT<reco::VertexCollection> svToken_;
    bool debug;
};

LLPTableProducer::LLPTableProducer(const edm::ParameterSet& params)
  : genToken_(consumes<std::vector<reco::GenParticle>>(params.getParameter<edm::InputTag>("src"))),
    LLPName_(params.getParameter<std::string>("LLPName")),
    LLPDoc_(params.getParameter<std::string>("LLPDoc")),
    pvToken_(consumes<reco::VertexCollection>(params.getParameter<edm::InputTag>("pvToken"))),
    tkToken_(consumes<reco::TrackCollection>(params.getParameter<edm::InputTag>("tkToken"))),
    svToken_(consumes<reco::VertexCollection>(params.getParameter<edm::InputTag>("svToken"))),
    debug(params.getParameter<bool>("debug"))
{
  produces<nanoaod::FlatTable>("LLPs");
  produces<nanoaod::FlatTable>("GenPart");
  produces<nanoaod::FlatTable>("GenSecVtx");
  produces<nanoaod::FlatTable>("SDVTrack");
  produces<nanoaod::FlatTable>("SDVSecVtx");
}

LLPTableProducer::~LLPTableProducer() {}

void LLPTableProducer::produce(edm::Event& iEvent, const edm::EventSetup& iSetup) {
  edm::Handle<reco::GenParticleCollection> genParticles;
  iEvent.getByToken(genToken_, genParticles);
  edm::Handle<reco::VertexCollection> primary_vertices;
  iEvent.getByToken(pvToken_, primary_vertices);

  const reco::Vertex* primary_vertex = 0;
  if (primary_vertices->size())
    primary_vertex = &primary_vertices->at(0);

  edm::Handle<reco::TrackCollection> tracks;
  iEvent.getByToken(tkToken_, tracks);

  edm::Handle<reco::VertexCollection> secondary_vertices;
  iEvent.getByToken(svToken_, secondary_vertices);

  std::pair<std::vector<int>,std::vector<int>> llp_idx_dm = SoftDV::FindLLP(genParticles, debug);
  std::vector<int> llp_idx = llp_idx_dm.first;
  std::vector<int> llp_decaymdoe = llp_idx_dm.second;
  std::vector<float> llp_pt, llp_eta, llp_phi, llp_mass, llp_ctau, llp_decay_x, llp_decay_y, llp_decay_z;
  std::vector<int> llp_pdgId, llp_status, llp_statusFlags, llp_ngentk, llp_nrecotk, llp_dm;

  std::vector<int> genpart_llpidx(genParticles->size(), -1);
  std::vector<int> genpart_pdgId(genParticles->size(), 0);
  std::vector<int> genpart_isgentk(genParticles->size(), 0);
  std::vector<int> genpart_recomatch(genParticles->size(), -1);
  std::vector<int> genpart_charge(genParticles->size(), 0);
  std::vector<float> genpart_recomatch_dr(genParticles->size(), -1);
  std::vector<float> genpart_dxy(genParticles->size(), -1);
  std::vector<float> genpart_dz(genParticles->size(), -1);
  std::vector<float> genpart_vertex_x(genParticles->size(), -1);
  std::vector<float> genpart_vertex_y(genParticles->size(), -1);
  std::vector<float> genpart_vertex_z(genParticles->size(), -1);
  std::vector<float> gensecvtx_llpidx;
  std::vector<float> gensecvtx_x;
  std::vector<float> gensecvtx_y;
  std::vector<float> gensecvtx_z;
  std::vector<int> tk_genpartidx(tracks->size(), -1);
  std::vector<int> tk_llpidx(tracks->size(), -1);
  std::vector<int> tk_gensecvtxidx(tracks->size(), -1);

  //for (size_t igen=0; igen<genParticles->size(); ++igen) {
  //  const reco::GenParticle& iigen = genParticles->at(igen);
  //  genpart_pdgId[igen] = iigen.pdgId();
  //}

  for (size_t illp=0; illp<llp_idx.size(); ++illp){
    const reco::GenParticle& llp = genParticles->at(llp_idx[illp]);
    llp_pt.push_back(llp.pt());
    llp_eta.push_back(llp.eta());
    llp_phi.push_back(llp.phi());
    llp_mass.push_back(llp.mass());
    llp_pdgId.push_back(llp.pdgId());
    llp_dm.push_back(llp_decaymdoe[illp]);
    llp_status.push_back(llp.status());
    llp_statusFlags.push_back( llp.statusFlags().isLastCopyBeforeFSR()             * 16384 +llp.statusFlags().isLastCopy()                           * 8192  +llp.statusFlags().isFirstCopy()                          * 4096  +llp.statusFlags().fromHardProcessBeforeFSR()             * 2048  +llp.statusFlags().isDirectHardProcessTauDecayProduct()   * 1024  +llp.statusFlags().isHardProcessTauDecayProduct()         * 512   +llp.statusFlags().fromHardProcess()                      * 256   +llp.statusFlags().isHardProcess()                        * 128   +llp.statusFlags().isDirectHadronDecayProduct()           * 64    +llp.statusFlags().isDirectPromptTauDecayProduct()        * 32    +llp.statusFlags().isDirectTauDecayProduct()              * 16    +llp.statusFlags().isPromptTauDecayProduct()              * 8     +llp.statusFlags().isTauDecayProduct()                    * 4     +llp.statusFlags().isDecayedLeptonHadron()                * 2     +llp.statusFlags().isPrompt()                             * 1);
    // Now determine the LLP decay point
    if (llp.numberOfDaughters()==0){
      throw cms::Exception("LLPTableProducer") << "LLP has no Daughters!";
    }

    if (!llp.daughter(0)) {
      throw cms::Exception("LLPTableProducer") << "LLP daughter pointer is null!";
    }

    if (debug)
    {
      for (size_t idau=0; idau<llp.numberOfDaughters(); ++idau){
        std::cout << "LLP daughter " << idau << " ID " << llp.daughter(idau)->pdgId() << std::endl;
        std::cout << llp.daughter(idau)->vertex().x() << std::endl;
      }
    }
    auto decay_point = llp.daughter(0)->vertex();
    llp_decay_x.push_back(decay_point.x());
    llp_decay_y.push_back(decay_point.y());
    llp_decay_z.push_back(decay_point.z());

    math::XYZVector flight = math::XYZVector(decay_point) - math::XYZVector(primary_vertex->position());
    auto polarp4 = llp.polarP4();
    float ctau = std::sqrt(flight.Mag2())/polarp4.Beta()/polarp4.Gamma();
    llp_ctau.push_back(ctau);

    // Get the LLP decay products
    std::vector<int> llp_daus = SoftDV::GetDaughters(llp_idx[illp], genParticles, debug);
    int ngentk = 0;
    int nmatchedtk = 0;

    for (int igen:llp_daus){
      const reco::GenParticle& idau = genParticles->at(igen);
      genpart_llpidx[igen] = illp;
      genpart_pdgId[igen] = idau.pdgId();
      genpart_dxy[igen] = gen_dxy(idau, primary_vertex->position());
      genpart_dz[igen] = gen_dz(idau, primary_vertex->position());
      genpart_charge[igen] = idau.charge();
      genpart_vertex_x[igen] = idau.vx();
      genpart_vertex_y[igen] = idau.vy();
      genpart_vertex_z[igen] = idau.vz();
      if (SoftDV::pass_gentk(idau, primary_vertex->position())){
        ngentk += 1;
        genpart_isgentk[igen] = 1;
      }
      else{
        genpart_isgentk[igen] = 0;
      }
      const auto matchres = SoftDV::matchtracks(idau, tracks, primary_vertex->position());
      if (matchres.first!=-1) {
        tk_genpartidx[matchres.first] = igen;
        tk_llpidx[matchres.first] = illp;
        nmatchedtk += 1;
        genpart_recomatch[igen] = matchres.first;
        genpart_recomatch_dr[igen] = matchres.second.second[0];
      }
    }
    std::vector<SoftDV::Point> illp_vertices;
    for (size_t itk=0; itk<tk_genpartidx.size(); ++itk) {
      if ((tk_genpartidx[itk]==-1) || (tk_llpidx[itk]!=int(illp)) ) continue;
      int tk_genidx = tk_genpartidx[itk];
      SoftDV::Point tk_vtx = SoftDV::Point();
      tk_vtx.SetXYZ(genpart_vertex_x[tk_genidx],genpart_vertex_y[tk_genidx],genpart_vertex_z[tk_genidx]);
      bool vtx_isNew = true;
      int tk_vtx_idx = -1;
      for (size_t illpvtx=0; illpvtx<illp_vertices.size(); ++illpvtx) {
        // if the vertices are close to each other (within 50um)
        if ((illp_vertices[illpvtx]-tk_vtx).mag2()<0.000025) {
          vtx_isNew = false;
          tk_vtx_idx = illpvtx+gensecvtx_x.size();
        }
      }
      if (vtx_isNew) {
        illp_vertices.push_back(tk_vtx);
        tk_vtx_idx = illp_vertices.size()-1+gensecvtx_x.size();
      }
      tk_gensecvtxidx[itk] = tk_vtx_idx;
    }
    for (auto& igensecvtx: illp_vertices) {
      gensecvtx_llpidx.push_back(illp);
      gensecvtx_x.push_back(igensecvtx.x());
      gensecvtx_y.push_back(igensecvtx.y());
      gensecvtx_z.push_back(igensecvtx.z());
    }
    llp_ngentk.push_back(ngentk);
    llp_nrecotk.push_back(nmatchedtk);
  }

  // Match LLP with reco vertices
  std::vector<int> llp_match_bydau(llp_idx.size(), -1);
  std::vector<int> llp_match_bydau_ntk(llp_idx.size(), 0);
  std::vector<float> llp_match_bydau_dist(llp_idx.size(), -1);
  std::vector<int> llp_match_bydist(llp_idx.size(), -1);
  std::vector<float> llp_match_bydist_dist(llp_idx.size(), -1);
  std::vector<int> SDV_match_bydau(secondary_vertices->size(), -1);
  std::vector<int> SDV_match_bydau_ntk(secondary_vertices->size(), 0);
  std::vector<int> SDV_match_bydist(secondary_vertices->size(), -1);
  std::vector<float> SDV_match_bydist_dist(secondary_vertices->size(), -1);

  // Match LLP and reco vertices by daughter
  //
  std::map<int,std::pair<int,int>> vtxllpmatch = SoftDV::VtxLLPMatch( genParticles, secondary_vertices, tracks, primary_vertex->position(), debug);
  for (size_t ivtx=0; ivtx<secondary_vertices->size(); ++ivtx) {
    if (vtxllpmatch.find(ivtx) != vtxllpmatch.end()){
      int llp_matched_idx = vtxllpmatch[ivtx].first;
      int match_ntk = vtxllpmatch[ivtx].second;
      if (llp_matched_idx<0) continue;
      SDV_match_bydau[ivtx] = llp_matched_idx;
      SDV_match_bydau_ntk[ivtx] = match_ntk;
      math::XYZPoint llp_decay = math::XYZPoint(llp_decay_x[llp_matched_idx], llp_decay_y[llp_matched_idx], llp_decay_z[llp_matched_idx]);
      if (llp_match_bydau_ntk[llp_matched_idx] < match_ntk) {
        llp_match_bydau_ntk[llp_matched_idx] = match_ntk;
        llp_match_bydau[llp_matched_idx] = ivtx;
        const reco::Vertex& sv = secondary_vertices->at(ivtx);
        const auto d_gen = gen_dist(sv,llp_decay,true);
        llp_match_bydau_dist[llp_matched_idx] = fabs(d_gen.significance());
      }
    }
  }
  //

  // Match LLP and reco vertices by distance
  for (size_t illp=0; illp<llp_idx.size(); ++illp){
    math::XYZPoint llp_decay = math::XYZPoint(llp_decay_x[illp], llp_decay_y[illp], llp_decay_z[illp]);
    float d_gen_min = 999;
    int vtx_idx = -1;
    for (size_t ivtx=0; ivtx<secondary_vertices->size(); ++ivtx) {
      const reco::Vertex& vtx = secondary_vertices->at(ivtx);
      const auto d_gen = gen_dist(vtx,llp_decay,true);
      float d_gen_sig = fabs(d_gen.significance());
      if (d_gen_sig<d_gen_min){
        d_gen_min = d_gen_sig;
        vtx_idx = ivtx;
      }
    }
    if (vtx_idx!=-1){
      llp_match_bydist[illp] = vtx_idx;
      llp_match_bydist_dist[illp] = d_gen_min;
      SDV_match_bydist[vtx_idx] = illp;
      SDV_match_bydist_dist[vtx_idx] = d_gen_min;
    }
  }

  // Flat table for LLPs
  auto llpTable = std::make_unique<nanoaod::FlatTable>(llp_idx.size(), LLPName_, false);
  llpTable->addColumn<float>("pt", llp_pt, "pt", 10);
  llpTable->addColumn<float>("eta", llp_eta, "eta", 10);
  llpTable->addColumn<float>("phi", llp_phi, "phi", 10);
  llpTable->addColumn<float>("mass", llp_mass, "mass", 10);
  llpTable->addColumn<float>("ctau", llp_ctau, "ctau", 10);
  llpTable->addColumn<float>("decay_x", llp_decay_x, "x position of LLP decay in cm", 10);
  llpTable->addColumn<float>("decay_y", llp_decay_y, "y position of LLP decay in cm", 10);
  llpTable->addColumn<float>("decay_z", llp_decay_z, "z position of LLP decay in cm", 10);
  llpTable->addColumn<int16_t>("pdgId", llp_pdgId, "pdgID of LLP", 10);
  llpTable->addColumn<int16_t>("decaymode", llp_dm, "Decay mode of LLP: 0-undefined; 1-stop->bffChi0; 2-stop->cChi0; 3-N2->ZChi0->bbChi0; 4-N2->ZChi0->qqChi0; 5-N2->ZChi0->llChi0; 6-N2->HChi0->bbChi0; 7-N2->HChi0->qqChi0; 8-N2->HChi0->llChi0", 10);
  llpTable->addColumn<int16_t>("status", llp_status, "status of LLP", 10);
  llpTable->addColumn<int16_t>("statusFlags", llp_statusFlags, "gen status flags stored bitwise, bits are: 0 : isPrompt, 1 : isDecayedLeptonHadron, 2 : isTauDecayProduct, 3 : isPromptTauDecayProduct, 4 : isDirectTauDecayProduct, 5 : isDirectPromptTauDecayProduct, 6 : isDirectHadronDecayProduct, 7 : isHardProcess, 8 : fromHardProcess, 9 : isHardProcessTauDecayProduct, 10 : isDirectHardProcessTauDecayProduct, 11 : fromHardProcessBeforeFSR, 12 : isFirstCopy, 13 : isLastCopy, 14 : isLastCopyBeforeFSR, ", 10);
  llpTable->addColumn<int16_t>("ngentk", llp_ngentk, "Number of gen tracks", 10);
  llpTable->addColumn<int16_t>("nrecotk", llp_nrecotk, "Number of gen tracks that match with reco track", 10);
  llpTable->addColumn<int16_t>("matchedSDVIdx_bydau", llp_match_bydau, "SDV index matched with LLP by daughters", 10);
  llpTable->addColumn<int16_t>("matchedSDVnDau_bydau", llp_match_bydau_ntk, "The number of matched gen daughters of LLP", 10); 
  llpTable->addColumn<float>("matchedSDVDist_bydau", llp_match_bydau_dist, "The distance between daughter-matched SDV and LLP", 10);
  llpTable->addColumn<int16_t>("matchedSDVIdx_bydist", llp_match_bydist, "SDV index matched with LLP by daughters", 10);
  llpTable->addColumn<float>("matchedSDVDist_bydist", llp_match_bydist_dist, "The distance between distance-matched SDV and LLP", 10);

  auto genPartTable = std::make_unique<nanoaod::FlatTable>(genParticles->size(), "SDVGenPart", false, true);
  genPartTable->addColumn<int16_t>("LLPIdx",genpart_llpidx, "LLP index", 10);
  genPartTable->addColumn<int16_t>("pdgId",genpart_pdgId, "pdgId", 10);
  genPartTable->addColumn<int16_t>("isGentk",genpart_isgentk, "whether the gen particle is possibly measured as a reco track", 10);
  genPartTable->addColumn<int16_t>("recomatch",genpart_recomatch, "whether the gen particle is matched with a reco track", 10);
  genPartTable->addColumn<int16_t>("charge",genpart_charge, "charge", 10);
  genPartTable->addColumn<float>("recomatch_dr",genpart_recomatch_dr, "dR between the matched track and the gen particle", 10);
  genPartTable->addColumn<float>("dxy",genpart_dxy, "dxy between PV and the closest approach", 10);
  genPartTable->addColumn<float>("dz",genpart_dz, "dz between PV and the closest approach", 10);
  genPartTable->addColumn<float>("vertex_x",genpart_vertex_x, "x position of gen particle vertex", 10);
  genPartTable->addColumn<float>("vertex_y",genpart_vertex_y, "y position of gen particle vertex", 10);
  genPartTable->addColumn<float>("vertex_z",genpart_vertex_z, "z position of gen particle vertex", 10);

  auto genSecVtxTable = std::make_unique<nanoaod::FlatTable>(gensecvtx_x.size(), "GenSecVtx", false);
  genSecVtxTable->addColumn<int16_t>("LLPIdx",gensecvtx_llpidx, "LLP index", 10);
  genSecVtxTable->addColumn<float>("vertex_x",gensecvtx_x, "x position of gen secondary vertex", 10);
  genSecVtxTable->addColumn<float>("vertex_y",gensecvtx_y, "y position of gen secondary vertex", 10);
  genSecVtxTable->addColumn<float>("vertex_z",gensecvtx_z, "z position of gen secondary vertex", 10);

  auto tkTable = std::make_unique<nanoaod::FlatTable>(tracks->size(), "SDVTrack", false, true);
  tkTable->addColumn<int16_t>("GenPartIdx", tk_genpartidx, "GenParticle index", 10);
  tkTable->addColumn<int16_t>("LLPIdx", tk_llpidx, "LLP index", 10);
  tkTable->addColumn<int16_t>("GenSecVtxIdx", tk_gensecvtxidx, "GenSecVtx index", 10);

  auto vtxTable = std::make_unique<nanoaod::FlatTable>(secondary_vertices->size(), "SDVSecVtx", false, true);
  vtxTable->addColumn<int16_t>("matchedLLPIdx_bydau", SDV_match_bydau, "LLP index matched with SDV by daughters", 10);
  vtxTable->addColumn<int16_t>("matchedLLPnDau_bydau", SDV_match_bydau_ntk, "The number of matched gen daughters of LLP", 10);
  vtxTable->addColumn<int16_t>("matchedLLPIdx_bydist", SDV_match_bydist, "LLP index matched with SDV by distance", 10);
  vtxTable->addColumn<float>("matchedLLPDist_bydist", SDV_match_bydist_dist, "The distance between matched SDV and LLP", 10);

  iEvent.put(std::move(llpTable), "LLPs"); 
  iEvent.put(std::move(genPartTable), "GenPart");
  iEvent.put(std::move(genSecVtxTable), "GenSecVtx");
  iEvent.put(std::move(tkTable), "SDVTrack");
  iEvent.put(std::move(vtxTable), "SDVSecVtx");

}

// ------------ method called once each stream before processing any runs, lumis or events  ------------
void LLPTableProducer::beginStream(edm::StreamID) {}

// ------------ method called once each stream after processing all runs, lumis and events  ------------
void LLPTableProducer::endStream() {}

// ------------ method fills 'descriptions' with the allowed parameters for the module  ------------
void LLPTableProducer::fillDescriptions(edm::ConfigurationDescriptions& descriptions) {
  //The following says we do not know what parameters are allowed so do no validation
  // Please change this to state exactly what you do use, even if it is no parameters
  // edm::ParameterSetDescription desc;
  // desc.setUnknown();
  // descriptions.addDefault(desc);
  edm::ParameterSetDescription desc;

  desc.add<edm::InputTag>("src")->setComment("");
  desc.add<edm::InputTag>("pvToken")->setComment("");
  desc.add<edm::InputTag>("tkToken")->setComment("");
  desc.add<edm::InputTag>("svToken")->setComment("");
  desc.add<std::string>("LLPName")->setComment("");
  desc.add<std::string>("LLPDoc")->setComment("");
  //desc.add<std::vector<int>>("LLPid_")->setComment("");
  //desc.add<int>("LSPid_")->setComment("");
  desc.add<bool>("debug")->setComment("");

  descriptions.addWithDefaultLabel(desc);
}

DEFINE_FWK_MODULE(LLPTableProducer);
