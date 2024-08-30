#include <queue>
#include "FWCore/Framework/interface/one/EDProducer.h"
#include "FWCore/Framework/interface/Event.h"
#include "FWCore/Framework/interface/Frameworkfwd.h"
#include "FWCore/Framework/interface/MakerMacros.h"
#include "FWCore/ServiceRegistry/interface/Service.h"
#include "CommonTools/UtilAlgos/interface/TFileService.h"
#include "DataFormats/BeamSpot/interface/BeamSpot.h"
#include "DataFormats/HepMCCandidate/interface/GenParticle.h"
#include "DataFormats/HepMCCandidate/interface/GenParticleFwd.h"
#include "DataFormats/Math/interface/deltaR.h"
#include "RecoVertex/VertexTools/interface/VertexDistance3D.h"
#include "RecoVertex/VertexTools/interface/VertexDistanceXY.h"
#include "SoftDisplacedVertices/SoftDVDataFormats/interface/GenInfo.h"


class GenProducer : public edm::one::EDProducer<edm::one::SharedResources> {
  public:
    explicit GenProducer(const edm::ParameterSet&);
  private:
    void produce(edm::Event&, const edm::EventSetup&) override;
    const edm::EDGetTokenT<reco::GenParticleCollection> gen_particles_token;
    const edm::EDGetTokenT<reco::BeamSpot> beamspot_token;
    int llp_id;
    int lsp_id;
    bool match_by_dist;
    bool match_by_daughter;
    bool debug;

    std::vector<SoftDV::LLP> findPattern(const edm::Handle<reco::GenParticleCollection>& gen_particles, const edm::Handle<reco::BeamSpot>& beamspot) const;
    reco::GenParticleCollection GetDaughters(const reco::GenParticle& gen, const edm::Handle<reco::GenParticleCollection>& gen_particles) const;

    bool pass_gtk(const reco::GenParticle& gtk, const edm::Handle<reco::BeamSpot>& beamspot) const {
      if (gtk.status()!=1) return false;
      if ( (gtk.charge()==0) || (fabs(gtk.charge())<1) ) return false;
      if (gtk.pt()<0.5 || fabs(gtk.eta()) > 2.5 ) return false;
      double dxy_gen = gen_dxy(gtk,beamspot->position());
      if (dxy_gen<0.005) return false;

      return true;
    }

    reco::GenParticleRef get_gen(const reco::Candidate* c, const edm::Handle<reco::GenParticleCollection>& gens) const {
      if (c != 0) {
        for (int i = 0, ie = int(gens->size()); i < ie; ++i) {
          const reco::GenParticle& gen = gens->at(i);
          if (&gen == c)
            return reco::GenParticleRef(gens, i);
        }
      }
      return reco::GenParticleRef();
    }

    VertexDistanceXY distcalc_2d;
    VertexDistance3D distcalc_3d;
};

GenProducer::GenProducer(const edm::ParameterSet& cfg)
  : gen_particles_token(consumes<reco::GenParticleCollection>(cfg.getParameter<edm::InputTag>("gen_particles_token"))),
    beamspot_token(consumes<reco::BeamSpot>(cfg.getParameter<edm::InputTag>("beamspot_token"))),
    llp_id(cfg.getParameter<int>("llp_id")),
    lsp_id(cfg.getParameter<int>("lsp_id")),
    match_by_dist(cfg.getParameter<bool>("match_by_dist")),
    match_by_daughter(cfg.getParameter<bool>("match_by_daughter")),
    debug(cfg.getParameter<bool>("debug"))
{
  // usesResource();
  if (match_by_dist + match_by_daughter != 1)
    throw cms::Exception("GenProducer", "Only one of match_by_dist and match_by_daughter should be true.");
  produces<std::vector<SoftDV::LLP>>();
}

std::vector<SoftDV::LLP>
GenProducer::findPattern(const edm::Handle<reco::GenParticleCollection>& gen_particles, const edm::Handle<reco::BeamSpot>& beamspot) const
{
  if (debug)
    std::cout << "GenProducer: start looking for LLP pattern." << std::endl;
  
  bool found = false;
  std::vector<SoftDV::LLP> llps;
  for (size_t i=0; i<gen_particles->size(); ++i) {
    const reco::GenParticle& gen = gen_particles->at(i);
    std::vector<SoftDV::Particle> daus;
    //if (abs(gen.pdgId()) == llp_id && gen.numberOfDaughters() == 3) {
    if (abs(gen.pdgId()) == llp_id) {
      if (!gen.isLastCopy()) continue;
      if (debug)
        std::cout << "llp id: " << gen.pdgId() << " vertex " << gen.vertex().x() << " " << gen.vertex().y() << " " << gen.vertex().z() << std::endl;
      for (size_t j=0; j<gen.numberOfDaughters(); ++j) {
        if (abs(gen.daughter(j)->pdgId())==lsp_id){
          found = true;
        }
        if (gen.daughter(j)->pdgId()==llp_id){
          if (debug){
            std::cout << "!!! Found LLP daughter still the LLP, so discard the previous LLP." << std::endl;
          }
          found = false;
          break;
        }
        SoftDV::Particle dau = SoftDV::Particle(gen.daughter(j)->pdgId(), gen.daughter(j)->charge(), gen.daughter(j)->polarP4(), gen.daughter(j)->vertex());
        daus.push_back(dau);
        if (debug)
          std::cout << "|->  daughter id: " << gen.daughter(j)->pdgId() << " vertex " << gen.daughter(j)->vertex().x() << " " << gen.daughter(j)->vertex().y() << " " << gen.daughter(j)->vertex().z() << std::endl;
      }
    }
    SoftDV::LLP llp = SoftDV::LLP(gen.pdgId(),gen.charge(),gen.polarP4(),gen.vertex(),daus);
    if (!llp.valid()) continue;

    // Look for charged gen particles that originate in the LLP decay
    //const auto& llp_daus = GetDaughters(gen, gen_particles);
    std::queue<reco::GenParticleRef> gen_daughter_queue;
    std::vector<int> processed_gen_key;
    reco::GenParticleCollection llp_daus;
    const auto& llp_ref = reco::GenParticleRef(gen_particles, i);
    std::vector<reco::GenParticle> gtks;

    // This algorithms match LLP decay products by the position of vertices (could ignore b decay)
    if (match_by_dist){
      for (size_t i=0; i<gen_particles->size(); ++i) {
        const reco::GenParticle& gtk = gen_particles->at(i);
        if (gtk.status()!=1) continue;
        if ( (gtk.charge()==0) || (fabs(gtk.charge())<1) ) continue;
        if (gtk.pt()<0.5 || fabs(gtk.eta()) > 2.5 ) continue;
        double r = 88.*gtk.pt();
        double cx = gtk.vx() + gtk.charge() * r * sin(gtk.phi());
        double cy = gtk.vy() - gtk.charge() * r * cos(gtk.phi());
        double dxy_gen = fabs(r-sqrt(pow((cx-( beamspot->x0() )), 2) + pow((cy-( beamspot->y0() )), 2)));
        if (dxy_gen<0.005) continue;
        math::XYZVector dl = gtk.vertex() - llp.decay_point();
        double d3d = std::sqrt(dl.Mag2());
        if (d3d < 0.005){
          gtks.push_back(gtk);
          if (debug){
            std::cout << "  Matched gen track at: " << gtk.vertex().x() << " " << gtk.vertex().y() << " " << gtk.vertex().z() << std::endl;
          }
        }
      }
    }
    if (match_by_daughter){
      gen_daughter_queue.push(llp_ref);
      processed_gen_key.push_back(llp_ref.key());
      while (!gen_daughter_queue.empty()) {
        reco::GenParticleRef dau = gen_daughter_queue.front();
        if (debug) {
          std::cout << "  Daughter " << dau->pdgId() << " status " << dau->status() << " charge " << dau->charge() << std::endl;
        }
        gen_daughter_queue.pop();
        if ( (dau->status()==1) && (dau->charge()!=0)){
          if (dau.isNonnull()){
            llp_daus.push_back(*(dau.get()));
          }
          if (debug){
            std::cout << "  Final status gen daughter added. ID " << dau->pdgId() << " pt " << dau->pt() << " eta " << dau->eta() << " phi " << dau->phi() << std::endl;
          }
          if (dau->numberOfDaughters()>0){
            std::cout << "GenProducer: Gen daughter with status 1 has daughters!" << std::endl;
          }
          continue;
        }
        for (size_t idau=0; idau<dau->numberOfDaughters(); ++idau){
          const auto& gendau = get_gen(dau->daughter(idau), gen_particles);
          int gendau_key = gendau.key();
          if (debug){
            std::cout << "    daughter " << gendau->pdgId() << " status " << gendau->status() << " key " << gendau_key << std::endl;
          }
          if(std::find(processed_gen_key.begin(), processed_gen_key.end(), gendau_key) != processed_gen_key.end()) {
            if (debug)
              std::cout << "     Is was processed before so skipping..." << std::endl;
            continue;
          }
          gen_daughter_queue.push(gendau);
          processed_gen_key.push_back(gendau.key());
        }
      }
      if (debug) {
        std::cout << "Found " << llp_daus.size() << " LLP daughters." << std::endl;
        for (size_t i=0; i<llp_daus.size(); ++i){
          std::cout << "  dau " << i << " ID " << llp_daus[i].pdgId() << " pt " << llp_daus[i].pt() << " eta " << llp_daus[i].eta() << " phi " << llp_daus[i].phi() << std::endl;
        }
      }
      for (size_t i=0; i<llp_daus.size(); ++i){
        if (pass_gtk(llp_daus[i], beamspot)) {
          gtks.push_back(llp_daus[i]);
          if (debug){
            std::cout << "  Matched gen track at: " << llp_daus[i].vertex().x() << " " << llp_daus[i].vertex().y() << " " << llp_daus[i].vertex().z() << std::endl;
          }
        }
      }
    }

    llp.gen_tracks = gtks;

    if (found){
      if (debug)
        std::cout << "LLP saved." << std::endl;
      llps.push_back(llp);
      found = false;
    }
  }
  return llps;
}

reco::GenParticleCollection GenProducer::GetDaughters(const reco::GenParticle& gen, const edm::Handle<reco::GenParticleCollection>& gen_particles) const
{
  std::queue<reco::GenParticle> gen_daughter_queue;
  reco::GenParticleCollection gen_final_daughters;
  return gen_final_daughters;
}

void GenProducer::produce(edm::Event& event, const edm::EventSetup&) {
  std::unique_ptr<std::vector<SoftDV::LLP>> llps(new std::vector<SoftDV::LLP>);
  
  if (!(event.isRealData())){
    edm::Handle<reco::GenParticleCollection> gen_particles;
    event.getByToken(gen_particles_token, gen_particles);

    edm::Handle<reco::BeamSpot> beamspot;
    event.getByToken(beamspot_token, beamspot);

    std::vector<SoftDV::LLP> genllps = findPattern(gen_particles, beamspot);
    for (auto& p: genllps){
      llps->push_back(p);
    }
  }
  event.put(std::move(llps));
}

DEFINE_FWK_MODULE(GenProducer);
