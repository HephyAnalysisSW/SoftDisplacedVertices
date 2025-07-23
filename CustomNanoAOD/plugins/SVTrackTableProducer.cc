// This code is copied from 
// PhysicsTools/NanoAOD/plugins/VertexTableProducer.cc
// The main difference is that the original code takes VertexCompositePtrCandidate as SV source
// while this code take reco::Vertex
// In addition, some more variables are added

// system include files
#include <memory>

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
#include "CommonTools/Utils/interface/StringCutObjectSelector.h"

#include "TrackingTools/IPTools/interface/IPTools.h"
#include "TrackingTools/Records/interface/TransientTrackRecord.h"
#include "TrackingTools/TransientTrack/interface/TransientTrack.h"
#include "TrackingTools/TransientTrack/interface/TransientTrackBuilder.h"

#include "DataFormats/NanoAOD/interface/FlatTable.h"
#include "RecoVertex/VertexTools/interface/VertexDistance3D.h"
#include "RecoVertex/VertexTools/interface/VertexDistanceXY.h"
#include "RecoVertex/VertexPrimitives/interface/ConvertToFromReco.h"
#include "RecoVertex/VertexPrimitives/interface/VertexState.h"
#include "DataFormats/Common/interface/ValueMap.h"

#include "DataFormats/GeometryVector/interface/GlobalVector.h"

class SVTrackTableProducer : public edm::stream::EDProducer<> {
public:
  explicit SVTrackTableProducer(const edm::ParameterSet&);
  ~SVTrackTableProducer() override;

  static void fillDescriptions(edm::ConfigurationDescriptions& descriptions);

private:
  void beginStream(edm::StreamID) override;
  void produce(edm::Event&, const edm::EventSetup&) override;
  void endStream() override;

  //virtual void beginRun(edm::Run const&, edm::EventSetup const&) override;
  //virtual void endRun(edm::Run const&, edm::EventSetup const&) override;
  //virtual void beginLuminosityBlock(edm::LuminosityBlock const&, edm::EventSetup const&) override;
  //virtual void endLuminosityBlock(edm::LuminosityBlock const&, edm::EventSetup const&) override;

  // ----------member data ---------------------------

  const edm::EDGetTokenT<std::vector<reco::Vertex>> pvs_;
  const edm::EDGetTokenT<std::vector<reco::Vertex>> svs_;
  const edm::EDGetTokenT<reco::TrackCollection> tksrc_;
  const StringCutObjectSelector<reco::Vertex> svCut_;
  const std::string svName_;
  const std::string svDoc_;
  const double dlenMin_, dlenSigMin_;
  const bool storeCharge_;
  const std::string tkName_, tkbranchName_, tkbranchDoc_;
  const std::string lookupName_, lookupDoc_;
  bool debug;

};

SVTrackTableProducer::SVTrackTableProducer(const edm::ParameterSet& params)
    : pvs_(consumes<std::vector<reco::Vertex>>(params.getParameter<edm::InputTag>("pvSrc"))),
      svs_(consumes<std::vector<reco::Vertex>>(params.getParameter<edm::InputTag>("svSrc"))),
      tksrc_(consumes<reco::TrackCollection>(params.getParameter<edm::InputTag>("tkSrc"))),
      svCut_(params.getParameter<std::string>("svCut"), true),
      svName_(params.getParameter<std::string>("svName")),
      svDoc_(params.getParameter<std::string>("svDoc")),
      dlenMin_(params.getParameter<double>("dlenMin")),
      dlenSigMin_(params.getParameter<double>("dlenSigMin")),
      storeCharge_(params.getParameter<bool>("storeCharge")),
      tkName_(params.getParameter<std::string>("tkName")),
      tkbranchName_(params.getParameter<std::string>("tkbranchName")),
      tkbranchDoc_(params.getParameter<std::string>("tkbranchDoc")),

      lookupName_(params.getParameter<std::string>("lookupName")),
      lookupDoc_(params.getParameter<std::string>("lookupDoc")),

      debug(params.getParameter<bool>("debug")
      )

{
  produces<nanoaod::FlatTable>("svs");
  produces<nanoaod::FlatTable>("tksrefit");
  produces<nanoaod::FlatTable>("svstksidx"); // secondary vertex track index
}

SVTrackTableProducer::~SVTrackTableProducer() {
}


void SVTrackTableProducer::produce(edm::Event& iEvent, const edm::EventSetup& iSetup) {
  using namespace edm;
  edm::Handle<std::vector<reco::Vertex>> pvsIn;
  iEvent.getByToken(pvs_, pvsIn);

  edm::Handle<std::vector<reco::Vertex>> svsIn;
  iEvent.getByToken(svs_, svsIn);

  edm::Handle<reco::TrackCollection> trIn;
  iEvent.getByToken(tksrc_, trIn);

  edm::ESHandle<TransientTrackBuilder> tt_builder;
  iSetup.get<TransientTrackRecord>().get("TransientTrackBuilder", tt_builder);


  auto vertices = std::make_unique<std::vector<reco::Vertex>>();
  std::vector<float> x,y,z,dlen, dlenSig, pAngle, Lxy, LxySig, chi2, normalizedChi2;
  std::vector<float> mass, energy, pt;
  std::vector<float> L_phi, L_eta, sum_tkW;
  std::vector<int> charge, sv_tracksSize, sv_nTracks, SecVtxIdx, TrackIdx;
  std::vector<float> ndof; 
  std::vector<int> ngoodTrackVec;
  ////// temporary
  std::vector<float> tk_W; // track weight
  // std::vector<float> tk_pt_vec; // track weight
  /////////////////
  VertexDistance3D vdist;
  VertexDistanceXY vdistXY;
  std::vector<float> tk_dist2d_min, tk_dist2d_max, tk_dist2d_min_sig, tk_dist2d_max_sig;
  std::vector<float> tk_dist3d_min, tk_dist3d_max, tk_dist3d_min_sig, tk_dist3d_max_sig;

  std::vector<float> tk_eta, tk_phi, tk_dxy, tk_dz, tk_pt, tk_dxyError, tk_dzError, tk_ptError, tk_phiError, tk_etaError, tk_validFraction, tk_normalizedChi2;
  std::vector<int> tk_charge, tk_numberOfValidHits, tk_numberOfLostHits;
  std::vector<int> tk_isHighPurity;
  std::vector<int> tk_algo; 
  std::vector<int> tk_svIdx, tk_tkIdx;
  int ntk_refit = 0;


  size_t i = 0;
  const auto& PV0 = pvsIn->front();
  for (const auto& sv : *svsIn) {
    if (svCut_(sv)) {
      Measurement1D dl =
          vdist.distance(PV0, VertexState(RecoVertex::convertPos(sv.position()), RecoVertex::convertError(sv.error())));
      if (dl.value() > dlenMin_ and dl.significance() > dlenSigMin_) {
        x.push_back(sv.x());
        y.push_back(sv.y());
        z.push_back(sv.z());
        dlen.push_back(dl.value());
        dlenSig.push_back(dl.significance());
        vertices->push_back(sv);
        double dx = (sv.x() - PV0.x());
        double dy = (sv.y() - PV0.y());
        double dz = (sv.z() - PV0.z());
        double pdotv = (dx * sv.p4().Px() + dy * sv.p4().Py() + dz * sv.p4().Pz()) / sqrt(sv.p4().P2()) / sqrt(dx * dx + dy * dy + dz * dz);
        pAngle.push_back(std::acos(pdotv));
        
        GlobalVector pVec(dx, dy, dz);
        L_eta.push_back(pVec.eta());
        L_phi.push_back(pVec.phi());
        
        
        Measurement1D d2d = vdistXY.distance(
            PV0, VertexState(RecoVertex::convertPos(sv.position()), RecoVertex::convertError(sv.error())));
        Lxy.push_back(d2d.value());
        LxySig.push_back(d2d.significance());
        mass.push_back(sv.p4().mass());
        energy.push_back(sv.p4().E());
        pt.push_back(sv.p4().pt());
        sv_tracksSize.push_back(sv.tracksSize());
        sv_nTracks.push_back(sv.nTracks());
        chi2.push_back(sv.chi2());
        normalizedChi2.push_back(sv.normalizedChi2());
        ndof.push_back(sv.ndof());

        std::vector<Measurement1D> dists2d;
        std::vector<Measurement1D> dists3d;
        double max2d = -1;
        double max2dsig = -1;
        double min2d = 999;
        double min2dsig = 999;
        double max3d = -1;
        double max3dsig = -1;
        double min3d = 999;
        double min3dsig = 999;

        if (!sv.hasRefittedTracks()) {
          //std::cout << "SV has no refitted tracks!" << std::endl;
        }
        else{
          auto rtks = sv.refittedTracks();
          for (auto& rtk:rtks){
            tk_normalizedChi2.push_back(rtk.normalizedChi2());
            tk_eta.push_back(rtk.eta());
            tk_phi.push_back(rtk.phi());
            tk_pt.push_back(rtk.pt());
            tk_dxy.push_back(rtk.dxy(PV0.position()));
            tk_dz.push_back(rtk.dz(PV0.position()));
            tk_etaError.push_back(rtk.etaError());
            tk_phiError.push_back(rtk.phiError());
            tk_ptError.push_back(rtk.ptError());
            tk_dxyError.push_back(rtk.dxyError(PV0.position(), PV0.covariance()));
            tk_dzError.push_back(rtk.dzError());
            tk_charge.push_back(rtk.charge());
            tk_isHighPurity.push_back(rtk.quality(reco::TrackBase::TrackQuality::highPurity));
            tk_numberOfValidHits.push_back(rtk.numberOfValidHits());
            tk_numberOfLostHits.push_back(rtk.numberOfLostHits());
            tk_validFraction.push_back(rtk.validFraction());
            tk_algo.push_back(rtk.algo());
            tk_svIdx.push_back(&sv - &((*svsIn)[0]));

            auto otk = sv.originalTrack(rtk);
            tk_tkIdx.push_back(otk.key());
            ntk_refit += 1;

            reco::TransientTrack ttk = tt_builder->build(*otk);
            auto dist2d = IPTools::absoluteTransverseImpactParameter(ttk, sv);
            auto dist3d = IPTools::absoluteImpactParameter3D(ttk, sv);
            if (dist2d.first) {
              dists2d.push_back(dist2d.second);
            }
            if (dist3d.first) {
              dists3d.push_back(dist3d.second);
            }
          }

          for (size_t i=0; i<dists2d.size(); ++i) {
            if (dists2d[i].value()>max2d) {
              max2d = dists2d[i].value();
              max2dsig = dists2d[i].significance();
            }
            if (dists2d[i].value()<min2d) {
              min2d = dists2d[i].value();
              min2dsig = dists2d[i].significance();
            }
          }
          for (size_t i=0; i<dists3d.size(); ++i) {
            if (dists3d[i].value()>max3d) {
              max3d = dists3d[i].value();
              max3dsig = dists3d[i].significance();
            }
            if (dists3d[i].value()<min3d) {
              min3d = dists3d[i].value();
              min3dsig = dists3d[i].significance();
            }
          }
        }
        tk_dist2d_min.push_back(min2d);
        tk_dist2d_max.push_back(max2d);
        tk_dist2d_min_sig.push_back(min2dsig);
        tk_dist2d_max_sig.push_back(max2dsig);
        tk_dist3d_min.push_back(min3d);
        tk_dist3d_max.push_back(max3d);
        tk_dist3d_min_sig.push_back(min3dsig);
        tk_dist3d_max_sig.push_back(max3dsig);

        // GOOD TRACK CRITERIA
        // ---------------------------
        int ngoodTrack = 0;
        float sum_tk_weights = 0.;
        for (auto v_tk = sv.tracks_begin(), vtke = sv.tracks_end(); v_tk != vtke; ++v_tk){
          sum_tk_weights += sv.trackWeight(*v_tk);
          if(debug){
            std::cout << "------------------------------------------------" << std::endl;
            std::cout << "----------  GOOD TRACK CRITERIA  ---------" << std::endl;
            std::cout << std::left << std::setw(20) << "numberOfValidHits:" << std::setw(16) << ((*v_tk)->numberOfValidHits()) << std::endl;
            std::cout << std::left << std::setw(20) << "normalizedChi2:" << std::setw(16) << ((*v_tk)->normalizedChi2()) << std::endl;
            std::cout << std::left << std::setw(20) << "ptError/pt:" << std::setw(16) << ((*v_tk)->ptError() / (*v_tk)->pt()) << std::endl;
            std::cout << std::left << std::setw(20) << "dxy/dxyError:" << std::setw(16) << (abs((*v_tk)->dxy(PV0.position()) / (*v_tk)->dxyError(PV0.position(), PV0.covariance()))) << std::endl;
            std::cout << std::left << std::setw(20) << "dz:" << std::setw(16) << (abs((*v_tk)->dz(PV0.position()))) << std::endl;
            std::cout << "------------------------------------------------" << std::endl;
          }
          if(
             (abs((*v_tk)->dxy(PV0.position()) / (*v_tk)->dxyError(PV0.position(), PV0.covariance())) > 4) &&
             ((*v_tk)->normalizedChi2() < 5) &&
             ((*v_tk)->numberOfValidHits() > 13) &&
             ((*v_tk)->ptError() / (*v_tk)->pt() < 0.015) &&
             (abs((*v_tk)->dz(PV0.position())) < 4)
             ){ngoodTrack++;}
          
        }
        sum_tkW.push_back(sum_tk_weights);
        ngoodTrackVec.push_back(ngoodTrack);
        // ------------------------------------------------------

        if (storeCharge_) {
          int sum_charge = 0;
          for (auto v_tk = sv.tracks_begin(), vtke = sv.tracks_end(); v_tk != vtke; ++v_tk){
            sum_charge += (*v_tk)->charge();
          }
          charge.push_back(sum_charge);
        }
        

        // Matches the track idx with the vertex idx.
        // ---------------------------------------------
        // Compares the indices of recoTracks_TrackFilter_seed and 
        // recoVertexs_IVFSecondaryVerticesSoftDV objects and pushes them in two different vectors in the correct order.
        for (const auto& tr : *trIn) {
          for (auto v_tk = sv.tracks_begin(), vtke = sv.tracks_end(); v_tk != vtke; ++v_tk){
            // type(v_tk): iterator(edm::RefToBase(reco::Track))
            if (&tr == &(**v_tk)){
              SecVtxIdx.push_back(&sv - &((*svsIn)[0]));
              TrackIdx.push_back(&tr - &((*trIn)[0]));
              tk_W.push_back(sv.trackWeight(*v_tk));

              // Sanity check --- temporary code
              // tk_pt_vec.push_back(tr.pt());
              ////////////////////////////////////

              if(debug){
                std::cout << "Vertex Id "  << &sv - &((*svsIn)[0]) << std::endl;
                std::cout << "Track Id " <<  &tr - &((*trIn)[0]) << std::endl;
                std::cout << "Track Weight: " << sv.trackWeight(*v_tk) << std::endl;
              }
            }
          }
        }
        // ----------------------------------------------------------------------


      }
    }
    i++;
  }

  // Flat table for the secondary vertices
  auto svsTable = std::make_unique<nanoaod::FlatTable>(vertices->size(), svName_, false);
  svsTable->addColumn<float>("x", x, "x position in cm", nanoaod::FlatTable::FloatColumn, 10);
  svsTable->addColumn<float>("y", y, "y position in cm", nanoaod::FlatTable::FloatColumn, 10);
  svsTable->addColumn<float>("z", z, "z position in cm", nanoaod::FlatTable::FloatColumn, 10);
  svsTable->addColumn<float>("mass", mass, "Reconstructed invariant mass at the vertex.", nanoaod::FlatTable::FloatColumn, 10);
  svsTable->addColumn<float>("energy", energy, "Reconstructed energy at the vertex.", nanoaod::FlatTable::FloatColumn, 10);
  svsTable->addColumn<float>("pt", pt, "Pt of 4-vector of vertex.", nanoaod::FlatTable::FloatColumn, 10);
  svsTable->addColumn<float>("dlen", dlen, "decay length in cm", nanoaod::FlatTable::FloatColumn, 10);
  svsTable->addColumn<float>("dlenSig", dlenSig, "decay length significance", nanoaod::FlatTable::FloatColumn, 10);
  svsTable->addColumn<float>("Lxy", Lxy, "2D decay length in cm", nanoaod::FlatTable::FloatColumn, 10);
  svsTable->addColumn<float>("LxySig", LxySig, "2D decay length significance", nanoaod::FlatTable::FloatColumn, 10);
  svsTable->addColumn<float>(
      "pAngle", pAngle, "pointing angle, i.e. acos(p_SV * (SV - PV)) ", nanoaod::FlatTable::FloatColumn, 10);
  svsTable->addColumn<float>(
      "L_phi", L_phi, "Azimuthal angle of the vector from PV to SV", nanoaod::FlatTable::FloatColumn, 10);
  svsTable->addColumn<float>(
      "L_eta", L_eta, "Pseudorapidity of the vector from PV to SV", nanoaod::FlatTable::FloatColumn, 10);
  svsTable->addColumn<int>("tracksSize", sv_tracksSize, "number of tracks in the SV", nanoaod::FlatTable::IntColumn);
  svsTable->addColumn<int>("nTracks", sv_nTracks, "the number of tracks in the vertex with weight above 0.50", nanoaod::FlatTable::IntColumn);
  if (storeCharge_) {
    svsTable->addColumn<int>("charge", charge, "sum of the charge of the SV tracks", nanoaod::FlatTable::IntColumn);
  }
  svsTable->addColumn<float>("chi2", chi2, "chi2 of vertex fit", nanoaod::FlatTable::FloatColumn, 10);
  svsTable->addColumn<float>("normalizedChi2", normalizedChi2, "normalizedChi2 of vertex fit", nanoaod::FlatTable::FloatColumn, 10);
  svsTable->addColumn<float>("ndof", ndof, "ndof of vertex fit", nanoaod::FlatTable::FloatColumn, 10);
  svsTable->addColumn<float>("sum_tkW", sum_tkW, "sum of track weights", nanoaod::FlatTable::FloatColumn, 10);
  svsTable->addColumn<int>("ngoodTrack", ngoodTrackVec, "number of good tracks associated with the vertex according to Ivan's criteria", nanoaod::FlatTable::IntColumn);
  svsTable->addColumn<float>("tk_dist2d_min", tk_dist2d_min, "Min track dxy wrt the vertex", nanoaod::FlatTable::FloatColumn, 10);
  svsTable->addColumn<float>("tk_dist2d_max", tk_dist2d_max, "Max track dxy wrt the vertex", nanoaod::FlatTable::FloatColumn, 10);
  svsTable->addColumn<float>("tk_dist2d_min_sig", tk_dist2d_min_sig, "Min track dxy significance wrt the vertex", nanoaod::FlatTable::FloatColumn, 10);
  svsTable->addColumn<float>("tk_dist2d_max_sig", tk_dist2d_max_sig, "Max track dxy significance wrt the vertex", nanoaod::FlatTable::FloatColumn, 10);
  svsTable->addColumn<float>("tk_dist3d_min", tk_dist3d_min, "Min track d3d wrt the vertex", nanoaod::FlatTable::FloatColumn, 10);
  svsTable->addColumn<float>("tk_dist3d_max", tk_dist3d_max, "Max track d3d wrt the vertex", nanoaod::FlatTable::FloatColumn, 10);
  svsTable->addColumn<float>("tk_dist3d_min_sig", tk_dist3d_min_sig, "Min track d3d significance wrt the vertex", nanoaod::FlatTable::FloatColumn, 10);
  svsTable->addColumn<float>("tk_dist3d_max_sig", tk_dist3d_max_sig, "Max track d3d significance wrt the vertex", nanoaod::FlatTable::FloatColumn, 10);
   
  
  if (debug) {
    std::cout << "SVs " << vertices->size() << std::endl;
    for (size_t ivtx=0; ivtx<vertices->size(); ++ivtx) {
        const reco::Vertex& vtx = vertices->at(ivtx);
        std::cout << "reco vertex " << ivtx << " x: " << vtx.x() << " y: " << vtx.y() << " z: " << vtx.z()  << " tracks " << std::endl;
        for (auto v_tk = vtx.tracks_begin(), vtke = vtx.tracks_end(); v_tk != vtke; ++v_tk){
          std::cout << "  pt: " << (*v_tk)->pt() << " eta: " << (*v_tk)->eta() << " phi: " << (*v_tk)->phi() << std::endl;
        }
    }
  }

  // Refitted track table
  //
  auto refittkTable = std::make_unique<nanoaod::FlatTable>(ntk_refit, tkName_, false);
  refittkTable->addColumn<float>("normalizedChi2", tk_normalizedChi2, "normalizedChi2", nanoaod::FlatTable::FloatColumn, 10);
  refittkTable->addColumn<float>("eta", tk_eta, "eta", nanoaod::FlatTable::FloatColumn, 10);
  refittkTable->addColumn<float>("phi", tk_phi, "phi", nanoaod::FlatTable::FloatColumn, 10);
  refittkTable->addColumn<float>("pt", tk_pt, "pt", nanoaod::FlatTable::FloatColumn, 10);
  refittkTable->addColumn<float>("dxy", tk_dxy, "dxy", nanoaod::FlatTable::FloatColumn, 10);
  refittkTable->addColumn<float>("dz", tk_dz, "dz", nanoaod::FlatTable::FloatColumn, 10);
  refittkTable->addColumn<float>("etaError", tk_etaError, "etaError", nanoaod::FlatTable::FloatColumn, 10);
  refittkTable->addColumn<float>("phiError", tk_phiError, "phiError", nanoaod::FlatTable::FloatColumn, 10);
  refittkTable->addColumn<float>("ptError", tk_ptError, "ptError", nanoaod::FlatTable::FloatColumn, 10);
  refittkTable->addColumn<float>("dxyError", tk_dxyError, "dxyError", nanoaod::FlatTable::FloatColumn, 10);
  refittkTable->addColumn<float>("dzError", tk_dzError, "dzError", nanoaod::FlatTable::FloatColumn, 10);
  refittkTable->addColumn<int>("charge", tk_charge, "Charge", nanoaod::FlatTable::IntColumn, 10);
  refittkTable->addColumn<int>("isHighPurity", tk_isHighPurity, "Is High Purity", nanoaod::FlatTable::IntColumn);
  refittkTable->addColumn<int>("numberOfValidHits", tk_numberOfValidHits, "Number of valid hits", nanoaod::FlatTable::IntColumn);
  refittkTable->addColumn<int>("numberOfLostHits", tk_numberOfLostHits, "Number of cases with layers without hits", nanoaod::FlatTable::IntColumn);
  refittkTable->addColumn<float>("validFraction", tk_validFraction, "Fraction of valid hits on track", nanoaod::FlatTable::FloatColumn, 10);
  refittkTable->addColumn<int>("algo", tk_algo, "Algorithm of track reconstruction", nanoaod::FlatTable::IntColumn);
  refittkTable->addColumn<int>("svIdx", tk_svIdx, "Index of displaced vertex the track is associated to", nanoaod::FlatTable::IntColumn);
  refittkTable->addColumn<int>("tkIdx", tk_tkIdx, "Index of original track that the refitted track corresponds to", nanoaod::FlatTable::IntColumn);


  //This part used to generate the index mapping between reco vertex and reco tracks, a bette way (LUT) is used now so this part is commented out
  // -------------------------------------------------------------
  //
  //// Now vertex table is produced, let's make track tables
  //const auto& tracks = iEvent.get(tksrc_);
  //auto ntrack = tracks.size();
  ////auto tktab = std::make_unique<nanoaod::FlatTable>(ntrack, tkName_, false, true);

  //std::vector<int> key(ntrack, -1);
 

  //for (size_t i = 0; i < ntrack; ++i) {
  //  const auto& tk = tracks.at(i);
  //  if (debug){
  //    std::cout << "reco track " << i << " pt " << tk.pt() << " eta " << tk.eta() << " phi " << tk.phi() << std::endl;
  //  }
  //  // match vertices by matching tracks
  //  // FIXME: This algorithm assumes tracks are not reused for different vertices, so it might be a problem when it is not the case
  //  int matched_vtx_idx = -1;

  //  for (size_t ivtx=0; ivtx<vertices->size(); ++ivtx) {
  //    const reco::Vertex& vtx = vertices->at(ivtx);
  //    double match_threshold = 1.1;
  //    // for each LLP, compare the matched tracks with tracks in the reco vertex 
  //    
  //    if (debug){
  //      std::cout << "reco vertex " << ivtx << " x: " << vtx.x() << " y: " << vtx.y() << " z: " << vtx.z()  << " tracks " << std::endl;
  //      for (auto v_tk = vtx.tracks_begin(), vtke = vtx.tracks_end(); v_tk != vtke; ++v_tk){
  //        std::cout << "  pt: " << (*v_tk)->pt() << " eta: " << (*v_tk)->eta() << " phi: " << (*v_tk)->phi() << std::endl;
  //      }
  //    }

  //    for (auto v_tk = vtx.tracks_begin(), vtke = vtx.tracks_end(); v_tk != vtke; ++v_tk){
  //      double dpt = fabs(tk.pt() - (*v_tk)->pt()) + 1;
  //      double deta = fabs(tk.eta() - (*v_tk)->eta()) + 1;
  //      double dphi = fabs(tk.phi() - (*v_tk)->phi()) + 1;
  //      if (dpt * deta * dphi < match_threshold){
  //        matched_vtx_idx = (int) ivtx;

  //        // First IdxLUT implementation (OLD)
  //        // -------------------------------------
  //        // SecVtxIdx.push_back(ivtx);
  //        // TrackIdx.push_back(i);
  //        // -------------------------------------

  //        if (debug) {
  //          std::cout << "  track matched: " << std::endl;
  //          std::cout << "  |->  gen pt " << tk.pt() << " eta " << tk.eta() << " phi " << tk.phi() << std::endl;
  //          std::cout << "  --> reco pt " << (*v_tk)->pt() << " eta " << (*v_tk)->eta() << " phi " << (*v_tk)->phi() << std::endl;
  //        }
  //        break;
  //      }
  //    }
  //    if (matched_vtx_idx!=-1)
  //      break;
  //  }
  //  if (debug)
  //    std::cout << "track matched with vertex " << matched_vtx_idx << std::endl;
  //  key[i] = matched_vtx_idx;
  //}
  // -------------------------------------------------------------

  // LUT: lookup table
  // ------------------------------------------------------------------------------
  // We create here another table which serves as a lookup table for indices.
  // Access track and vertex indices in both directions with LUT.
  // 
  // LUT: lookup table
  auto LUT = std::make_unique<nanoaod::FlatTable>(SecVtxIdx.size(), lookupName_, false);


  LUT->addColumn<int>("SecVtxIdx", SecVtxIdx, "Secondary vertex index", nanoaod::FlatTable::IntColumn);
  LUT->addColumn<int>("TrackIdx", TrackIdx, "Track index", nanoaod::FlatTable::IntColumn);
  LUT->addColumn<float>("TrackWeight", tk_W, "Trck weight", nanoaod::FlatTable::FloatColumn, -1);
  // LUT->addColumn<float>("Trackpt", tk_pt_vec, "Secondary vertex index", nanoaod::FlatTable::FloatColumn, -1);
  // ----------------------------------------------------------------------------------------------------


  // This is the previous track vertex mapping (similar functionality compared with LUT)
  //tktab->addColumn<int>(tkbranchName_, key, tkbranchDoc_, nanoaod::FlatTable::IntColumn);

  iEvent.put(std::move(svsTable), "svs");
  iEvent.put(std::move(refittkTable), "tksrefit");
  //iEvent.put(std::move(tktab), "tks");
  iEvent.put(std::move(LUT), "svstksidx");
}

// ------------ method called once each stream before processing any runs, lumis or events  ------------
void SVTrackTableProducer::beginStream(edm::StreamID) {}

// ------------ method called once each stream after processing all runs, lumis and events  ------------
void SVTrackTableProducer::endStream() {}

// ------------ method fills 'descriptions' with the allowed parameters for the module  ------------
void SVTrackTableProducer::fillDescriptions(edm::ConfigurationDescriptions& descriptions) {
  //The following says we do not know what parameters are allowed so do no validation
  // Please change this to state exactly what you do use, even if it is no parameters
  edm::ParameterSetDescription desc;
  desc.setUnknown();
  descriptions.addDefault(desc);
}

DEFINE_FWK_MODULE(SVTrackTableProducer);
