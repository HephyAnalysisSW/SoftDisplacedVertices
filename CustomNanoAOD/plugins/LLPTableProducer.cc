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
  std::vector<int> genpart_isgentk(genParticles->size(), 0);
  std::vector<int> genpart_recomatch(genParticles->size(), -1);
  std::vector<int> genpart_charge(genParticles->size(), 0);
  std::vector<float> genpart_recomatch_dr(genParticles->size(), -1);
  std::vector<float> genpart_dxy(genParticles->size(), -1);
  std::vector<float> genpart_dz(genParticles->size(), -1);
  std::vector<float> genpart_vertex_x(genParticles->size(), -1);
  std::vector<float> genpart_vertex_y(genParticles->size(), -1);
  std::vector<float> genpart_vertex_z(genParticles->size(), -1);
  std::vector<int> tk_genpartidx(tracks->size(), -1);
  std::vector<int> tk_llpidx(tracks->size(), -1);

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
  llpTable->addColumn<float>("pt", llp_pt, "pt", nanoaod::FlatTable::FloatColumn, 10);
  llpTable->addColumn<float>("eta", llp_eta, "eta", nanoaod::FlatTable::FloatColumn, 10);
  llpTable->addColumn<float>("phi", llp_phi, "phi", nanoaod::FlatTable::FloatColumn, 10);
  llpTable->addColumn<float>("mass", llp_mass, "mass", nanoaod::FlatTable::FloatColumn, 10);
  llpTable->addColumn<float>("ctau", llp_ctau, "ctau", nanoaod::FlatTable::FloatColumn, 10);
  llpTable->addColumn<float>("decay_x", llp_decay_x, "x position of LLP decay in cm", nanoaod::FlatTable::FloatColumn, 10);
  llpTable->addColumn<float>("decay_y", llp_decay_y, "y position of LLP decay in cm", nanoaod::FlatTable::FloatColumn, 10);
  llpTable->addColumn<float>("decay_z", llp_decay_z, "z position of LLP decay in cm", nanoaod::FlatTable::FloatColumn, 10);
  llpTable->addColumn<int>("pdgId", llp_pdgId, "pdgID of LLP", nanoaod::FlatTable::IntColumn);
  llpTable->addColumn<int>("decaymode", llp_dm, "Decay mode of LLP: 0-undefined; 1-stop->bffChi0; 2-stop->cChi0; 3-N2->ZChi0->bbChi0; 4-N2->ZChi0->qqChi0; 5-N2->ZChi0->llChi0; 6-N2->HChi0->bbChi0; 7-N2->HChi0->qqChi0; 8-N2->HChi0->llChi0", nanoaod::FlatTable::IntColumn);
  llpTable->addColumn<int>("status", llp_status, "status of LLP", nanoaod::FlatTable::IntColumn);
  llpTable->addColumn<int>("statusFlags", llp_statusFlags, "gen status flags stored bitwise, bits are: 0 : isPrompt, 1 : isDecayedLeptonHadron, 2 : isTauDecayProduct, 3 : isPromptTauDecayProduct, 4 : isDirectTauDecayProduct, 5 : isDirectPromptTauDecayProduct, 6 : isDirectHadronDecayProduct, 7 : isHardProcess, 8 : fromHardProcess, 9 : isHardProcessTauDecayProduct, 10 : isDirectHardProcessTauDecayProduct, 11 : fromHardProcessBeforeFSR, 12 : isFirstCopy, 13 : isLastCopy, 14 : isLastCopyBeforeFSR, ", nanoaod::FlatTable::IntColumn);
  llpTable->addColumn<int>("ngentk", llp_ngentk, "Number of gen tracks", nanoaod::FlatTable::IntColumn);
  llpTable->addColumn<int>("nrecotk", llp_nrecotk, "Number of gen tracks that match with reco track", nanoaod::FlatTable::IntColumn);
  llpTable->addColumn<int>("matchedSDVIdx_bydau", llp_match_bydau, "SDV index matched with LLP by daughters", nanoaod::FlatTable::IntColumn);
  llpTable->addColumn<int>("matchedSDVnDau_bydau", llp_match_bydau_ntk, "The number of matched gen daughters of LLP", nanoaod::FlatTable::IntColumn); 
  llpTable->addColumn<float>("matchedSDVDist_bydau", llp_match_bydau_dist, "The distance between daughter-matched SDV and LLP", nanoaod::FlatTable::FloatColumn, 10);
  llpTable->addColumn<int>("matchedSDVIdx_bydist", llp_match_bydist, "SDV index matched with LLP by daughters", nanoaod::FlatTable::IntColumn);
  llpTable->addColumn<float>("matchedSDVDist_bydist", llp_match_bydist_dist, "The distance between distance-matched SDV and LLP", nanoaod::FlatTable::FloatColumn, 10);


  auto genPartTable = std::make_unique<nanoaod::FlatTable>(genParticles->size(), "SDVGenPart", false, true);
  genPartTable->addColumn<int>("LLPIdx",genpart_llpidx, "LLP index", nanoaod::FlatTable::IntColumn);
  genPartTable->addColumn<int>("isGentk",genpart_isgentk, "whether the gen particle is possibly measured as a reco track", nanoaod::FlatTable::IntColumn);
  genPartTable->addColumn<int>("recomatch",genpart_recomatch, "whether the gen particle is matched with a reco track", nanoaod::FlatTable::IntColumn);
  genPartTable->addColumn<int>("charge",genpart_charge, "charge", nanoaod::FlatTable::IntColumn);
  genPartTable->addColumn<float>("recomatch_dr",genpart_recomatch_dr, "dR between the matched track and the gen particle", nanoaod::FlatTable::FloatColumn, 10);
  genPartTable->addColumn<float>("dxy",genpart_dxy, "dxy between PV and the closest approach", nanoaod::FlatTable::FloatColumn, 10);
  genPartTable->addColumn<float>("dz",genpart_dz, "dz between PV and the closest approach", nanoaod::FlatTable::FloatColumn, 10);
  genPartTable->addColumn<float>("vertex_x",genpart_vertex_x, "x position of gen particle vertex", nanoaod::FlatTable::FloatColumn, 10);
  genPartTable->addColumn<float>("vertex_y",genpart_vertex_y, "y position of gen particle vertex", nanoaod::FlatTable::FloatColumn, 10);
  genPartTable->addColumn<float>("vertex_z",genpart_vertex_z, "z position of gen particle vertex", nanoaod::FlatTable::FloatColumn, 10);

  auto tkTable = std::make_unique<nanoaod::FlatTable>(tracks->size(), "SDVTrack", false, true);
  tkTable->addColumn<int>("GenPartIdx", tk_genpartidx, "GenParticle index", nanoaod::FlatTable::IntColumn);
  tkTable->addColumn<int>("LLPIdx", tk_llpidx, "LLP index", nanoaod::FlatTable::IntColumn);

  auto vtxTable = std::make_unique<nanoaod::FlatTable>(secondary_vertices->size(), "SDVSecVtx", false, true);
  vtxTable->addColumn<int>("matchedLLPIdx_bydau", SDV_match_bydau, "LLP index matched with SDV by daughters", nanoaod::FlatTable::IntColumn);
  vtxTable->addColumn<int>("matchedLLPnDau_bydau", SDV_match_bydau_ntk, "The number of matched gen daughters of LLP", nanoaod::FlatTable::IntColumn);
  vtxTable->addColumn<int>("matchedLLPIdx_bydist", SDV_match_bydist, "LLP index matched with SDV by distance", nanoaod::FlatTable::IntColumn);
  vtxTable->addColumn<float>("matchedLLPDist_bydist", SDV_match_bydist_dist, "The distance between matched SDV and LLP", nanoaod::FlatTable::FloatColumn, 10);

  iEvent.put(std::move(llpTable), "LLPs"); 
  iEvent.put(std::move(genPartTable), "GenPart");
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
  edm::ParameterSetDescription desc;
  desc.setUnknown();
  descriptions.addDefault(desc);
}

DEFINE_FWK_MODULE(LLPTableProducer);
