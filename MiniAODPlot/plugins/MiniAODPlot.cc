// system include files
#include <memory>

// user include files
#include "TH1.h"
#include "TH2.h"

#include "FWCore/ServiceRegistry/interface/Service.h"
#include "CommonTools/UtilAlgos/interface/TFileService.h"

#include "FWCore/Framework/interface/Frameworkfwd.h"
#include "FWCore/Framework/interface/one/EDAnalyzer.h"

#include "FWCore/Framework/interface/Event.h"
#include "FWCore/Framework/interface/MakerMacros.h"

#include "FWCore/ParameterSet/interface/ParameterSet.h"
#include "FWCore/Utilities/interface/InputTag.h"

#include "DataFormats/VertexReco/interface/Vertex.h"
#include "DataFormats/VertexReco/interface/VertexFwd.h"
#include "DataFormats/PatCandidates/interface/MET.h"
#include "DataFormats/PatCandidates/interface/Muon.h"

using reco::TrackCollection;

class MiniAODPlot : public edm::one::EDAnalyzer<edm::one::SharedResources> {
public:
  explicit MiniAODPlot(const edm::ParameterSet&);
  ~MiniAODPlot() override;

private:
  void beginJob() override;
  void analyze(const edm::Event&, const edm::EventSetup&) override;

  const edm::EDGetTokenT<pat::METCollection> met_token;
  const edm::EDGetTokenT<pat::MuonCollection> muons_token;
  const edm::EDGetTokenT<reco::VertexCollection> vtx_token;

  TH1D* h_sv_r;
  TH2D* h_sv_xy;
};

MiniAODPlot::MiniAODPlot(const edm::ParameterSet& iConfig)
    : met_token(consumes<pat::METCollection>(iConfig.getUntrackedParameter<edm::InputTag>("met_token"))),
      muons_token(consumes<pat::MuonCollection>(iConfig.getUntrackedParameter<edm::InputTag>("muons_src"))),
      vtx_token(consumes<reco::VertexCollection>(iConfig.getUntrackedParameter<edm::InputTag>("vtx_token")))
{
}

MiniAODPlot::~MiniAODPlot() {
}


void MiniAODPlot::analyze(const edm::Event& iEvent, const edm::EventSetup& iSetup) {

    edm::Handle<pat::METCollection> met;
    iEvent.getByToken(met_token,met);

    edm::Handle<pat::MuonCollection> muons;
    iEvent.getByToken(muons_token, muons);

    int nMuons = 0;
    for (const auto& mu : *muons) {
        if (mu.passed(0)) {
            if ((mu.pt()>10) && (fabs(mu.eta())<2.4) ){
                nMuons += 1;
            }
        }
    }

    if (nMuons<1) return;

    edm::Handle<reco::VertexCollection> vertices;
    iEvent.getByToken(vtx_token,vertices);

    for (const auto& vtx : *vertices) {
        double sv_r = std::hypot(vtx.x(),vtx.y());
        if (sv_r>2) {
            h_sv_r->Fill(std::hypot(vtx.x(),vtx.y()));
            h_sv_xy->Fill(vtx.x(),vtx.y());
        }
    }
    return;
}

void MiniAODPlot::beginJob() {
    edm::Service<TFileService> fs;
    h_sv_r = fs->make<TH1D>("h_sv_r",";vertex r (cm);A.U.",500,0,50);
    h_sv_xy = fs->make<TH2D>("h_sv_xy",";vertex x (cm);vertex y (cm)",2000, -50, 50, 2000, -50, 50);
}

DEFINE_FWK_MODULE(MiniAODPlot);
