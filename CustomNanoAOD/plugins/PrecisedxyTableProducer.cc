// https://cms-talk.web.cern.ch/t/track-impact-parameter-measurement/6577

// IPTools -> absoluteTransverseImpactParameter
// TransientTrackBuilder

// system include files
#include <memory>
#include <vector>

// user include files
#include "FWCore/Framework/interface/Frameworkfwd.h"
#include "FWCore/Framework/interface/stream/EDProducer.h"

#include "FWCore/Framework/interface/Event.h"
#include "FWCore/Framework/interface/MakerMacros.h"

#include "FWCore/ParameterSet/interface/ParameterSet.h"
#include "FWCore/Utilities/interface/StreamID.h"

#include "DataFormats/Math/interface/deltaR.h"
#include "DataFormats/Math/interface/Vector3D.h"
/* #include "MagneticField/Engine/interface/MagneticField.h"
#include "TrackingTools/GeomPropagators/interface/Propagator.h"
#include "TrackingTools/TrajectoryParametrization/interface/GlobalTrajectoryParameters.h"
#include "TrackingTools/TrajectoryState/interface/FreeTrajectoryState.h"
#include "MagneticField/Records/interface/IdealMagneticFieldRecord.h"
#include "TrackingTools/Records/interface/TrackingComponentsRecord.h" */

#include "DataFormats/VertexReco/interface/Vertex.h"
#include "DataFormats/VertexReco/interface/VertexFwd.h"
#include "DataFormats/NanoAOD/interface/FlatTable.h"

#include "TrackingTools/TransientTrack/interface/TransientTrackBuilder.h"
#include "TrackingTools/Records/interface/TransientTrackRecord.h"
#include "TrackingTools/TransientTrack/interface/TransientTrack.h"
#include "TrackingTools/IPTools/interface/IPTools.h"
#include "DataFormats/GeometryCommonDetAlgo/interface/Measurement1D.h"


//
// class declaration
//
class PrecisedxyTableProducer : public edm::stream::EDProducer<> {
public:
  explicit PrecisedxyTableProducer(const edm::ParameterSet&);
  ~PrecisedxyTableProducer() override;

  static void fillDescriptions(edm::ConfigurationDescriptions& descriptions);

private:
  void beginStream(edm::StreamID) override;
  void produce(edm::Event&, const edm::EventSetup&) override;
  void endStream() override;

  // ----------member data ---------------------------

  const edm::EDGetTokenT<std::vector<reco::Vertex>> svSrc_;  /// Input
  const edm::EDGetTokenT<std::vector<reco::Vertex>> pvSrc_;  /// Input
  const std::string extraOut_;   /// New parameters will be added to this table.

  // ----------internal functions ---------------------------

  /// Propagate a track to a given radius, given the magnetic
  /// field and the propagator. Store the resulting
  /// position, momentum, and direction.
/*   void propagateTrackToPCA(const reco::Vertex& fSV,
                           const reco::Track& fTrack,
                           const MagneticField& fField,
                           const Propagator& fPropagator,
                           reco::TrackBase::Point& resultPos,
                           reco::TrackBase::Vector& resultMom); */
};


//
// constructors and destructor
//
PrecisedxyTableProducer::PrecisedxyTableProducer(const edm::ParameterSet& iConfig)
    : svSrc_(consumes<std::vector<reco::Vertex>>(iConfig.getParameter<edm::InputTag>("svSrc"))),
      pvSrc_(consumes<std::vector<reco::Vertex>>(iConfig.getParameter<edm::InputTag>("pvSrc"))),
      extraOut_(iConfig.getParameter<std::string>("extrapOut"))
      {
        std::cout << "Propagator constructor is called" << std::endl;
        produces<nanoaod::FlatTable>(extraOut_);
      }

PrecisedxyTableProducer::~PrecisedxyTableProducer() {}

//
// member functions
//

// ------------ method called on each new Event  ------------
void PrecisedxyTableProducer::produce(edm::Event& iEvent, const edm::EventSetup& iSetup) {
  
  // get stuff from Event Setup
/*   edm::ESHandle<MagneticField> field_h;
  iSetup.get<IdealMagneticFieldRecord>().get(field_h);
  edm::ESHandle<Propagator> propagator_h;
  iSetup.get<TrackingComponentsRecord>().get("SteppingHelixPropagatorAny", propagator_h); */
  edm::ESHandle<TransientTrackBuilder> trackBuilder;
  iSetup.get<TransientTrackRecord>().get("TransientTrackBuilder", trackBuilder);
  

  // get stuff from Event
  edm::Handle<std::vector<reco::Vertex>> svsIn;
  iEvent.getByToken(svSrc_, svsIn);

  edm::Handle<std::vector<reco::Vertex>> pvsIn;
  iEvent.getByToken(pvSrc_, pvsIn);
  const auto& PV0 = pvsIn->front();

  // auto temporaryOutput = std::make_unique<std::vector<float>>();

  std::vector<float> dummy;
/*   std::vector<float> track_dxyByHand, track_dxy; */



  for (auto& sv : *svsIn) {
    for(auto trkBegin = sv.tracks_begin(), trkEnd = sv.tracks_end(), itrk = trkBegin;
       itrk != trkEnd;
       ++itrk){

        reco::TransientTrack transient_track = trackBuilder->build(**itrk);
        std::pair<bool, Measurement1D> precisedxy = IPTools::absoluteTransverseImpactParameter(transient_track, PV0);
        dummy.push_back(precisedxy.second.value());

/*         reco::TrackBase::Point extTkPos;
        reco::TrackBase::Vector extTkMom;
        propagateTrackToPCA(sv, **itrk, *field_h, *propagator_h, extTkPos, extTkMom); */

/*         // backwards propagate
        reco::TrackBase::Point extTkPos_r;
        reco::TrackBase::Vector extTkMom_r;
        propagateTrackToPCA(PV0, sv.refittedTrack(*itrk), *field_h, *propagator_h, extTkPos_r, extTkMom_r);
        reco::Track extrapolated */
        
 /*  //      temporaryOutput->push_back(extTkPos.X());
        refit_extrap_dxy.push_back((extTkPos_r.X() - PV0.x())*(extTkPos_r.X() - PV0.x()) + 
                                   (extTkPos_r.Y() - PV0.y())*(extTkPos_r.Y() - PV0.y()));
        track_dxyByHand.push_back(((**itrk).vx() - PV0.x())*((**itrk).vx() - PV0.x()) + 
                                  ((**itrk).vy() - PV0.y())*((**itrk).vy() - PV0.y()));
        track_dxy.push_back((**itrk).dxy(PV0.position())); */

/*         std::cout << std::left << std::setw(8) << " " << std::setw(20) << "SV_pos" << std::setw(20) << "extrap_refPoint" << std::setw(20) << "orig_refPoint" << std::setw(20) << "reverse extrap_refPoint" << std::endl;
        std::cout << std::left << std::setw(8) << "x" << std::setw(20) << sv.x() << std::setw(20) << extTkPos.X() << std::setw(20) << (**itrk).vx() << std::setw(20) << extTkPos_r.X() << std::endl;
        std::cout << std::left << std::setw(8) << "y" << std::setw(20) << sv.y() << std::setw(20) << extTkPos.Y() << std::setw(20) << (**itrk).vy() << std::setw(20) << extTkPos_r.Y() << std::endl;
        std::cout << std::left << std::setw(8) << "z" << std::setw(20) << sv.z() << std::setw(20) << extTkPos.Z() << std::setw(20) << (**itrk).vz() << std::setw(20) << extTkPos_r.Z() << std::endl;
        std::cout << " " << std::endl;
        std::cout << std::left << std::setw(8) << " " << std::setw(20) << "refit_mom" << std::setw(20)  << "extrap_mom" << std::setw(20) << "orig_mom" << std::setw(20) << "reverse extrap_mom"<< std::endl;
        std::cout << std::left << std::setw(8) << "x" << std::setw(20) << sv.refittedTrack(*itrk).px() << std::setw(20) << extTkMom.X() << std::setw(20) << (**itrk).px() << std::setw(20) << extTkMom_r.X() << std::endl;
        std::cout << std::left << std::setw(8) << "y" << std::setw(20) << sv.refittedTrack(*itrk).py() << std::setw(20) << extTkMom.Y() << std::setw(20) << (**itrk).py() << std::setw(20) << extTkMom_r.Y() << std::endl;
        std::cout << std::left << std::setw(8) << "z" << std::setw(20) << sv.refittedTrack(*itrk).pz() << std::setw(20) << extTkMom.Z() << std::setw(20) << (**itrk).pz() << std::setw(20) << extTkMom_r.Z() << std::endl;
        std::cout << "--------------------------------------------------------------------------------" << std::endl; */

    }
  }  
  int nEntries = dummy.size();

  auto extraTable = std::make_unique<nanoaod::FlatTable>(nEntries, extraOut_, false);
  extraTable->addColumn<float>("dummy", dummy, "dummy", nanoaod::FlatTable::FloatColumn, 10);
/*   extraTable->addColumn<float>("track_dxyByHand", track_dxyByHand, "track_dxyByHand", nanoaod::FlatTable::FloatColumn, 10);
  extraTable->addColumn<float>("track_dxy", track_dxy, "track dxy", nanoaod::FlatTable::FloatColumn, 10); */

  /* iEvent.put(std::move(temporaryOutput), "tkExpo"); */
  iEvent.put(std::move(extraTable), extraOut_);


}

// ------------ method called once each stream before processing any runs, lumis or events  ------------
void PrecisedxyTableProducer::beginStream(edm::StreamID) {}

// ------------ method called once each stream after processing all runs, lumis and events  ------------
void PrecisedxyTableProducer::endStream() {}

// ------------ method fills 'descriptions' with the allowed parameters for the module  ------------
// ------------ method fills 'descriptions' with the allowed parameters for the module  ------------
void PrecisedxyTableProducer::fillDescriptions(edm::ConfigurationDescriptions &descriptions)
{
    edm::ParameterSetDescription desc;

    desc.add<edm::InputTag>("pvSrc")->setComment("Primary vertices");
    desc.add<edm::InputTag>("svSrc")->setComment("Secondary vertices");
    desc.add<std::string>("extraOut")->setComment("New table name");
    descriptions.addWithDefaultLabel(desc);
}

// -----------------------------------------------------------------------------
//
/* void PrecisedxyTableProducer::propagateTrackToPCA(const reco::Vertex& fSV,
                                            const reco::Track& fTrack,
                                            const MagneticField& fField,
                                            const Propagator& fPropagator,
                                            reco::TrackBase::Point& resultPos,
                                            reco::TrackBase::Vector& resultMom) {
  GlobalPoint SVPosition(fSV.x(),fSV.y(),fSV.z());   // reference point
  GlobalPoint trackPosition(fTrack.vx(), fTrack.vy(), fTrack.vz());   // reference point
  GlobalVector trackMomentum(fTrack.px(), fTrack.py(), fTrack.pz());  // reference momentum
  

  GlobalTrajectoryParameters trackParams(trackPosition, trackMomentum, fTrack.charge(), &fField);
  FreeTrajectoryState trackState(trackParams);

  FreeTrajectoryState propagatedInfo = fPropagator.propagate(
      trackState, SVPosition);

  resultPos = propagatedInfo.position();
  resultMom = propagatedInfo.momentum();
  } */


/*   if (propagatedInfo.isValid()) {
    resultPos = propagatedInfo.globalPosition();
    resultMom = propagatedInfo.globalMomentum();
    return true;
  } else {
    return false;
  } */

//define this as a plug-in
DEFINE_FWK_MODULE(PrecisedxyTableProducer);