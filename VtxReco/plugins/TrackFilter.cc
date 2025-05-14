#include <iomanip>

#include "CommonTools/UtilAlgos/interface/TFileService.h"
#include "DataFormats/TrackReco/interface/Track.h"
#include "DataFormats/TrackReco/interface/TrackFwd.h"
#include "FWCore/Framework/interface/stream/EDFilter.h"
#include "FWCore/Framework/interface/Event.h"
#include "FWCore/Framework/interface/MakerMacros.h"
#include "FWCore/ParameterSet/interface/ParameterSet.h"
#include "FWCore/Utilities/interface/InputTag.h"
#include "FWCore/ServiceRegistry/interface/Service.h"

// ISOLATION RELATED INCLUDES
// ----------------------------------------------------------------

#include <string>

#include "FWCore/Framework/interface/stream/EDProducer.h"
#include "FWCore/Framework/interface/ESHandle.h"
#include "FWCore/Framework/interface/Event.h"
#include "FWCore/Framework/interface/EventSetup.h"
#include "FWCore/Framework/interface/Frameworkfwd.h"
#include "FWCore/ParameterSet/interface/ParameterSet.h"
#include "FWCore/Utilities/interface/Exception.h"

#include "DataFormats/ParticleFlowCandidate/interface/PFCandidate.h"

#include "DataFormats/PatCandidates/interface/PackedCandidate.h"
#include "DataFormats/PatCandidates/interface/IsolatedTrack.h"
#include "DataFormats/PatCandidates/interface/PFIsolation.h"
#include "DataFormats/Candidate/interface/CandidateFwd.h"
#include "DataFormats/Common/interface/View.h"
#include "DataFormats/Common/interface/RefToPtr.h"
#include "DataFormats/Math/interface/deltaR.h"
#include "DataFormats/JetReco/interface/CaloJet.h"
#include "DataFormats/TrackReco/interface/Track.h"
#include "DataFormats/TrackReco/interface/TrackExtraFwd.h"
#include "DataFormats/TrackReco/interface/DeDxData.h"
#include "DataFormats/TrackReco/interface/DeDxHitInfo.h"
#include "DataFormats/VertexReco/interface/Vertex.h"
#include "DataFormats/VertexReco/interface/VertexFwd.h"
#include "RecoTracker/DeDx/interface/DeDxTools.h"
#include "CommonTools/Utils/interface/StringCutObjectSelector.h"

#include "TrackingTools/TrackAssociator/interface/TrackDetectorAssociator.h"
#include "TrackingTools/TrackAssociator/interface/TrackAssociatorParameters.h"
#include "TrackingTools/TrajectoryState/interface/TrajectoryStateTransform.h"

#include "CondFormats/HcalObjects/interface/HcalChannelQuality.h"
#include "CondFormats/HcalObjects/interface/HcalChannelStatus.h"
#include "CondFormats/EcalObjects/interface/EcalChannelStatus.h"
#include "CondFormats/DataRecord/interface/HcalChannelQualityRcd.h"
#include "CondFormats/DataRecord/interface/EcalChannelStatusRcd.h"

#include "MagneticField/Engine/interface/MagneticField.h"

#include "SoftDisplacedVertices/SoftDVDataFormats/interface/PFIsolation.h"
// -------------------------------------------------------------------------------




class TrackFilter : public edm::stream::EDFilter<> {
public:
  TrackFilter(const edm::ParameterSet&);
  virtual bool filter(edm::Event&, const edm::EventSetup&);

  typedef pat::IsolatedTrack::PolarLorentzVector PolarLorentzVector;
  typedef pat::IsolatedTrack::LorentzVector LorentzVector;
  // compute iso/miniiso
  void getIsolation(const PolarLorentzVector& p4, const pat::PackedCandidateCollection* pc, int pc_idx,
                    pat::PFIsolation &iso, pat::PFIsolation &miniiso) const;
private:
  const edm::EDGetTokenT<reco::BeamSpot>                    beamspot_token;
  const edm::EDGetTokenT<std::vector<reco::Vertex>>         vtxToken_;  // primaryVertices
  const edm::EDGetTokenT<pat::PackedCandidateCollection>    pc_;        // packedPFCandidates
  const edm::EDGetTokenT<pat::PackedCandidateCollection>    lt_;        // lostTracks
  const edm::EDGetTokenT<reco::TrackCollection>             gt_;        // generalTracks
  const edm::EDGetTokenT<edm::Association<pat::PackedCandidateCollection>>  gt2pc_;
  const edm::EDGetTokenT<edm::Association<pat::PackedCandidateCollection>>  gt2lt_;
  const edm::EDGetTokenT<edm::Association<reco::PFCandidateCollection>>     pc2pf_;

  std::vector<double> miniIsoParams_;
  const float pfIsolation_DR_;  // isolation radius
  const float pfIsolation_DZ_;  // used in determining if pfcand is from PV or PU

  const int min_track_nhits;
  const int min_n_seed_tracks;
  const double min_track_pt;
  const double min_track_dxy;
  const double min_track_nsigmadxy;
  const double max_track_normchi2;
  const double max_track_dz;
  const double max_track_sigmapt_ratio;
  const bool histos;


  static const int N_TRACK_TYPES = 2;
  static const int N_TRACK_VARS = 13;
  TH1D* h_n_track[N_TRACK_TYPES];
  TH1D* h_track_vars[N_TRACK_TYPES][N_TRACK_VARS];
  TH1D* h_track_pt[N_TRACK_TYPES];
  TH1D* h_track_dxy[N_TRACK_TYPES];
  TH1D* h_track_dxyerr[N_TRACK_TYPES];
  TH1D* h_track_nsigmadxy[N_TRACK_TYPES];
  TH1D* h_track_nhits[N_TRACK_TYPES];
  TH1D* h_track_normchi2[N_TRACK_TYPES];
  TH1D* h_track_dz[N_TRACK_TYPES];
  TH1D* h_track_sigmapt_ratio[N_TRACK_TYPES];
};

TrackFilter::TrackFilter(const edm::ParameterSet& cfg)
  : beamspot_token(consumes<reco::BeamSpot>(cfg.getParameter<edm::InputTag>("beamspot"))),
    vtxToken_(consumes<reco::VertexCollection>(cfg.getParameter<edm::InputTag>("primaryVertices"))),
    pc_(consumes<pat::PackedCandidateCollection>(cfg.getParameter<edm::InputTag>("packedPFCandidates"))),
    lt_(consumes<pat::PackedCandidateCollection>(cfg.getParameter<edm::InputTag>("lostTracks"))),
    gt_(consumes<reco::TrackCollection>(cfg.getParameter<edm::InputTag>("generalTracks"))),
    gt2pc_(consumes<edm::Association<pat::PackedCandidateCollection> >(cfg.getParameter<edm::InputTag>("packedPFCandidates"))),
    gt2lt_(consumes<edm::Association<pat::PackedCandidateCollection> >(cfg.getParameter<edm::InputTag>("lostTracks"))),
    pc2pf_(consumes<edm::Association<reco::PFCandidateCollection> >(cfg.getParameter<edm::InputTag>("packedPFCandidates"))),
    pfIsolation_DR_ (cfg.getParameter<double>("pfIsolation_DR")),
    pfIsolation_DZ_ (cfg.getParameter<double>("pfIsolation_DZ")),

    min_track_nhits(cfg.getParameter<int>("min_track_nhits")),
    min_n_seed_tracks(cfg.getParameter<int>("min_n_seed_tracks")),
    min_track_pt(cfg.getParameter<double>("min_track_pt")),
    min_track_dxy(cfg.getParameter<double>("min_track_dxy")),
    min_track_nsigmadxy(cfg.getParameter<double>("min_track_nsigmadxy")),
    max_track_normchi2(cfg.getParameter<double>("max_track_normchi2")),
    max_track_dz(cfg.getParameter<double>("max_track_dz")),
    max_track_sigmapt_ratio(cfg.getParameter<double>("max_track_sigmapt_ratio")),
    histos(cfg.getParameter<bool>("histos"))
{
  miniIsoParams_ = cfg.getParameter<std::vector<double> >("miniIsoParams");
  if(miniIsoParams_.size() != 3) throw cms::Exception("ParameterError") << "miniIsoParams must have exactly 3 elements.\n";


  produces<std::vector<reco::TrackRef>>("all");
  produces<std::vector<reco::TrackRef>>("seed");
  produces<reco::TrackCollection>("seed");
  produces<std::vector<SoftDV::PFIsolation>>("isolationDR03");

  if (histos){
    edm::Service<TFileService> fs;
    const char* track_desc[N_TRACK_TYPES] = {"all", "seed"};
    const char* var_names[N_TRACK_VARS] = {"pt", "eta", "phi", "dxy", "dxyerr", "ddxy", "ddxyerr", "nsigmadxy", "nhits", "normchi2", "dz", "pterr", "pterr_ratio"};
    const int var_nbins[N_TRACK_VARS] = {250,   50,    50,  500, 500,  500, 500, 100, 20, 20,  80,   50,  50};
    const double var_lo[N_TRACK_VARS] = {  0, -2.5, -3.15, -0.2,   0, -0.2,   0,   0,  0,  0, -20,    0,   0};
    const double var_hi[N_TRACK_VARS] = { 50,  2.5,  3.15,  0.2, 0.2,  0.2, 0.2,  10, 20, 10,  20, 0.15, 0.1};
    for (int i=0; i<N_TRACK_TYPES; ++i){
      h_n_track[i] = fs->make<TH1D>(TString::Format("h_n_%s_track", track_desc[i]),TString::Format(";number of %s tracks;A.U.", track_desc[i]),200,0,200);
      for (int ii=0; ii<N_TRACK_VARS; ++ii){
        h_track_vars[i][ii] = fs->make<TH1D>(TString::Format("h_%s_track_%s",track_desc[i],var_names[ii]), TString::Format(";%s;",var_names[ii]),var_nbins[ii],var_lo[ii],var_hi[ii]);
      }
    }
  }
}

bool TrackFilter::filter(edm::Event& event, const edm::EventSetup& setup) {

  std::unique_ptr<std::vector<reco::TrackRef>> all_tracks (new std::vector<reco::TrackRef>);
  std::unique_ptr<std::vector<reco::TrackRef>> seed_tracks(new std::vector<reco::TrackRef>);
  std::unique_ptr<reco::TrackCollection> seed_tracks_copy(new reco::TrackCollection);
  std::unique_ptr<std::vector<SoftDV::PFIsolation>> track_isolationDR03(new std::vector<SoftDV::PFIsolation>);

  // BeamSpot
  edm::Handle<reco::BeamSpot> beamspot;
  event.getByToken(beamspot_token, beamspot);

  // Primary Vertex
  edm::Handle<reco::VertexCollection> recoVertices;
  event.getByToken(vtxToken_, recoVertices);
  auto pvx = recoVertices->begin();

  // packedPFCandidate collection
  edm::Handle<pat::PackedCandidateCollection> pc_h;
  event.getByToken( pc_, pc_h );
  const pat::PackedCandidateCollection *pc = pc_h.product();

  // lostTracks collection
  edm::Handle<pat::PackedCandidateCollection> lt_h;
  event.getByToken( lt_, lt_h );

  // generalTracks collection
  edm::Handle<reco::TrackCollection> gt_h;
  event.getByToken( gt_, gt_h );

  // generalTracks-->packedPFCandidate association
  edm::Handle<edm::Association<pat::PackedCandidateCollection> > gt2pc;
  event.getByToken(gt2pc_, gt2pc);

  // generalTracks-->lostTracks association
  edm::Handle<edm::Association<pat::PackedCandidateCollection> > gt2lt;
  event.getByToken(gt2lt_, gt2lt);

  // packedPFCandidates-->particleFlow(reco::PFCandidate) association
  edm::Handle<edm::Association<reco::PFCandidateCollection> > pc2pf;
  event.getByToken(pc2pf_, pc2pf);



  for (size_t i=0; i<gt_h->size(); ++i){
    const reco::Track &gentk = (*gt_h)[i];
    reco::TrackRef tkref(gt_h, i);
    pat::PackedCandidateRef pcref = (*gt2pc)[tkref];
    pat::PackedCandidateRef ltref = (*gt2lt)[tkref];
    const pat::PackedCandidate & pfCand = *(pcref.get());
    const pat::PackedCandidate & lostTrack = *(ltref.get());

    // Determine if this general track is associated with anything in packedPFCandidates or lostTracks
    // Sometimes, a track gets associated w/ a neutral pfCand.
    // In this case, ignore the pfCand and take from lostTracks.
    bool isInPackedCands = (pcref.isNonnull() && pcref.id()==pc_h.id() && pfCand.charge()!=0);
    bool isInLostTracks  = (ltref.isNonnull() && ltref.id()==lt_h.id());

    PolarLorentzVector polarP4;
    LorentzVector p4;
    pat::PackedCandidateRef refToCand;
    int charge;
    // float dz, dxy, dzError, dxyError;
    int pfCandInd; //to avoid counting packedPFCands in their own isolation

    // get the four-momentum and charge
    if(isInPackedCands){
        p4        = pfCand.p4();
        polarP4   = pfCand.polarP4();
        charge    = pfCand.charge();
        pfCandInd = pcref.key();
    }else if(isInLostTracks){
        p4        = lostTrack.p4();
        polarP4   = lostTrack.polarP4();
        charge    = lostTrack.charge();
        pfCandInd = -1;
    }else{
        double m = 0.13957018; //assume pion mass
        double E = sqrt(m*m + gentk.p()*gentk.p());
        p4.SetPxPyPzE(gentk.px(), gentk.py(), gentk.pz(), E);
        polarP4.SetCoordinates(gentk.pt(), gentk.eta(), gentk.phi(), m);
        charge = gentk.charge();
        pfCandInd = -1;
    }

    if(charge == 0)
      continue;

    // get the isolation of the track
    pat::PFIsolation isolationDR03;
    pat::PFIsolation miniIso;
    getIsolation(polarP4, pc, pfCandInd, isolationDR03, miniIso);


    all_tracks->push_back(tkref);
    const double pt = tkref->pt();
    const double dxy = tkref->dxy(pvx->position());
    const double dxybs = tkref->dxy(*beamspot);
    const double dxyerr = tkref->dxyError(pvx->position(), pvx->covariance());
    const double dxyerrbs = tkref->dxyError();
    const double nsigmadxy = dxy / dxyerr;
    const double nhits = tkref->hitPattern().numberOfValidHits();
    const double normchi2 = tkref->normalizedChi2();
    const double dz = tkref->dz(pvx->position());
    const double sigmapt = tkref->ptError();
    const double sigmapt_ratio = sigmapt / pt;
    // std::cout.precision(15);
    // if ((pt > 0.9884) && (pt < 0.9886)){
    //   std::cout << "--------------------------------------------------------------------------------" << std::endl;
    //   std::cout << std::scientific << std::setw(30) << "PV"                          << std::setw(30) << "BS"                    << std::endl;
    //   std::cout << std::scientific << std::setw(30) << tkref->dxy(pvx->position()) << std::setw(30) << tkref->dxy(*beamspot) << std::endl;
    //   std::cout << std::scientific << std::setw(30) << tkref->dxyError(pvx->position(), pvx->covariance()) << std::setw(30) << tkref->dxyError() << std::endl;
    //   std::cout << std::scientific << std::setw(30) << tkref->dz(pvx->position()) << std::setw(30) << tkref->dz((*beamspot).position()) << std::endl;
    //   std::cout << std::scientific << "pt " << pt << " " << min_track_pt << std::endl;
    //   std::cout << std::scientific << "fabs(dxy) " << fabs(dxy) << " " << min_track_dxy << std::endl;
    //   std::cout << std::scientific << "fabs(nsigmadxy) " << fabs(nsigmadxy) << " " << min_track_nsigmadxy << std::endl;
    //   std::cout << std::scientific << "nhits " << nhits << " " << min_track_nhits << std::endl;
    //   std::cout << std::scientific << "normchi2 " << normchi2 << " " << max_track_normchi2 << std::endl;
    //   std::cout << std::scientific << "fabs(dz) " << fabs(dz) << " " << max_track_dz << std::endl;
    //   std::cout << std::scientific << "sigmapt_ratio " << sigmapt_ratio << " " << max_track_sigmapt_ratio << std::endl;
    //   std::cout << "--------------------------------------------------------------------------------" << std::endl;
      
  // }

    bool use_track =
      pt > min_track_pt &&
      fabs(dxy) > min_track_dxy &&
      fabs(nsigmadxy) > min_track_nsigmadxy &&
      nhits >= min_track_nhits &&
      normchi2 < max_track_normchi2 && 
      fabs(dz) < max_track_dz &&
      sigmapt_ratio < max_track_sigmapt_ratio;

    if (histos) {
      const double vars[N_TRACK_VARS] = {pt, tkref->eta(), tkref->phi(), dxy, dxyerr, dxy - dxybs, dxyerr-dxyerrbs, nsigmadxy, nhits, normchi2, dz, sigmapt, sigmapt_ratio};
      for (int ivar=0; ivar<N_TRACK_VARS; ++ivar){
        h_track_vars[0][ivar]->Fill(vars[ivar]);
      }
    }

    if (use_track) {
      // std::cout<< "PASS" << std::endl;
      // std::cout << "--------------------------------------------------------------------------------" << std::endl;
      // std::cout << std::scientific << std::setw(30) << "PV"                          << std::setw(30) << "BS"                    << std::endl;
      // std::cout << std::scientific << std::setw(30) << tkref->dxy(pvx->position()) << std::setw(30) << tkref->dxy(*beamspot) << std::endl;
      // std::cout << std::scientific << std::setw(30) << tkref->dxyError(pvx->position(), pvx->covariance()) << std::setw(30) << tkref->dxyError() << std::endl;
      // std::cout << std::scientific << std::setw(30) << tkref->dz(pvx->position()) << std::setw(30) << tkref->dz((*beamspot).position()) << std::endl;
      // std::cout << std::scientific << "pt " << pt << " " << min_track_pt << std::endl;
      // std::cout << std::scientific << "fabs(dxy) " << fabs(dxy) << " " << min_track_dxy << std::endl;
      // std::cout << std::scientific << "fabs(nsigmadxy) " << fabs(nsigmadxy) << " " << min_track_nsigmadxy << std::endl;
      // std::cout << std::scientific << "nhits " << nhits << " " << min_track_nhits << std::endl;
      // std::cout << std::scientific << "normchi2 " << normchi2 << " " << max_track_normchi2 << std::endl;
      // std::cout << std::scientific << "fabs(dz) " << fabs(dz) << " " << max_track_dz << std::endl;
      // std::cout << std::scientific << "sigmapt_ratio " << sigmapt_ratio << " " << max_track_sigmapt_ratio << std::endl;
      // std::cout << "--------------------------------------------------------------------------------" << std::endl;
      seed_tracks->push_back(tkref);
      seed_tracks_copy->push_back(*tkref);
      track_isolationDR03->push_back(SoftDV::PFIsolation(isolationDR03));
      if (histos) {
        const double vars[N_TRACK_VARS] = {pt, tkref->eta(), tkref->phi(), dxy, dxyerr, nsigmadxy, nhits, normchi2, dz, sigmapt, sigmapt_ratio};
        for (int ivar=0; ivar<N_TRACK_VARS; ++ivar){
          h_track_vars[1][ivar]->Fill(vars[ivar]);
        }
      }
    }
  }

  const bool pass_min_n_seed_tracks = int(seed_tracks->size()) >= min_n_seed_tracks;

  event.put(std::move(all_tracks), "all");
  event.put(std::move(seed_tracks), "seed");
  event.put(std::move(seed_tracks_copy), "seed");
  event.put(std::move(track_isolationDR03), "isolationDR03");
  

  return pass_min_n_seed_tracks;
}

void TrackFilter::getIsolation(const PolarLorentzVector& p4, 
                                       const pat::PackedCandidateCollection *pc, int pc_idx,
                                       pat::PFIsolation &iso, pat::PFIsolation &miniiso) const
{
        float chiso=0, nhiso=0, phiso=0, puiso=0;   // standard isolation
        float chmiso=0, nhmiso=0, phmiso=0, pumiso=0;  // mini isolation
        float miniDR = std::max(miniIsoParams_[0], std::min(miniIsoParams_[1], miniIsoParams_[2]/p4.pt()));
        for(pat::PackedCandidateCollection::const_iterator pf_it = pc->begin(); pf_it != pc->end(); pf_it++){
            if(int(pf_it - pc->begin()) == pc_idx)  //don't count itself
                continue;
            int id = std::abs(pf_it->pdgId());
            bool fromPV = (pf_it->fromPV()>1 || fabs(pf_it->dz()) < pfIsolation_DZ_);
            float pt = pf_it->p4().pt();
            float dr = deltaR(p4, *pf_it);

            if(dr < pfIsolation_DR_){
                // charged cands from PV get added to trackIso
                if(id==211 && fromPV)
                    chiso += pt;
                // charged cands not from PV get added to pileup iso
                else if(id==211)
                    puiso += pt;
                // neutral hadron iso
                if(id==130)
                    nhiso += pt;
                // photon iso
                if(id==22)
                    phiso += pt;
            }
            // same for mini isolation
            if(dr < miniDR){
                if(id == 211 && fromPV)
                    chmiso += pt;
                else if(id == 211)
                    pumiso += pt;
                if(id == 130)
                    nhmiso += pt;
                if(id == 22)
                    phmiso += pt;
            }
        }

        iso = pat::PFIsolation(chiso,nhiso,phiso,puiso);
        miniiso = pat::PFIsolation(chmiso,nhmiso,phmiso,pumiso);

}






DEFINE_FWK_MODULE(TrackFilter);
