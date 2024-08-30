#include "DataFormats/PatCandidates/interface/PackedCandidate.h"
#include "DataFormats/TrackReco/interface/Track.h"
#include "DataFormats/TrackReco/interface/TrackFwd.h"
#include "FWCore/Framework/interface/one/EDProducer.h"
#include "FWCore/Framework/interface/Event.h"
#include "FWCore/Framework/interface/Frameworkfwd.h"
#include "FWCore/Framework/interface/MakerMacros.h"


class TracksMiniAOD : public edm::one::EDProducer<edm::one::SharedResources> {
  public:
    explicit TracksMiniAOD(const edm::ParameterSet&);
    virtual void produce(edm::Event&, const edm::EventSetup&);
  private:
    const edm::EDGetTokenT<pat::PackedCandidateCollection> packed_candidates_token;
};

TracksMiniAOD::TracksMiniAOD(const edm::ParameterSet& cfg)
  : packed_candidates_token(consumes<pat::PackedCandidateCollection>(cfg.getParameter<edm::InputTag>("packed_candidates")))
{
  // usesResource();
  produces<reco::TrackCollection>();
}

void TracksMiniAOD::produce(edm::Event& event, const edm::EventSetup& setup) {
  edm::Handle<pat::PackedCandidateCollection> packed_candidates;
  event.getByToken(packed_candidates_token, packed_candidates);

  auto tracks = std::make_unique<reco::TrackCollection>();

  for (size_t i=0; i<packed_candidates->size(); ++i){
    const pat::PackedCandidate& cand = packed_candidates->at(i);

    if (cand.charge() && cand.hasTrackDetails()) {
      const reco::Track& tk = cand.pseudoTrack();
      tracks->push_back(tk);
    }
  }

  event.put(std::move(tracks));
}

DEFINE_FWK_MODULE(TracksMiniAOD);
