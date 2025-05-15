import FWCore.ParameterSet.Config as cms

LLPTable = cms.EDProducer("LLPTableProducer",
    src = cms.InputTag("genParticles"),
    #src = cms.InputTag("finalGenParticlesWithStableCharged"),
    LLPName = cms.string("LLP"),
    LLPDoc = cms.string("Table of LLPs"),
    pvToken = cms.InputTag("offlineSlimmedPrimaryVertices"),
    tkToken = cms.InputTag("TrackFilter","seed"),
    svToken = cms.InputTag("IVFSecondaryVerticesSoftDV"),
    debug = cms.bool(False),
    )
