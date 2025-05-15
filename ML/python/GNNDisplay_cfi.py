import FWCore.ParameterSet.Config as cms

kvr_params = cms.PSet(
    maxDistance = cms.double(0.01),
    maxNbrOfIterations = cms.int32(10),
    doSmoothing = cms.bool(True),
)

#vtx_params = cms.PSet(
#    finder = cms.string("avr"),
#    primcut = cms.double(1.0),
#    seccut = cms.double(3.0),
#    smoothing = cms.bool(True),
#)
vtx_params = cms.PSet(
    finder = cms.string("kalman"),
    #maxDistance = cms.double(0.01),
    maxDistance = cms.double(999),
    maxNbrOfIterations = cms.int32(10),
    doSmoothing = cms.bool(True),
)

GNNDisplay = cms.EDProducer('GNNDisplay',
    input_names_emb = cms.vstring("input_tk"),
    input_names_gnn = cms.vstring("input_tk","input_edges"),
    primary_vertex_token = cms.InputTag("offlineSlimmedPrimaryVertices"),
    tracks = cms.InputTag("TrackFilter", "seed"),
    isoDR03 = cms.InputTag("TrackFilter", "isolationDR03"),
    #EMB_model_path = cms.FileInPath("SoftDisplacedVertices/ML/EMB_1.onnx"),
    #GNN_model_path = cms.FileInPath("SoftDisplacedVertices/ML/GNN_dist0p15_0509.onnx"),
    EMB_model_path = cms.FileInPath("SoftDisplacedVertices/ML/EMB_0603_3.onnx"),
    GNN_model_path = cms.FileInPath("SoftDisplacedVertices/ML/GNN_0607.onnx"),
    edge_dist_cut = cms.double(0.02),
    edge_gnn_cut = cms.double(0.9),
    gen = cms.InputTag("genParticles"),
    #kvr_params = kvr_params,
    vtx_params = vtx_params,
    )
