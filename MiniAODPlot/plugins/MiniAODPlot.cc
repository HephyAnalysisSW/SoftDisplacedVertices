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

  TH1D* h_sv_r_all;
  TH2D* h_sv_xy_all;
  TH2D* h_sv_rz_all;
  TH1D* h_sv_r_barrel;
  TH2D* h_sv_xy_barrel;
  TH2D* h_sv_rz_barrel;
  TH1D* h_sv_r_endcap;
  TH2D* h_sv_xy_endcap;
  TH2D* h_sv_rz_endcap;
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
        double sv_x = vtx.x();
        double sv_y = vtx.y();
        double sv_z = vtx.z();
        double sv_r = std::hypot(sv_x,sv_y);
        if (sv_r>2) {
            h_sv_r_all->Fill(sv_r);
            h_sv_xy_all->Fill(sv_x,sv_y);
            h_sv_rz_all->Fill(sv_z,sv_r);
        }
        if (fabs(sv_z)<30) {
            h_sv_r_barrel->Fill(sv_r);
            h_sv_xy_barrel->Fill(sv_x,sv_y);
            h_sv_rz_barrel->Fill(sv_z,sv_r);
        }
        else {
            h_sv_r_endcap->Fill(sv_r);
            h_sv_xy_endcap->Fill(sv_x,sv_y);
            h_sv_rz_endcap->Fill(sv_z,sv_r);
        
        }
    }
    return;
}

void MiniAODPlot::beginJob() {
    edm::Service<TFileService> fs;
    h_sv_r_all = fs->make<TH1D>("h_sv_r_all",";all vertex r (cm);A.U.",500,0,50);
    h_sv_xy_all = fs->make<TH2D>("h_sv_xy_all",";all vertex x (cm);all vertex y (cm)",2000, -50, 50, 2000, -50, 50);
    h_sv_rz_all = fs->make<TH2D>("h_sv_rz_all",";all vertex z (cm);all vertex r (cm)",2400, -300, 300, 1000, 0, 50);
    h_sv_r_barrel = fs->make<TH1D>("h_sv_r_barrel",";barrel vertex r (cm);A.U.",500,0,50);
    h_sv_xy_barrel = fs->make<TH2D>("h_sv_xy_barrel",";barrel vertex x (cm);barrel vertex y (cm)",2000, -50, 50, 2000, -50, 50);
    h_sv_rz_barrel = fs->make<TH2D>("h_sv_rz_barrel",";barrel vertex z (cm);barrel vertex r (cm)",2400, -300, 300, 1000, 0, 50);
    h_sv_r_endcap = fs->make<TH1D>("h_sv_r_endcap",";endcap vertex r (cm);A.U.",500,0,50);
    h_sv_xy_endcap = fs->make<TH2D>("h_sv_xy_endcap",";endcap vertex x (cm);endcap vertex y (cm)",2000, -50, 50, 2000, -50, 50);
    h_sv_rz_endcap = fs->make<TH2D>("h_sv_rz_endcap",";endcap vertex z (cm);endcap vertex r (cm)",2400, -300, 300, 1000, 0, 50);
}

DEFINE_FWK_MODULE(MiniAODPlot);
