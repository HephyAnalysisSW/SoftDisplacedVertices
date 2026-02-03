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

class DisplayProducer : public edm::stream::EDProducer<> {
  public:
    explicit DisplayProducer(const edm::ParameterSet&);
    ~DisplayProducer() override;

    static void fillDescriptions(edm::ConfigurationDescriptions& descriptions);

  private:
    void beginStream(edm::StreamID) override;
    void produce(edm::Event&, const edm::EventSetup&) override;
    void endStream() override;

    const edm::EDGetTokenT<std::vector<reco::GenParticle>> genToken_;
    const edm::EDGetTokenT<reco::VertexCollection> pvToken_;
    const edm::EDGetTokenT<reco::TrackCollection> tkToken_;
    const edm::EDGetTokenT<reco::VertexCollection> svIVFToken_;
    const edm::EDGetTokenT<reco::VertexCollection> svMFVToken_;
    bool debug;
};

DisplayProducer::DisplayProducer(const edm::ParameterSet& params)
  : genToken_(consumes<std::vector<reco::GenParticle>>(params.getParameter<edm::InputTag>("src"))),
    pvToken_(consumes<reco::VertexCollection>(params.getParameter<edm::InputTag>("pvToken"))),
    tkToken_(consumes<reco::TrackCollection>(params.getParameter<edm::InputTag>("tkToken"))),
    svIVFToken_(consumes<reco::VertexCollection>(params.getParameter<edm::InputTag>("svIVFToken"))),
    svMFVToken_(consumes<reco::VertexCollection>(params.getParameter<edm::InputTag>("svMFVToken"))),
    debug(params.getParameter<bool>("debug"))
{
  produces<reco::GenParticleCollection>("LLPdecays");
  produces<reco::TrackCollection>("LLPmatched");
  produces<reco::VertexCollection>("LLPmatchedIVF");
  produces<reco::VertexCollection>("LLPmatchedMFV");
}

DisplayProducer::~DisplayProducer() {}

void DisplayProducer::produce(edm::Event& iEvent, const edm::EventSetup& iSetup) {

  std::unique_ptr<reco::GenParticleCollection> genpart_llpdecay(new reco::GenParticleCollection);
  std::unique_ptr<reco::TrackCollection> tk_llpmatched(new reco::TrackCollection);
  std::unique_ptr<reco::VertexCollection> vtx_llpmatched_IVF(new reco::VertexCollection);
  std::unique_ptr<reco::VertexCollection> vtx_llpmatched_MFV(new reco::VertexCollection);

  edm::Handle<reco::GenParticleCollection> genParticles;
  iEvent.getByToken(genToken_, genParticles);

  edm::Handle<reco::VertexCollection> primary_vertices;
  iEvent.getByToken(pvToken_, primary_vertices);
  const reco::Vertex* primary_vertex = 0;
  if (primary_vertices->size())
    primary_vertex = &primary_vertices->at(0);

  edm::Handle<reco::TrackCollection> tracks;
  iEvent.getByToken(tkToken_, tracks);

  edm::Handle<reco::VertexCollection> secondary_vertices_IVF;
  iEvent.getByToken(svIVFToken_, secondary_vertices_IVF);

  edm::Handle<reco::VertexCollection> secondary_vertices_MFV;
  iEvent.getByToken(svMFVToken_, secondary_vertices_MFV);

  std::vector<int> llp_idx = SoftDV::FindLLP(genParticles, debug).first;
  std::vector<float> llp_pt, llp_eta, llp_phi, llp_mass, llp_ctau, llp_decay_x, llp_decay_y, llp_decay_z;
  std::vector<int> llp_pdgId, llp_status, llp_statusFlags, llp_ngentk, llp_nrecotk;

  std::vector<int> tk_llpidx(tracks->size(), -1);

  for (size_t illp=0; illp<llp_idx.size(); ++illp){
    const reco::GenParticle& llp = genParticles->at(llp_idx[illp]);
    genpart_llpdecay->push_back(llp);

    // Now determine the LLP decay point
    if (llp.numberOfDaughters()==0){
      throw cms::Exception("DisplayProducer") << "LLP has no Daughters!";
    }
    if (debug)
    {
      for (size_t idau=0; idau<llp.numberOfDaughters(); ++idau){
        std::cout << "LLP daughter " << idau << " ID " << llp.daughter(idau)->pdgId() << std::endl;
        std::cout << llp.daughter(idau)->vertex().x() << std::endl;
      }
    }
    auto decay_point = llp.daughter(0)->vertex();

    math::XYZVector flight = math::XYZVector(decay_point) - math::XYZVector(primary_vertex->position());
    auto polarp4 = llp.polarP4();
    float ctau = std::sqrt(flight.Mag2())/polarp4.Beta()/polarp4.Gamma();

    // Get the LLP decay products
    std::vector<int> llp_daus = SoftDV::GetDaughters(llp_idx[illp], genParticles, debug);
    int ngentk = 0;
    int nmatchedtk = 0;

    for (int igen:llp_daus){
      const reco::GenParticle& idau = genParticles->at(igen);
      if (SoftDV::pass_gentk(idau, primary_vertex->position())){
        genpart_llpdecay->push_back(idau);
      }
      const auto matchres = SoftDV::matchtracks(idau, tracks, primary_vertex->position());
      if (matchres.first!=-1) {
        tk_llpidx[matchres.first] = illp;
        const reco::Track& itk = tracks->at(matchres.first);
        tk_llpmatched->push_back(itk);
      }
    }
  }

  // Match LLP with reco vertices

  // Match LLP and reco vertices (IVF) by daughter
  for (size_t ivtx=0; ivtx<secondary_vertices_IVF->size(); ++ivtx) {
    std::vector<int> match_bydau_ntk(llp_idx.size(), 0);
    const reco::Vertex& sv = secondary_vertices_IVF->at(ivtx);
    //FIXME: there should be a more elegent way to refer the track in vertex in the reco track collection using TrackRef :) 
    for (auto v_tk = sv.tracks_begin(), vtke = sv.tracks_end(); v_tk != vtke; ++v_tk){
      for (size_t itk=0; itk<tracks->size(); ++itk) {
        const reco::Track& tk = tracks->at(itk);
        if (&tk == &(**v_tk)) {
            const int llp_matched_idx = tk_llpidx[itk];
            if (llp_matched_idx!=-1){
                vtx_llpmatched_IVF->push_back(sv);
            }
            break;
        }
      }
    }
  }

  // Match LLP and reco vertices (MFV) by daughter
  for (size_t ivtx=0; ivtx<secondary_vertices_MFV->size(); ++ivtx) {
    std::vector<int> match_bydau_ntk(llp_idx.size(), 0);
    const reco::Vertex& sv = secondary_vertices_MFV->at(ivtx);
    //FIXME: there should be a more elegent way to refer the track in vertex in the reco track collection using TrackRef :) 
    for (auto v_tk = sv.tracks_begin(), vtke = sv.tracks_end(); v_tk != vtke; ++v_tk){
      for (size_t itk=0; itk<tracks->size(); ++itk) {
        const reco::Track& tk = tracks->at(itk);
        if (&tk == &(**v_tk)) {
            const int llp_matched_idx = tk_llpidx[itk];
            if (llp_matched_idx!=-1){
                vtx_llpmatched_MFV->push_back(sv);
            }
            break;
        }
      }
    }
  }

  iEvent.put(std::move(genpart_llpdecay), "LLPdecays"); 
  iEvent.put(std::move(tk_llpmatched), "LLPmatched");
  iEvent.put(std::move(vtx_llpmatched_IVF), "LLPmatchedIVF");
  iEvent.put(std::move(vtx_llpmatched_MFV), "LLPmatchedMFV");

}

// ------------ method called once each stream before processing any runs, lumis or events  ------------
void DisplayProducer::beginStream(edm::StreamID) {}

// ------------ method called once each stream after processing all runs, lumis and events  ------------
void DisplayProducer::endStream() {}

// ------------ method fills 'descriptions' with the allowed parameters for the module  ------------
void DisplayProducer::fillDescriptions(edm::ConfigurationDescriptions& descriptions) {
  //The following says we do not know what parameters are allowed so do no validation
  // Please change this to state exactly what you do use, even if it is no parameters
  edm::ParameterSetDescription desc;
  desc.setUnknown();
  descriptions.addDefault(desc);
}

DEFINE_FWK_MODULE(DisplayProducer);
