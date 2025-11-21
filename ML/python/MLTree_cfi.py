import FWCore.ParameterSet.Config as cms

MLTree = cms.EDAnalyzer("MLTree",
    beamspot_token = cms.InputTag('offlineBeamSpot'),
    primary_vertex_token = cms.InputTag('offlineSlimmedPrimaryVertices'),
    jet_token = cms.InputTag('slimmedJets'),
    met_token = cms.InputTag('slimmedMETs'),
    vtx_token = cms.InputTag('IVFSecondaryVerticesSoftDV'),
    gen_token = cms.InputTag('genParticles'),
    tk_token = cms.InputTag('TrackFilter',"seed"),
    isoDR03 = cms.InputTag("TrackFilter", "isolationDR03"),
    LLPid_ = cms.vint32(1000006),
    LSPid_ = cms.int32(1000022),
    debug = cms.bool(False),
)
