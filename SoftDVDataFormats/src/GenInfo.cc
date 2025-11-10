#include <queue>
#include <algorithm>
#include "SoftDisplacedVertices/SoftDVDataFormats/interface/GenInfo.h"

reco::GenParticleRef SoftDV::get_gen(const reco::Candidate* c, const edm::Handle<reco::GenParticleCollection>& gens) {
  if (c != 0) {
    for (int i = 0, ie = int(gens->size()); i < ie; ++i) {
      const reco::GenParticle& gen = gens->at(i);
      if (&gen == c)
        return reco::GenParticleRef(gens, i);
    }
  }
  return reco::GenParticleRef();
}

SoftDV::DecayMode SoftDV::try_STOP(const reco::GenParticle& gen, bool debug) {
  if (!gen.isLastCopy()) return SoftDV::Undefined;
  if (abs(gen.pdgId())!=1000006) return SoftDV::Undefined;
  if (debug){
    std::cout << "try_STOP for particle " << gen.pdgId() << std::endl;
    std::cout << "Decay products: ";
    for (size_t j=0; j<gen.numberOfDaughters(); ++j) {
      std::cout << gen.daughter(j)->pdgId() << ", ";
    }
    std::cout << std::endl;
  }
  bool found=false;
  for (size_t j=0; j<gen.numberOfDaughters(); ++j) {
    if (abs(gen.daughter(j)->pdgId())==1000022){
      found = true;
    }
    if (abs(gen.daughter(j)->pdgId()) == 1000006){
      if (debug){
        std::cout << "!!! Found LLP daughter still the LLP, so discard the previous LLP." << std::endl;
      }
      found = false;
      break;
    }
  }
  if (!found) return SoftDV::Undefined;
  if (gen.numberOfDaughters()==3) {
    if (debug)
      std::cout << "Found 4 body decay!" << std::endl;
    return SoftDV::STOP_4body;
  }
  if (gen.numberOfDaughters()==2){ 
    if (debug)
      std::cout << "Found 2 body decay!" << std::endl;
    return SoftDV::STOP_2body;
  }
  if (debug)
    std::cout << "Something unexpected!!! N dau " << gen.numberOfDaughters() << std::endl;
  return SoftDV::Undefined;
}

SoftDV::DecayMode SoftDV::try_N2(const reco::GenParticle& gen, bool debug) {
  if (!gen.isLastCopy()) return SoftDV::Undefined;
  if (abs(gen.pdgId())!=1000023) return SoftDV::Undefined;
  if (debug){
    std::cout << "try_N2 for particle " << gen.pdgId() << std::endl;
    std::cout << "Decay products: ";
    for (size_t j=0; j<gen.numberOfDaughters(); ++j) {
      std::cout << gen.daughter(j)->pdgId() << ", ";
    }
    std::cout << std::endl;
  }
  bool found=false;
  SoftDV::DecayMode dm = SoftDV::Undefined;
  std::vector<int> ZorH = {23,25};
  for (size_t j=0; j<gen.numberOfDaughters(); ++j) {
    if (abs(gen.daughter(j)->pdgId())==1000022){
      found = true;
    }
    else{
      for (auto& f : ZorH) {
        if (abs(gen.daughter(j)->pdgId())==f) {
          std::vector<const reco::Candidate*> daus;
          daus.push_back(gen.daughter(j));
          //auto& dau = SoftDV::get_gen(gen.daughter(j), gen_particles);
          bool foundItself=true;
          while (foundItself) {
            foundItself=false;
            const reco::Candidate* dau = daus[0];
            if (debug)
              std::cout << "dau " << dau->pdgId() << " : ";
            for (size_t jj=0; jj<dau->numberOfDaughters(); ++jj) {
              if (debug)
                std::cout << dau->daughter(jj)->pdgId() << ", ";
              if (abs(dau->daughter(jj)->pdgId())==f){
                foundItself=true;
                //dau = SoftDV::get_gen(dau->daughter(jj), gen_particles);
                daus.pop_back();
                daus.push_back(dau->daughter(jj));
              }
            }
            if (debug)
              std::cout << std::endl;
          }
          const reco::Candidate* dau = daus[0];
          if (debug){
            std::cout << "Daughter Decay products: ";
            for (size_t jj=0; jj<dau->numberOfDaughters(); ++jj) {
              std::cout << dau->daughter(jj)->pdgId() << ", ";
            }
            std::cout << std::endl;
          }
          for (size_t jj=0; jj<dau->numberOfDaughters(); ++jj) {
            if (abs(dau->daughter(jj)->pdgId())==5){
              if (f==23){
                dm = SoftDV::N2_Zbb;
              }
              else if (f==25){
                dm = SoftDV::N2_Hbb;
              }
            }
            else if (abs(dau->daughter(jj)->pdgId())<5){
              if (f==23){
                dm = SoftDV::N2_Zqq;
              }
              else if (f==25){
                dm = SoftDV::N2_Hqq;
              }
            }
            else {
              if (f==23){
                dm = SoftDV::N2_Zll;
              }
              else if (f==25){
                dm = SoftDV::N2_Hll;
              }
            }
          }
        }
      }
    }
    if (abs(gen.daughter(j)->pdgId()) == 1000023){
      if (debug){
        std::cout << "!!! Found LLP daughter still the LLP, so discard the previous LLP." << std::endl;
      }
      found = false;
      break;
    }
  }
  if (!found) return SoftDV::Undefined;
  if (debug)
    std::cout << "Found decay mode " << dm << std::endl;
  return dm;
}

std::pair<std::vector<int>,std::vector<int>> SoftDV::FindLLP(const edm::Handle<reco::GenParticleCollection>& gen_particles, bool debug){
  if (debug)
    std::cout << "Start looking for LLP." << std::endl;

  std::vector<int> llps;
  std::vector<int> llps_decay_mode;
  for (size_t i=0; i<gen_particles->size(); ++i) {
    const reco::GenParticle& gen = gen_particles->at(i);
    SoftDV::DecayMode stop_mode = try_STOP(gen,debug);
    SoftDV::DecayMode c1n2_mode = try_N2(gen,debug);
    if (stop_mode>SoftDV::Undefined || c1n2_mode>SoftDV::Undefined){
      if (debug)
        std::cout << "LLP with decay mode " << c1n2_mode+stop_mode << " found." << std::endl;
      llps.push_back(i);
      if (stop_mode>SoftDV::Undefined){
        llps_decay_mode.push_back(stop_mode);
      }
      else{
        llps_decay_mode.push_back(c1n2_mode);
      }
    }
  }

  if (debug){
    std::cout << "Total LLPs: " << llps.size() << std::endl;
  }
  return std::pair<std::vector<int>,std::vector<int>>({llps,llps_decay_mode});
  
}

std::vector<int> SoftDV::GetDaughters(const size_t igen, const edm::Handle<reco::GenParticleCollection>& gen_particles, bool debug) {
  const reco::GenParticle gen = gen_particles->at(igen);
  std::queue<reco::GenParticleRef> gen_daughter_queue;
  std::vector<int> processed_gen_key;
  std::vector<int> llp_daus;
  //reco::GenParticleCollection llp_daus;
  std::vector<reco::GenParticle> gtks;

  // Use GenParticleRef to check duplication
  //const auto& llp_ref = reco::GenParticleRef(gen_particles, i);
  if (debug)
    std::cout << "Start looking for daughters." << std::endl;
  //const auto& llp_ref = SoftDV::get_gen(&gen, gen_particles);
  const auto& llp_ref = reco::GenParticleRef(gen_particles, igen);
  if (debug)
    std::cout << "Get LLP reference." << std::endl;
  if (!llp_ref)
    std::cout << "CANNOT FIND LLP REFERENCE!" << std::endl;
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
        llp_daus.push_back(dau.key());
        //llp_daus.push_back(*(dau.get()));
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
      const auto& gendau = SoftDV::get_gen(dau->daughter(idau), gen_particles);
      if (!gendau)
        continue;
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
  return llp_daus;

}

std::map<std::vector<double>,std::vector<int>> SoftDV::ClusterGenParts(const std::vector<int> parts, const edm::Handle<reco::GenParticleCollection>& gen_particles) {
  std::map<std::vector<double>,std::vector<int>> clusters;
  for (const auto& p : parts) {
    const reco::GenParticle gen = gen_particles->at(p);
    std::vector<double> v = {gen.vx(),gen.vy(),gen.vz()};
    if (clusters.find(v)==clusters.end()) {
      bool found_close = false;
      for (auto it=clusters.begin(); it!=clusters.end(); ++it){
        std::vector<double> nv = it->first;
        double dist = sqrt(pow(v[0]-nv[0],2)+pow(v[1]-nv[1],2)+pow(v[2]-nv[2],2));
        if (dist<0.005){
          clusters[nv].push_back(p);
          break;
        }
      }
      if (!found_close)
        clusters[v] = {p};
    }
    else {
      clusters[v].push_back(p);
    }
  }
  return clusters;
}

SoftDV::MatchResult SoftDV::matchtracks(const reco::GenParticle& gtk, const edm::Handle<reco::TrackCollection>& tracks, const SoftDV::Point& refpoint) {
  SoftDV::Match min_match(-1,std::vector<double>());
  int tk_idx = -1;
  for (size_t i=0; i<tracks->size(); ++i){
    reco::TrackRef tk(tracks, i);
    SoftDV::Match match = SoftDV::matchchi2(gtk,tk,refpoint);
    if ( ( (min_match.first==-1 || match.first<min_match.first) && match.second[0]<0.2 && match.second[1]<3) ){
    //if (match.first<min_match.first && match.second[0]<0.2){
    //if ( (min_match.first==-1) || (match.first<min_match.first) ) {
      min_match = match;
      tk_idx = i;
    }
  }
  return SoftDV::MatchResult(tk_idx,min_match);

}

SoftDV::Match SoftDV::matchchi2(const reco::GenParticle& gtk, const reco::TrackRef& rtk, const SoftDV::Point& refpoint) {
  //double dxy = gen_dxy_reco(gtk,refpoint);
  double dxy = gen_dxy(gtk,refpoint);
  double dz = gen_dz(gtk,refpoint);

  std::vector<double> a;
  a.push_back( ( fabs(rtk->dxy(refpoint)) - fabs(dxy) ) / rtk->dxyError() );
  a.push_back( ( rtk->dz(refpoint)- dz ) / (4*rtk->dzError()) );
  a.push_back( ( rtk->charge()/rtk->pt() - gtk.charge()/gtk.pt()) / (1.0/rtk->ptError()) );
  double dr = reco::deltaR(rtk->eta(), rtk->phi(), gtk.eta(), gtk.phi());
  a.push_back(dr/0.01);
  double asum = 0;
  for (double& xa:a){
    asum += xa*xa;
  }
  std::vector<double> m({dr,fabs( fabs(rtk->dxy(refpoint)) - fabs(dxy) ) / rtk->dxyError()});
  return std::pair<double,std::vector<double>>(0.25*asum,m);
}

bool SoftDV::pass_gentk(const reco::GenParticle& gtk, const SoftDV::Point& refpoint){
  if (gtk.status()!=1) return false;
  if ( (gtk.charge()==0) || (fabs(gtk.charge())<1) ) return false;
  if (gtk.pt()<0.5 || fabs(gtk.eta()) > 2.5 ) return false;
  double dxy_gen = gen_dxy(gtk,refpoint);
  if (dxy_gen<0.005) return false;

  return true;  
}

// The VtxLLPMatch function matches reco vertices with LLPs
// A map is returned: 
//   Key: vertex index
//   Value: a std::pair of (matched LLP index, number of matched tracks)
std::map<int,std::pair<int,int>> SoftDV::VtxLLPMatch(const edm::Handle<reco::GenParticleCollection>& genPart, const edm::Handle<reco::VertexCollection>& vertices, const edm::Handle<reco::TrackCollection>& tracks, const SoftDV::Point& refpoint, bool debug) {
  std::map<int,std::pair<int,int>> res;
  // Get all LLPs
  std::vector<int> llp_idx = SoftDV::FindLLP(genPart, debug).first;
  std::map<int,std::vector<int>> tk_llp_map; // first element is track key; second element is a vector of indices of matched LLPs
  for (size_t illp=0; illp<llp_idx.size(); ++illp){
    std::vector<int> llp_daus = SoftDV::GetDaughters(llp_idx[illp], genPart, debug);
    // Match Gen daughters with reco tracks
    for (int igen:llp_daus) {
      const reco::GenParticle& idau = genPart->at(igen);
      const auto matchres = SoftDV::matchtracks(idau, tracks, refpoint);
      if (matchres.first != -1) {
        reco::TrackRef itk = reco::TrackRef(tracks, matchres.first);
        if (tk_llp_map.find(itk.key())!=tk_llp_map.end() && std::find(tk_llp_map[itk.key()].begin(),tk_llp_map[itk.key()].end(),illp)!=tk_llp_map[itk.key()].end()) {
          if (debug)
            std::cout << " LLP " << illp << " already matched with tk " << itk.key() << std::endl;
          continue;
        }
        tk_llp_map[itk.key()].push_back(illp);
        if (debug){
          std::cout << " matched with track " << itk.key() << std::endl;
        }
      }
    }
  }
  if (debug){
    std::cout << "Track LLP match map:" << std::endl;
    for (auto mit = tk_llp_map.begin(); mit!=tk_llp_map.end(); ++mit) {
      std::cout << " tk " << mit->first << " LLP ";
      for (auto e:mit->second){
        std::cout << e << ", ";
      }
      std::cout << std::endl;
    }
  }
  // Now loop through vertices
  for (size_t ivtx=0; ivtx<vertices->size(); ++ivtx){
    const reco::Vertex& sv = vertices->at(ivtx);
    // A vector that stores the number of matched tracks for each LLP
    std::vector<int> nmatchtk(llp_idx.size(),0);
    if (debug)
      std::cout << "vtx tks: ";
    for (auto v_tk = sv.tracks_begin(), vtke = sv.tracks_end(); v_tk != vtke; ++v_tk){
      int tkkey = (*v_tk).key();
      if (debug)
        std::cout << tkkey << ", ";
      //const auto& otk = tracks->at(tkkey);
      // If a track is matched with LLP, increment the corresponding number in the vector
      if (tk_llp_map.find(tkkey)!=tk_llp_map.end()) {
        for (auto& imllp:tk_llp_map[tkkey]){
          nmatchtk[imllp] += 1;
        }
      }
    }
    if (debug)
      std::cout << std::endl;
    if (nmatchtk.size()==0){
      // return -1 for background
      res[ivtx] = std::pair<int,int>(-1,0);
    }
    else{
      // Pick the LLP that have most number of matched track with the vertex as matched LLP
      int matchllp_idx = std::max_element(nmatchtk.begin(),nmatchtk.end())-nmatchtk.begin();
      if (nmatchtk[matchllp_idx]>0){
        res[ivtx] = std::pair<int,int>(matchllp_idx,nmatchtk[matchllp_idx]);
      }
    }
  }
  return res;
}

double gen_dxy(const reco::GenParticle& gtk, const SoftDV::Point& refpoint){
  // calculate dxy for gen track
  double r = 88.*gtk.pt();
  double cx = gtk.vx() + gtk.charge() * r * sin(gtk.phi());
  double cy = gtk.vy() - gtk.charge() * r * cos(gtk.phi());
  double dxy = fabs(r-sqrt(pow((cx-( refpoint.x() )), 2) + pow((cy-( refpoint.y() )), 2)));

  return dxy;
}

double gen_dz(const reco::GenParticle& gtk, const SoftDV::Point& refpoint) {
  double rz = sqrt(pow((gtk.vx()-( refpoint.x() )), 2) + pow((gtk.vy()-( refpoint.y() )), 2));
  double z = gtk.vz() - refpoint.z();
  double dz = z-rz*(gtk.pz()/gtk.pt());

  return dz;
}

double gen_dxy_reco(const reco::GenParticle& gtk, const SoftDV::Point& refpoint) {
  return (-(gtk.vx() - refpoint.x()) * gtk.py() + (gtk.vy() - refpoint.y()) * gtk.px()) / gtk.pt();
}

Measurement1D gen_dist(const reco::Vertex& sv, const SoftDV::Point& gen, const bool use3d) {
  math::XYZPoint sv_pos = sv.position();
  math::XYZVector l_sv_gen = sv_pos - gen;
  double d = sqrt(l_sv_gen.Mag2());
  AlgebraicVector3 v(sv.x(), sv.y(), use3d ? sv.z() : 0);
  const double dist2 = ROOT::Math::Mag2(v);
  const double sim  = ROOT::Math::Similarity(v, sv.covariance());
  const double ed = dist2 != 0 ? sqrt(sim/dist2) : 0;
  return Measurement1D(d, ed);
}
