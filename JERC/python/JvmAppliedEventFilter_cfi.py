
import FWCore.ParameterSet.Config as cms

jvmAppliedEventFilter = cms.EDFilter(
    "JvmAppliedEventFilter",
    Jets = cms.PSet(
        SourcesAK4 = cms.InputTag("slimmedJetsPuppi"),
        minPt   = cms.double(15.0),
        maxEta  = cms.double(4.0),
        Year    = cms.string("2018"),
        JvmConfig = cms.FileInPath("jerc-application-tutorial/JvmConfig.json"),
    )
    
)

