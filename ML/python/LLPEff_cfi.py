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

LLPEff = cms.EDAnalyzer('LLPEff',
    primary_vertex_token = cms.InputTag("offlineSlimmedPrimaryVertices"),
    secondary_vertex_token = cms.InputTag("GNNVtxSoftDV"),
    tracks = cms.InputTag("TrackFilter", "seed"),
    isoDR03 = cms.InputTag("TrackFilter", "isolationDR03"),
    gen = cms.InputTag("genParticles"),
    #kvr_params = kvr_params,
    vtx_params = vtx_params,
    )
