"""
Implementation date: 4/4/2024
Implemented from RecoTracker/TrackExtrapolator/src/TrackExtrapolator.cc
"""
import FWCore.ParameterSet.Config as cms
TrackExtrapolationTable = cms.EDProducer("TrackExtrapolator",
    pvSrc = cms.InputTag("offlineSlimmedPrimaryVertices"),
    svSrc = cms.InputTag("IVFSecondaryVerticesSoftDV"),
    tkSrc = cms.InputTag("TrackFilter", "seed"),
    extrapTkOut = cms.string("SDVTkExtra"),
    extrapSvOut = cms.string("SDVSvExtra")
)
