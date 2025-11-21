#include <memory>
#include <vector>
#include <set>
#include <algorithm>
#include <iostream>

#include "TMath.h"

#include "FWCore/Framework/interface/Event.h"
#include "FWCore/Framework/interface/Frameworkfwd.h"
#include "FWCore/Framework/interface/MakerMacros.h"
#include "FWCore/Framework/interface/stream/EDProducer.h"
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
#include "RecoVertex/VertexTools/interface/VertexDistance3D.h"
#include "RecoVertex/VertexTools/interface/SharedTracks.h"
#include "RecoVertex/VertexPrimitives/interface/VertexState.h"
#include "RecoVertex/VertexPrimitives/interface/ConvertToFromReco.h"

#include "PhysicsTools/ONNXRuntime/interface/ONNXRuntime.h"

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

struct Cluster {
  int nTrack;
  int nGoodTrack;
  double mass;
  std::vector<int> tks;
};

using namespace cms::Ort;
typedef std::vector<std::unique_ptr<ONNXRuntime>> NNArray;

class GNNInference : public edm::stream::EDProducer<edm::GlobalCache<NNArray>> {
  public:
    explicit GNNInference(const edm::ParameterSet &, const NNArray *);
    
    static std::unique_ptr<NNArray> initializeGlobalCache(const edm::ParameterSet &);
    static void globalEndJob(const NNArray *);

  private:
    void beginJob();
    void produce(edm::Event&, const edm::EventSetup&) override;
    void endJob();

    float edge_dist(std::vector<float> v1, std::vector<float> v2);
    std::vector<float> track_input(reco::TrackRef tk, const reco::Vertex* pv, SoftDV::PFIsolation isoDR03);
    bool v_pass(const reco::Vertex& v, const reco::Vertex* pv);
    bool isGoodTrack(reco::TrackRef tk, const reco::Vertex* pv, SoftDV::PFIsolation isoDR03);

    std::vector<std::string> input_names_emb_;
    std::vector<std::string> input_names_gnn_;
    std::vector<std::vector<int64_t>> input_shapes_;
    const edm::EDGetTokenT<reco::VertexCollection> primary_vertex_token;
    const edm::EDGetTokenT<reco::TrackCollection> tracks_token;
    edm::EDGetTokenT<std::vector<SoftDV::PFIsolation>> isoDR03Token_;
    const edm::ESGetToken<TransientTrackBuilder, TransientTrackRecord> transientTrackBuilderToken_;
    //FloatArrays data_; // each stream hosts its own data
    //
    double edge_dist_cut_;
    double edge_gnn_cut_;

    bool useAVR;
    bool useKF;
    std::unique_ptr<VertexReconstructor> vtxReco;
};

GNNInference::GNNInference(const edm::ParameterSet &iConfig, const NNArray *cache)
  : input_names_emb_(iConfig.getParameter<std::vector<std::string>>("input_names_emb")),
    input_names_gnn_(iConfig.getParameter<std::vector<std::string>>("input_names_gnn")),
    input_shapes_(),
    primary_vertex_token(consumes<reco::VertexCollection>(iConfig.getParameter<edm::InputTag>("primary_vertex_token"))),
    tracks_token(consumes<reco::TrackCollection>(iConfig.getParameter<edm::InputTag>("tracks"))),
    isoDR03Token_(consumes<std::vector<SoftDV::PFIsolation>>(iConfig.getParameter<edm::InputTag>("isoDR03"))),
    transientTrackBuilderToken_{esConsumes(edm::ESInputTag("", "TransientTrackBuilder"))},
    edge_dist_cut_(iConfig.getParameter<double>("edge_dist_cut")),
    edge_gnn_cut_(iConfig.getParameter<double>("edge_gnn_cut")),
    //kv_reco(new KalmanVertexFitter(iConfig.getParameter<edm::ParameterSet>("kvr_params"), iConfig.getParameter<edm::ParameterSet>("kvr_params").getParameter<bool>("doSmoothing")))
    useAVR(iConfig.getParameter<bool>("useAVR")),
    useKF(iConfig.getParameter<bool>("useKF")),
    vtxReco(new ConfigurableVertexReconstructor(iConfig.getParameter<edm::ParameterSet>("vtx_params"))){
    if ((useAVR+useKF)!=1)
      throw cms::Exception("GNNInference", "One and only one of useAVR and useKF should be set to true!");

    produces<reco::VertexCollection>();
    produces<reco::TrackCollection>();
    }

std::unique_ptr<NNArray> GNNInference::initializeGlobalCache(const edm::ParameterSet &iConfig) {
  std::unique_ptr<NNArray> NNs = std::make_unique<NNArray>();
  NNs->push_back(std::make_unique<ONNXRuntime>(iConfig.getParameter<edm::FileInPath>("EMB_model_path").fullPath()));
  NNs->push_back(std::make_unique<ONNXRuntime>(iConfig.getParameter<edm::FileInPath>("GNN_model_path").fullPath()));
  return NNs;
}

void GNNInference::globalEndJob(const NNArray *cache) {}

void GNNInference::produce(edm::Event &iEvent, const edm::EventSetup &iSetup) {

  std::unique_ptr<reco::VertexCollection> vertices(new reco::VertexCollection);
  std::unique_ptr<reco::TrackCollection> good_tracks(new reco::TrackCollection);

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
    throw cms::Exception("GNNInference") << "Tracks mismatch with track IsoDR03!";

  TransientTrackBuilder const* tt_builder = nullptr;
  tt_builder = &iSetup.getData(transientTrackBuilderToken_);

  int ntks = tracks->size();

  if (ntks==0) {
    iEvent.put(std::move(vertices));
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

  std::vector<float> emb = globalCache()->at(0)->run(input_names_emb_, inputdata, tk_shape, {}, ntks)[0];

  std::vector<int> sender_idx;
  std::vector<int> receiver_idx;
  std::vector<float> distance;

  for (int i=0;i<ntks;++i){
    for (int j=0;j<ntks;++j){
      if (i==j) continue;
      std::vector<float> emb_i(emb.begin()+i*16,emb.begin()+(i+1)*16);
      std::vector<float> emb_j(emb.begin()+j*16,emb.begin()+(j+1)*16);
      float d2 = edge_dist(emb_i,emb_j);
      if (d2<999){ // FIXME: the cut value on d2 should be revisited
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

  std::vector<float> gnn = globalCache()->at(1)->run(input_names_gnn_, input_GNN, input_shape_GNN, {}, 1)[0];

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
  std::set<int> tk_idx;
  for (auto& ic : clus) {
    //std::vector<reco::TransientTrack> seed_tracks;
    for (int itk : ic){
      tk_idx.insert(itk);
      //reco::TrackRef tk(tracks, itk);
      //seed_tracks.push_back(tt_builder->build(tk));
    }
    //reco::Vertex v(TransientVertex(kv_reco->vertex(seed_tracks)));
    //std::cout << "Number of tracks: " << seed_tracks.size() << std::endl;
    //std::vector<TransientVertex> vs = vtxReco->vertices(seed_tracks);
    //for (auto& v : vs) {
    //  //std::cout << "  ntk " << v.originalTracks().size() << " " << v.normalisedChiSquared() << std::endl;
    //  if (v.isValid() && v.originalTracks().size()>1){
    //    vertices->push_back(v);
    //  }
    //}
    //if (v.nTracks()>1)
    //  vertices->push_back(v);
  }

  std::map<int, reco::TransientTrack> ttk_map;
  for(int itk:tk_idx) {
    reco::TrackRef tk(tracks, itk);
    ttk_map[itk] = tt_builder->build(tk);
    good_tracks->push_back(*tk);
  }
  //std::vector<TransientVertex> vs = vtxReco->vertices(seed_tracks);
  //for (auto& v : vs) {
  //  if (v.isValid() && v.originalTracks().size()>1){
  //    vertices->push_back(v);
  //  }
  //}

  std::vector<Cluster> clusters;
  for (auto& ic : clus) {
    Cluster icluster;
    std::vector<int> vtks(ic.begin(),ic.end());
    icluster.tks = vtks;
    icluster.nTrack = vtks.size();
    math::XYZTLorentzVectorD sum;
    ROOT::Math::LorentzVector<ROOT::Math::PxPyPzM4D<double> > vec;
    int nGoodTrack = 0;
    for (int itk : ic) {
      reco::TrackRef tk(tracks, itk);
      vec.SetPx(tk->px());
      vec.SetPy(tk->py());
      vec.SetPy(tk->pz());
      vec.SetM(0.13957018);
      sum += vec;
      SoftDV::PFIsolation isoDR03 = (*tracks_isoDR03)[itk];
      if (isGoodTrack(tk,primary_vertex,isoDR03)) {
        nGoodTrack += 1;
      }
    }
    //std::cout << "Number of Good track " << nGoodTrack << std::endl;
    icluster.mass = sum.M();
    icluster.nGoodTrack = nGoodTrack;
    //if (icluster.mass<0.5)
    //  continue;
    //if (icluster.nGoodTrack<1)
    //  continue;
    //if (icluster.nTrack<3)
    //  continue;
    clusters.push_back(icluster);
  }

  if (useAVR) {
    // Below reconstructs vertices using Adaptive vertex reconstruction
    for (auto& ic : clusters) {
      std::vector<int> vtks = ic.tks;
      int nst = vtks.size();
      std::vector<reco::TransientTrack> vtx_tks;
      for (auto& ist : vtks) {
        if (ttk_map.find(ist)==ttk_map.end())
          throw cms::Exception("GNNInference") << "Track index " << ist << " not found in map!";
        vtx_tks.push_back(ttk_map[ist]);
      }
      std::vector<TransientVertex> vs = vtxReco->vertices(vtx_tks);
      for (auto& v : vs) {
        if (v.isValid() && v.originalTracks().size()>1){
          vertices->push_back(v);
        }
      }
    }
  }
  else if (useKF) {
    // Below reconstructs vertices using Kalman vertex filter:
    // Start from each pair of tracks to fit seed vertices
    // Merge vertices when tracks are shared
    for (auto& ic : clusters) {
      std::vector<int> vtks = ic.tks;
      int nst = vtks.size();
      for (int iist=0; iist<nst; ++iist){
        for (int jjst=iist+1; jjst<nst; ++jjst){
          int ist = vtks[iist];
          int jst = vtks[jjst];
          if (ttk_map.find(ist)==ttk_map.end())
            throw cms::Exception("GNNInference") << "Track index " << ist << " not found in map!";
          if (ttk_map.find(jst)==ttk_map.end())
            throw cms::Exception("GNNInference") << "Track index " << jst << " not found in map!";
          std::vector<reco::TransientTrack> track_pairs({ttk_map[ist],ttk_map[jst]});
          std::vector<TransientVertex> vs = vtxReco->vertices(track_pairs);
          for (auto& v : vs) {
            const reco::Vertex nv(v);
            if (v_pass(nv,primary_vertex)){
              vertices->push_back(nv);
            }
          }
        }
      }
    }

    // Now try a vertex merge
    VertexDistance3D dist;
    for (auto sv1 = vertices->begin(); sv1!=vertices->end(); ++sv1) {
      VertexState s1(RecoVertex::convertPos(sv1->position()),RecoVertex::convertError(sv1->error()));
      for (auto sv2 = vertices->begin(); sv2!=vertices->end();++sv2) {
        VertexState s2(RecoVertex::convertPos(sv2->position()),RecoVertex::convertError(sv2->error()));
        double fr = vertexTools::computeSharedTracks(*sv1, *sv2);
        if (fr > 0.3 && dist.distance(s1,s2).significance() < 10 && sv1-sv2!=0 && fr >= vertexTools::computeSharedTracks(*sv2, *sv1)) {
          std::set<int> tk_sets;
          for (auto it = sv1->tracks_begin();it!=sv1->tracks_end();++it) {
            reco::TrackRef tref = it->castTo<reco::TrackRef>();
            tk_sets.insert(tref.key());
          }
          for (auto it = sv2->tracks_begin();it!=sv2->tracks_end();++it) {
            reco::TrackRef tref = it->castTo<reco::TrackRef>();
            tk_sets.insert(tref.key());
          }
          std::vector<reco::TransientTrack> new_tks;
          for (auto& it : tk_sets){
            if (ttk_map.find(it)==ttk_map.end())
              throw cms::Exception("GNNInference") << "Track index " << it << " not found in map!";
            new_tks.push_back(ttk_map[it]);
          }
          std::vector<TransientVertex> vs = vtxReco->vertices(new_tks);
          if (vs.size()>1) {
            throw cms::Exception("GNNInference") << "More than 1 vertex is fitted!";
          }
          if (vs.size()==1) {
            reco::Vertex nv = reco::Vertex(vs[0]);
            if (nv.isValid() && nv.normalizedChi2()<10) {
              *sv1 = nv;
              if (sv2>sv1) {
                vertices->erase(sv2);
                sv1 -= 1;
              }
              else {
                vertices->erase(sv2);
                sv1 -= 2;
              }
              break;
            }
          }
        }
      }
    }
  }
  else {
    throw cms::Exception("GNNInference", "No vertex reco is specified!");
  }

  iEvent.put(std::move(vertices));
  iEvent.put(std::move(good_tracks));
}

float GNNInference::edge_dist(std::vector<float> v1, std::vector<float> v2) {
  if (v1.size() != v2.size()){
    throw cms::Exception("GNNInference::edge_dist") << "Sizes of v1 and v2 do not match!";
  }
  float d2 = 0;
  for (size_t i=0; i<v1.size(); ++i){
    d2 += pow(v1[i]-v2[i],2);
  }
  return d2;
}

std::vector<float> GNNInference::track_input(reco::TrackRef tk, const reco::Vertex* pv, SoftDV::PFIsolation isoDR03) {
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

bool GNNInference::v_pass(const reco::Vertex& v, const reco::Vertex* pv) {
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

bool GNNInference::isGoodTrack(reco::TrackRef tk, const reco::Vertex* pv, SoftDV::PFIsolation isoDR03) {
  float pt = tk->pt();
  //float eta = tk->eta();
  //float phi = tk->phi();
  float dxy = tk->dxy(pv->position());
  float dxyError = tk->dxyError(pv->position(), pv->covariance());
  float dz = tk->dz(pv->position());
  //float dzError = tk->dzError();
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

DEFINE_FWK_MODULE(GNNInference);
