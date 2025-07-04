#include <memory>
#include <vector>
#include <set>
#include <algorithm>
#include <iostream>

#include "TTree.h"
#include "TMath.h"

#include "FWCore/Framework/interface/Event.h"
#include "FWCore/Framework/interface/Frameworkfwd.h"
#include "FWCore/Framework/interface/MakerMacros.h"
#include "FWCore/ServiceRegistry/interface/Service.h"
#include "CommonTools/UtilAlgos/interface/TFileService.h"
#include "FWCore/Framework/interface/stream/EDProducer.h"
#include "FWCore/Framework/interface/one/EDProducer.h"
#include "FWCore/ParameterSet/interface/ParameterSet.h"
#include "DataFormats/TrackReco/interface/Track.h"
#include "DataFormats/TrackReco/interface/TrackFwd.h"
#include "DataFormats/VertexReco/interface/Vertex.h"
#include "DataFormats/VertexReco/interface/VertexFwd.h"
#include "SoftDisplacedVertices/SoftDVDataFormats/interface/PFIsolation.h"
#include "TrackingTools/Records/interface/TransientTrackRecord.h"
#include "TrackingTools/TransientTrack/interface/TransientTrack.h"
#include "TrackingTools/TransientTrack/interface/TransientTrackBuilder.h"
#include "RecoVertex/VertexPrimitives/interface/TransientVertex.h"
#include "RecoVertex/ConfigurableVertexReco/interface/ConfigurableVertexReconstructor.h"
#include "RecoVertex/KalmanVertexFit/interface/KalmanVertexFitter.h"
#include "DataFormats/HepMCCandidate/interface/GenParticle.h"
#include "SoftDisplacedVertices/SoftDVDataFormats/interface/GenInfo.h"

#include "PhysicsTools/ONNXRuntime/interface/ONNXRuntime.h"

struct eventInfo
{
  int ntk;
  int ntk_clus;
  int ntk_llp;
  int ntk_clus_llp;
  std::vector<int> clus_ntk;
  std::vector<float> clus_mass;
  std::vector<int> clus_llpidx;
  std::vector<int> clus_ntk_match;
  std::vector<int> clus_nGoodTrack;
  std::vector<int> llp_ntk;
  std::vector<int> llp_ntk_match;
  std::vector<float> llp_lxy;
  std::vector<float> llp_closest_genv_dist;
  std::vector<float> llp_closest_genv_dist_z;
  std::vector<float> llp_closest_genv_dist_2d;
  std::vector<float> llp_min_vtx_normchi2;
  std::vector<int> llp_matched;
  std::vector<int> llp_matched_vtx;
  std::vector<int> vtx_matched;
  std::vector<float> vtx_chi2;
  std::vector<float> vtx_normchi2;
  std::vector<float> vtx_genvdist;
  std::vector<float> vtx_genvdist_z;
  std::vector<float> vtx_genvdist_2d;
};

class Graph {
  public:
    int numVertices;
    std::vector<std::set<int>> adjList;
    std::vector<std::set<int>> cliques;

    Graph(int vertices) : numVertices(vertices), adjList(vertices), cliques() {}

    void addEdge(int u, int v) {
      adjList[u].insert(v);
      adjList[v].insert(u);
    }

    std::vector<std::set<int>> getCliques() {
      if (cliques.size()!=0)
        throw cms::Exception("GNNInterface") << "Non-empty cliques before searching!";
      std::set<int> R, P, X;
      for (int i=0; i < numVertices; ++i) {
        P.insert(i);
      }
      bronKerboschWithPivot(R,P,X);
      return cliques;
    }

    void bronKerboschWithPivot(std::set<int> R, std::set<int> P, std::set<int> X) {
      if (P.empty() && X.empty()) {
        if (R.size()>1)
          cliques.push_back(R);
        // Print maximal clique
        //for (int v : R) {
        //  std::cout << v << " ";
        //}
        //std::cout << std::endl;
        return;
      }
      int u = *P.begin();  // Choosing the first vertex in P as the pivot
      std::set<int> P_diff;

      // P \ N(u)
      for (int v : P) {
          if (adjList[u].find(v) == adjList[u].end()) {
              P_diff.insert(v);
          }
      }

      std::set<int> P_copy = P_diff;  // Create a copy to iterate over
      for (int v : P_copy) {
          std::set<int> R_new = R;
          R_new.insert(v);
          std::set<int> P_new, X_new;

          for (int neighbor : adjList[v]) {
              if (P.find(neighbor) != P.end()) {
                  P_new.insert(neighbor);
              }
              if (X.find(neighbor) != X.end()) {
                  X_new.insert(neighbor);
              }
          }

          bronKerboschWithPivot(R_new, P_new, X_new);

          P.erase(v);
          X.insert(v);
      }
    }
};


using namespace cms::Ort;
typedef std::vector<std::unique_ptr<ONNXRuntime>> NNArray;

class GNNDisplay: public edm::one::EDProducer<edm::one::SharedResources> {
  public:
    explicit GNNDisplay(const edm::ParameterSet &);

  private:
    void beginJob();
    void produce(edm::Event&, const edm::EventSetup&) override;

    void initEventStructure();

    float edge_dist(std::vector<float> v1, std::vector<float> v2);
    std::vector<float> track_input(reco::TrackRef tk, const reco::Vertex* pv, SoftDV::PFIsolation isoDR03);
    bool v_pass(const reco::Vertex& v, const reco::Vertex* pv);
    std::unique_ptr<NNArray> initializeNNs(const edm::ParameterSet &);
    bool isGoodTrack(reco::TrackRef tk, const reco::Vertex* pv, SoftDV::PFIsolation isoDR03);

    std::vector<std::string> input_names_emb_;
    std::vector<std::string> input_names_gnn_;
    std::vector<std::vector<int64_t>> input_shapes_;
    const edm::EDGetTokenT<reco::VertexCollection> primary_vertex_token;
    const edm::EDGetTokenT<reco::TrackCollection> tracks_token;
    edm::EDGetTokenT<std::vector<SoftDV::PFIsolation>> isoDR03Token_;
    //FloatArrays data_; // each stream hosts its own data
    //
    double edge_dist_cut_;
    double edge_gnn_cut_;
    const edm::EDGetTokenT<std::vector<reco::GenParticle>> genToken_;

    std::unique_ptr<VertexReconstructor> vtxReco;

    TTree *eventTree;
    eventInfo *evInfo;

    std::unique_ptr<NNArray> NNs;
};

GNNDisplay::GNNDisplay(const edm::ParameterSet &iConfig)
  : input_names_emb_(iConfig.getParameter<std::vector<std::string>>("input_names_emb")),
    input_names_gnn_(iConfig.getParameter<std::vector<std::string>>("input_names_gnn")),
    input_shapes_(),
    primary_vertex_token(consumes<reco::VertexCollection>(iConfig.getParameter<edm::InputTag>("primary_vertex_token"))),
    tracks_token(consumes<reco::TrackCollection>(iConfig.getParameter<edm::InputTag>("tracks"))),
    isoDR03Token_(consumes<std::vector<SoftDV::PFIsolation>>(iConfig.getParameter<edm::InputTag>("isoDR03"))),
    edge_dist_cut_(iConfig.getParameter<double>("edge_dist_cut")),
    edge_gnn_cut_(iConfig.getParameter<double>("edge_gnn_cut")),
    genToken_(consumes<std::vector<reco::GenParticle>>(iConfig.getParameter<edm::InputTag>("gen"))),
    //kv_reco(new KalmanVertexFitter(iConfig.getParameter<edm::ParameterSet>("kvr_params"), iConfig.getParameter<edm::ParameterSet>("kvr_params").getParameter<bool>("doSmoothing")))
    vtxReco(new ConfigurableVertexReconstructor(iConfig.getParameter<edm::ParameterSet>("vtx_params"))){
    usesResource("TFileService");
    evInfo = new eventInfo;
    //NNs = initializeNNs(iConfig);
    NNs = std::make_unique<NNArray>();
    NNs->push_back(std::make_unique<ONNXRuntime>(iConfig.getParameter<edm::FileInPath>("EMB_model_path").fullPath()));
    NNs->push_back(std::make_unique<ONNXRuntime>(iConfig.getParameter<edm::FileInPath>("GNN_model_path").fullPath()));
    produces<reco::GenParticleCollection>("LLPdecays");
    produces<reco::TrackCollection>("LLPmatched");
    produces<reco::TrackCollection>("GNN");
    }

std::unique_ptr<NNArray> GNNDisplay::initializeNNs(const edm::ParameterSet &iConfig) {
  std::unique_ptr<NNArray> NNs = std::make_unique<NNArray>();
  NNs->push_back(std::make_unique<ONNXRuntime>(iConfig.getParameter<edm::FileInPath>("EMB_model_path").fullPath()));
  NNs->push_back(std::make_unique<ONNXRuntime>(iConfig.getParameter<edm::FileInPath>("GNN_model_path").fullPath()));
  return NNs;
}

void GNNDisplay::produce(edm::Event &iEvent, const edm::EventSetup &iSetup) {
  initEventStructure();

  std::unique_ptr<reco::GenParticleCollection> genpart_llpdecay(new reco::GenParticleCollection);
  std::unique_ptr<reco::TrackCollection> tk_llpmatched(new reco::TrackCollection);
  std::unique_ptr<reco::TrackCollection> tk_gnn(new reco::TrackCollection);

  edm::Handle<reco::TrackCollection> tracks;
  iEvent.getByToken(tracks_token, tracks);

  edm::Handle<reco::VertexCollection> primary_vertices;
  iEvent.getByToken(primary_vertex_token, primary_vertices);
  const reco::Vertex* primary_vertex = &primary_vertices->at(0);
  if (primary_vertices->size()==0)
    throw cms::Exception("GNNInterface") << "No Primary Vertices available!";

  edm::Handle<std::vector<SoftDV::PFIsolation>> tracks_isoDR03;
  iEvent.getByToken(isoDR03Token_, tracks_isoDR03);
  if (tracks->size() != tracks_isoDR03->size())
    throw cms::Exception("GNNDisplay") << "Tracks mismatch with track IsoDR03!";

  edm::Handle<reco::GenParticleCollection> genParticles;
  iEvent.getByToken(genToken_, genParticles);

  edm::ESHandle<TransientTrackBuilder> tt_builder;
  iSetup.get<TransientTrackRecord>().get("TransientTrackBuilder", tt_builder);

  // Get Gen info
  std::pair<std::vector<int>,std::vector<int>> llp_idx_dm = SoftDV::FindLLP(genParticles, false);
  std::vector<int> llp_idx = llp_idx_dm.first;
  std::vector<int> llp_decaymdoe = llp_idx_dm.second;
  std::vector<std::set<int>> llp_track_idx;
  std::vector<std::set<reco::TrackRef>> llp_track_refs;
  std::set<int> llp_all_track;
  std::map<int,std::vector<float>> tk_genv_pos;
  std::map<reco::TrackRef,std::vector<float>> tkref_genv_pos;
  for (auto& illp : llp_idx) {
    std::set<int> tk_idx;
    std::set<reco::TrackRef> tk_refs;
    std::set<int> matched_dau_idx;
    const reco::GenParticle& llp = genParticles->at(illp);
    genpart_llpdecay->push_back(llp);
    auto decay_point = llp.daughter(0)->vertex();
    float llp_lxy = std::hypot(decay_point.x()-primary_vertex->x(), decay_point.y()-primary_vertex->y());
    std::vector<int> llp_daus = SoftDV::GetDaughters(illp, genParticles, false);
    for (int igen:llp_daus){
      const reco::GenParticle& idau = genParticles->at(igen);
      if (SoftDV::pass_gentk(idau, primary_vertex->position())){
        genpart_llpdecay->push_back(idau);
      }
      const auto matchres = SoftDV::matchtracks(idau, tracks, primary_vertex->position());
      if (matchres.first!=-1) {
        const reco::Track& itk = tracks->at(matchres.first);
        tk_llpmatched->push_back(itk);
        reco::TrackRef mtk(tracks, matchres.first);
        tk_refs.insert(mtk);
        tk_idx.insert(matchres.first);
        llp_all_track.insert(matchres.first);
        matched_dau_idx.insert(igen);
        tk_genv_pos[matchres.first] = std::vector<float>({(float)idau.vx(),(float)idau.vy(),(float)idau.vz()});
        tkref_genv_pos[mtk] = std::vector<float>({(float)idau.vx(),(float)idau.vy(),(float)idau.vz()});
      }
    }
    std::vector<int> matched_dau_idx_v(matched_dau_idx.begin(),matched_dau_idx.end());
    double d_min = 999;
    double d_min_2d = 999;
    double d_min_z = 999;
    for (size_t ig=0;ig<matched_dau_idx_v.size();++ig){
      for(size_t jg=ig+1;jg<matched_dau_idx_v.size();++jg){
        const reco::GenParticle& idau = genParticles->at(matched_dau_idx_v[ig]);
        const reco::GenParticle& jdau = genParticles->at(matched_dau_idx_v[jg]);
        double tempd = std::hypot(idau.vx()-jdau.vx(),idau.vy()-jdau.vy(),idau.vz()-jdau.vz());
        if (d_min>tempd) {
          d_min = tempd;
          d_min_2d = std::hypot(idau.vx()-jdau.vx(),idau.vy()-jdau.vy());
          d_min_z = fabs(idau.vz()-jdau.vz());
        }
      }
    }
    llp_track_idx.push_back(tk_idx);
    llp_track_refs.push_back(tk_refs);
    evInfo->llp_ntk.push_back(tk_idx.size());
    evInfo->ntk_llp += tk_idx.size();
    evInfo->llp_lxy.push_back(llp_lxy);
    evInfo->llp_closest_genv_dist.push_back((float)d_min);
    evInfo->llp_closest_genv_dist_z.push_back((float)d_min_z);
    evInfo->llp_closest_genv_dist_2d.push_back((float)d_min_2d);
  }
  if (llp_track_idx.size()!=2){
    throw cms::Exception("GNNDisplay") << "llp_track_idx.size incorrect!";
  }
  int nllp =llp_track_idx.size(); 

  int ntks = tracks->size();
  evInfo->ntk = ntks;
  evInfo->llp_matched = std::vector<int>(nllp,0);

  if (ntks==0) {
    iEvent.put(std::move(genpart_llpdecay), "LLPdecays"); 
    iEvent.put(std::move(tk_llpmatched), "LLPmatched");
    iEvent.put(std::move(tk_gnn), "GNN");
    return;
  }
  int n_features = 0;
  FloatArrays inputdata;
  std::vector<float> tks_vars;
  for (int i=0; i<ntks; ++i){
    SoftDV::PFIsolation isoDR03 = (*tracks_isoDR03)[i];
    reco::TrackRef tk(tracks, i);
    std::vector<float> tk_vars = track_input(tk,primary_vertex,isoDR03);
    n_features = tk_vars.size();
    tks_vars.insert(tks_vars.end(),tk_vars.begin(),tk_vars.end());
  }
  inputdata.push_back(tks_vars);

  std::vector<std::vector<int64_t>> tk_shape = {{ntks,n_features}};

  std::vector<float> emb = NNs->at(0)->run(input_names_emb_, inputdata, tk_shape, {}, ntks)[0];

  std::vector<int> sender_idx;
  std::vector<int> receiver_idx;
  std::vector<float> distance;

  for (int i=0;i<ntks;++i){
    for (int j=0;j<ntks;++j){
      if (i==j) continue;
      std::vector<float> emb_i(emb.begin()+i*16,emb.begin()+(i+1)*16);
      std::vector<float> emb_j(emb.begin()+j*16,emb.begin()+(j+1)*16);
      float d2 = edge_dist(emb_i,emb_j);
      if (d2<0.02){ // FIXME: the cut value on d2 should be revisited
        sender_idx.push_back(i);
        receiver_idx.push_back(j);
        distance.push_back(d2);
      }
    }
  }

  FloatArrays input_GNN;
  std::vector<std::vector<int64_t>> input_shape_GNN;
  input_GNN.push_back(tks_vars);
  input_shape_GNN.push_back({1,ntks,n_features});
  std::vector<float> edge_idx;
  int64_t n_edges = sender_idx.size();
  edge_idx.insert(edge_idx.end(),sender_idx.begin(),sender_idx.end());
  edge_idx.insert(edge_idx.end(),receiver_idx.begin(),receiver_idx.end());
  input_GNN.push_back(edge_idx);
  input_shape_GNN.push_back({1,2,n_edges});

  std::vector<float> gnn = NNs->at(1)->run(input_names_gnn_, input_GNN, input_shape_GNN, {}, 1)[0];

  if (gnn.size() != distance.size()) 
    throw cms::Exception("GNNInterface") << "Embedding distance and GNN prediction doesn't match!";

  // Select edges based on distance and gnn score
  std::vector<std::pair<int,int>> edges;
  for (int i=0; i<n_edges; ++i) {
    if ( (distance[i] > edge_dist_cut_) || (gnn[i] < edge_gnn_cut_) )
      continue;
    edges.push_back(std::pair<int,int>({sender_idx[i],receiver_idx[i]}));
  }

  // Remove single directed edges
  Graph track_g(ntks);
  for (size_t i=0; i<edges.size(); ++i) {
    if (edges[i].first>edges[i].second)
      continue;
    std::pair<int,int> inverse_edge({edges[i].second,edges[i].first});
    if (std::find(edges.begin(),edges.end(),inverse_edge) != edges.end()) {
      track_g.addEdge(edges[i].first,edges[i].second);
    }
  }

  std::vector<std::set<int> > clus = track_g.getCliques();
  std::set<int> clus_tk;
  std::vector<std::vector<int>> nmatches;
  std::vector<std::set<int>> llp_tk_matched;
  for (int illp=0; illp<nllp; ++illp) {
    llp_tk_matched.push_back(std::set<int>());
  }
  for (auto& ic : clus) {
    evInfo->ntk_clus += ic.size();
    evInfo->clus_ntk.push_back(ic.size());
    std::vector<int> nmatch(nllp,0);
    int ntkmatch = 0;
    int nGoodTrack = 0;
    math::XYZTLorentzVectorD sum;
    ROOT::Math::LorentzVector<ROOT::Math::PxPyPzM4D<double> > vec;
    //std::vector<reco::TransientTrack> seed_tracks;
    for (int itk : ic){
      clus_tk.insert(itk);
      SoftDV::PFIsolation isoDR03 = (*tracks_isoDR03)[itk];
      reco::TrackRef tk(tracks, itk);
      vec.SetPx(tk->px());
      vec.SetPy(tk->py());
      vec.SetPy(tk->pz());
      vec.SetM(0.13957018);
      sum += vec;
      if (isGoodTrack(tk,primary_vertex,isoDR03))
        nGoodTrack += 1;
      bool matched = false;
      for (int illp=0; illp<nllp; ++illp){
        auto tkmatchres = std::find(llp_track_idx[illp].begin(),llp_track_idx[illp].end(),itk);
        if(tkmatchres!=llp_track_idx[illp].end()){
          nmatch[illp] += 1;
          matched = true;
          llp_tk_matched[illp].insert(itk); 
        }
      }
      if (matched)
        ntkmatch += 1;
      //reco::TrackRef tk(tracks, itk);
      //seed_tracks.push_back(tt_builder->build(tk));
    }
    nmatches.push_back(nmatch);
    evInfo->clus_mass.push_back(sum.M());
    evInfo->clus_ntk_match.push_back(ntkmatch);
    evInfo->clus_nGoodTrack.push_back(nGoodTrack);
    if ( (nmatch[0]>1) && (nmatch[1]>1)) {
      evInfo->clus_llpidx.push_back(3);
      evInfo->llp_matched[0] = 1;
      evInfo->llp_matched[1] = 1;
    }
    else if (nmatch[0]>1) {
      evInfo->clus_llpidx.push_back(0);
      evInfo->llp_matched[0] = 1;
    }
    else if (nmatch[1]>1) {
      evInfo->clus_llpidx.push_back(1);
      evInfo->llp_matched[1] = 1;
    }

    //std::vector<TransientVertex> vs = vtxReco->vertices(seed_tracks);
    //for (auto& v : vs) {
    //  if (v.isValid()){
    //    vertices->push_back(v);
    //  }
    //}
  }

  evInfo->llp_matched_vtx = std::vector<int>(nllp,0);
  evInfo->llp_min_vtx_normchi2 = std::vector<float>(nllp,std::numeric_limits<float>::infinity());
  std::map<int,reco::TransientTrack> ttk_map;
  std::map<reco::TrackRef,reco::TransientTrack> ttk_ref_map;
  for (int itk:clus_tk) {
    const reco::Track& ictk = tracks->at(itk);
    tk_gnn->push_back(ictk);
    reco::TrackRef tk(tracks, itk);
    ttk_map[itk] = tt_builder->build(tk);
    ttk_ref_map[tk] = tt_builder->build(tk);
  }

  std::vector<reco::Vertex> vtxs;
  for (auto& ic : clus) {
    std::vector<int> vtks(ic.begin(),ic.end());
    math::XYZTLorentzVectorD sum;
    ROOT::Math::LorentzVector<ROOT::Math::PxPyPzM4D<double> > vec;
    //std::vector<reco::TransientTrack> seed_tracks;
    for (int itk : vtks){
      reco::TrackRef tk(tracks, itk);
      vec.SetPx(tk->px());
      vec.SetPy(tk->py());
      vec.SetPy(tk->pz());
      vec.SetM(0.13957018);
      sum += vec;
    }
    //if ( (sum.M()<0.5) || (vtks.size()<3) )
    //  continue;
    int nst = vtks.size();
    for (int iist=0; iist<nst; ++iist){
      for (int jjst=iist+1; jjst<nst; ++jjst){
        int ist = vtks[iist];
        int jst = vtks[jjst];
        reco::TrackRef ist_ref (tracks, ist);
        reco::TrackRef jst_ref (tracks, jst);
        if (ttk_ref_map.find(ist_ref)==ttk_ref_map.end())
          throw cms::Exception("GNNDisplay") << "Track index " << ist << " not found in map!";
        if (ttk_ref_map.find(jst_ref)==ttk_ref_map.end())
          throw cms::Exception("GNNDisplay") << "Track index " << jst << " not found in map!";
        std::vector<reco::TransientTrack> track_pairs({ttk_ref_map[ist_ref],ttk_ref_map[jst_ref]});
        std::vector<TransientVertex> vs = vtxReco->vertices(track_pairs);
        for (auto & v: vs) {
          const reco::Vertex nv(v);
          std::cout << "Vertex: chi2 " << nv.chi2() << " normchi2 " << nv.normalizedChi2() << std::endl;
          std::cout << "  Tk1 pt " << ist_ref->pt() << " eta " << ist_ref->eta() << " phi " << ist_ref->phi() << std::endl;
          std::cout << "  Tk2 pt " << jst_ref->pt() << " eta " << jst_ref->eta() << " phi " << jst_ref->phi() << std::endl;
          if (v_pass(nv,primary_vertex)){
            bool matched = false;
            for(int illp=0; illp<nllp; ++illp) {
              auto itkmatchres = std::find(llp_track_idx[illp].begin(),llp_track_idx[illp].end(),ist);
              auto jtkmatchres = std::find(llp_track_idx[illp].begin(),llp_track_idx[illp].end(),jst);
              if ( (itkmatchres!=llp_track_idx[illp].end()) and (jtkmatchres!=llp_track_idx[illp].end())) {
                evInfo->llp_matched_vtx[illp] = 1;
                matched = true;
                evInfo->llp_min_vtx_normchi2[illp] = std::min(v.normalisedChiSquared(),evInfo->llp_min_vtx_normchi2[illp]);
              }
            }
            float d = -1;
            float d_2d = -1;
            float d_z = -1;
            if (matched){
              if (tk_genv_pos.find(ist)==tk_genv_pos.end())
                throw cms::Exception("GNNDisplay") << "Track index " << ist << " not found in map!";
              if (tk_genv_pos.find(jst)==tk_genv_pos.end())
                throw cms::Exception("GNNDisplay") << "Track index " << jst << " not found in map!";
              d = std::sqrt(edge_dist(tk_genv_pos[ist],tk_genv_pos[jst]));
              d_2d = std::hypot(tk_genv_pos[ist][0]-tk_genv_pos[jst][0],tk_genv_pos[ist][1]-tk_genv_pos[jst][1]);
              d_z = fabs(tk_genv_pos[ist][2]-tk_genv_pos[jst][2]);
            }
            evInfo->vtx_chi2.push_back(v.totalChiSquared());
            evInfo->vtx_matched.push_back(matched);
            evInfo->vtx_normchi2.push_back(v.normalisedChiSquared());
            evInfo->vtx_genvdist.push_back(d);
            evInfo->vtx_genvdist_2d.push_back(d_2d);
            evInfo->vtx_genvdist_z.push_back(d_z);
            //vertices->push_back(nv);
          }
        }
      }
    }
  }

  evInfo->ntk_clus = clus_tk.size();

  std::set<int> all_tk_clus_llp;
  for(auto& itk : llp_all_track){
    if (std::find(clus_tk.begin(),clus_tk.end(),itk)!=clus_tk.end()) {
      all_tk_clus_llp.insert(itk);
    }
  }

  evInfo->ntk_clus_llp = all_tk_clus_llp.size();
  for (int illp=0;illp<nllp; ++illp){
    evInfo->llp_ntk_match.push_back(llp_tk_matched[illp].size());
  }
  eventTree->Fill();

  iEvent.put(std::move(genpart_llpdecay), "LLPdecays"); 
  iEvent.put(std::move(tk_llpmatched), "LLPmatched");
  iEvent.put(std::move(tk_gnn), "GNN");
}

float GNNDisplay::edge_dist(std::vector<float> v1, std::vector<float> v2) {
  if (v1.size() != v2.size()){
    throw cms::Exception("GNNDisplay::edge_dist") << "Sizes of v1 and v2 do not match!";
  }
  float d2 = 0;
  for (size_t i=0; i<v1.size(); ++i){
    d2 += pow(v1[i]-v2[i],2);
  }
  return d2;
}

std::vector<float> GNNDisplay::track_input(reco::TrackRef tk, const reco::Vertex* pv, SoftDV::PFIsolation isoDR03) {
  float pt = tk->pt();
  float eta = tk->eta();
  float phi = tk->phi();
  float dxy = tk->dxy(pv->position());
  float dxyError = tk->dxyError(pv->position(), pv->covariance());
  float dz = tk->dz(pv->position());
  float dzError = tk->dzError();
  float ptError = tk->ptError();
  float normchi2 = tk->normalizedChi2();
  float nvalidhits = tk->numberOfValidHits();
  float pfRelIso03_all = (isoDR03.chargedHadronIso() +
                            std::max<double>(isoDR03.neutralHadronIso() +
                                             isoDR03.photonIso() -
                                             isoDR03.puChargedHadronIso()/2,0.0))
                          / tk->pt();

  std::vector<float> tk_vars = {pt,eta,phi,dxy,dxyError,dz,dzError,pfRelIso03_all,ptError,normchi2,nvalidhits};
  return tk_vars;
}

bool GNNDisplay::v_pass(const reco::Vertex& v, const reco::Vertex* pv) {
  if (!v.isValid())
    return false;
  if (v.normalizedChi2()>10)
    return false;
  double dx = (v.x() - pv->x());
  double dy = (v.y() - pv->y());
  double dz = (v.z() - pv->z());
  double pdotv = (dx * v.p4().Px() + dy * v.p4().Py() + dz * v.p4().Pz()) / sqrt(v.p4().P2()) / sqrt(dx * dx + dy * dy + dz * dz);
  if (std::acos(pdotv)>(TMath::Pi()/2))
    return false;
  return true;
}

bool GNNDisplay::isGoodTrack(reco::TrackRef tk, const reco::Vertex* pv, SoftDV::PFIsolation isoDR03) {
  float pt = tk->pt();
  float eta = tk->eta();
  float phi = tk->phi();
  float dxy = tk->dxy(pv->position());
  float dxyError = tk->dxyError(pv->position(), pv->covariance());
  float dz = tk->dz(pv->position());
  float dzError = tk->dzError();
  float ptError = tk->ptError();
  float normchi2 = tk->normalizedChi2();
  float nvalidhits = tk->numberOfValidHits();
  float pfRelIso03_all = (isoDR03.chargedHadronIso() +
                            std::max<double>(isoDR03.neutralHadronIso() +
                                             isoDR03.photonIso() -
                                             isoDR03.puChargedHadronIso()/2,0.0))
                          / tk->pt();

  if ( (abs(dxy/dxyError)>4 ) && (abs(dxy/dz)>0.25) && (pfRelIso03_all<5) && (normchi2<5) && (nvalidhits>13) && (ptError/pt <0.015) )
    return true;
  return false;
}

void GNNDisplay::beginJob()
{
  edm::Service<TFileService> fs;
  eventTree = fs->make<TTree>( "treeGNN", "treeGNN" );

  eventTree->Branch("ntk",  &evInfo->ntk);
  eventTree->Branch("ntk_clus",  &evInfo->ntk_clus);
  eventTree->Branch("ntk_llp",  &evInfo->ntk_llp);
  eventTree->Branch("ntk_clus_llp",  &evInfo->ntk_clus_llp);
  eventTree->Branch("clus_ntk",  &evInfo->clus_ntk);
  eventTree->Branch("clus_llpidx",  &evInfo->clus_llpidx);
  eventTree->Branch("clus_ntk_match",  &evInfo->clus_ntk_match);
  eventTree->Branch("clus_mass",  &evInfo->clus_mass);
  eventTree->Branch("clus_nGoodTrack",  &evInfo->clus_nGoodTrack);
  eventTree->Branch("llp_ntk",  &evInfo->llp_ntk);
  eventTree->Branch("llp_ntk_match",  &evInfo->llp_ntk_match);
  eventTree->Branch("llp_matched",  &evInfo->llp_matched);
  eventTree->Branch("llp_matched_vtx",  &evInfo->llp_matched_vtx);
  eventTree->Branch("llp_closest_genv_dist",  &evInfo->llp_closest_genv_dist);
  eventTree->Branch("llp_closest_genv_dist_z",  &evInfo->llp_closest_genv_dist_z);
  eventTree->Branch("llp_closest_genv_dist_2d",  &evInfo->llp_closest_genv_dist_2d);
  eventTree->Branch("llp_min_vtx_normchi2",  &evInfo->llp_min_vtx_normchi2);
  eventTree->Branch("vtx_chi2",  &evInfo->vtx_chi2);
  eventTree->Branch("vtx_matched",  &evInfo->vtx_matched);
  eventTree->Branch("vtx_normchi2",  &evInfo->vtx_normchi2);
  eventTree->Branch("vtx_genvdist",  &evInfo->vtx_genvdist);
  eventTree->Branch("vtx_genvdist_2d",  &evInfo->vtx_genvdist_2d);
  eventTree->Branch("vtx_genvdist_z",  &evInfo->vtx_genvdist_z);
}

void GNNDisplay::initEventStructure()
{
  evInfo->ntk = 0;
  evInfo->ntk_clus = 0;
  evInfo->ntk_llp = 0;
  evInfo->ntk_clus_llp = 0;
  evInfo->clus_ntk.clear();
  evInfo->clus_llpidx.clear();
  evInfo->clus_ntk_match.clear();
  evInfo->clus_mass.clear();
  evInfo->clus_nGoodTrack.clear();
  evInfo->llp_ntk.clear();
  evInfo->llp_ntk_match.clear();
  evInfo->llp_matched.clear();
  evInfo->llp_matched_vtx.clear();
  evInfo->vtx_chi2.clear();
  evInfo->vtx_matched.clear();
  evInfo->vtx_normchi2.clear();
  evInfo->vtx_genvdist.clear();
  evInfo->vtx_genvdist_2d.clear();
  evInfo->vtx_genvdist_z.clear();
  evInfo->llp_closest_genv_dist.clear();
  evInfo->llp_closest_genv_dist_z.clear();
  evInfo->llp_closest_genv_dist_2d.clear();
  evInfo->llp_min_vtx_normchi2.clear();
}

DEFINE_FWK_MODULE(GNNDisplay);
