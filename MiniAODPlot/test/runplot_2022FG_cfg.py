# import standard CMSSW modules
import FWCore.ParameterSet.Config as cms
import FWCore.Utilities.FileUtils as FileUtils
import HLTrigger.HLTfilters.hltHighLevel_cfi as hlt

process = cms.Process("Histos")

process.options = cms.untracked.PSet(
)

#Setup FWK for multithreaded
process.options.numberOfThreads=cms.untracked.uint32(4)
process.options.numberOfStreams=cms.untracked.uint32(0)
process.options.numberOfConcurrentLuminosityBlocks=cms.untracked.uint32(1)

process.load("FWCore.MessageService.MessageLogger_cfi")
process.MessageLogger.cerr.FwkReport.reportEvery = 10000

process.maxEvents = cms.untracked.PSet( input = cms.untracked.int32(-1) )

# configures the source that reads the input files
process.source = cms.Source("PoolSource",
  fileNames = cms.untracked.vstring(
    '/store/user/wuzh/SingleMuon/Run2018A_mini_v2/251223_130751/0002/MiniAOD_1-2869.root'
  )
)

# HLT trigger requirement
process.trig_filter = hlt.hltHighLevel.clone(
    HLTPaths = ['HLT_IsoMu24_v*', 'HLT_IsoMu27_v*'],
    throw = False
    )

process.noise_filter = hlt.hltHighLevel.clone(
    TriggerResultsTag = cms.InputTag("TriggerResults","","PAT"),
    HLTPaths = ['Flag_goodVertices','Flag_globalSuperTightHalo2016Filter','Flag_EcalDeadCellTriggerPrimitiveFilter','Flag_BadPFMuonFilter','Flag_BadPFMuonDzFilter','Flag_hfNoisyHitsFilter','Flag_eeBadScFilter'],
    andOr = False,
    throw = True
    )


process.TFileService = cms.Service("TFileService", fileName = cms.string("vtx_histos.root") )

process.load('RecoMET.METFilters.ecalBadCalibFilter_cfi')

baddetEcallist = cms.vuint32([838871812]) # This is the only badly calibrated crystal in 2022 and 2023.

process.ecalBadCalibReducedMINIAODFilter = cms.EDFilter(
    "EcalBadCalibFilter",
    EcalRecHitSource = cms.InputTag("reducedEgamma:reducedEBRecHits"),
    ecalMinEt        = cms.double(50.),
    baddetEcal    = baddetEcallist, 
    taggingMode = cms.bool(True),
    debug = cms.bool(False)
    )


process.load("SoftDisplacedVertices.VtxReco.VertexReco_cff")
process.load("SoftDisplacedVertices.VtxReco.Vertexer_cfi")
process.load("TrackingTools/TransientTrack/TransientTrackBuilder_cfi")
process.load('Configuration.StandardSequences.GeometryRecoDB_cff')
process.load("Configuration.StandardSequences.MagneticField_cff")
process.load('Configuration.StandardSequences.FrontierConditions_GlobalTag_cff')
process.GlobalTag.globaltag = '130X_dataRun3_PromptAnalysis_v1'

process.vtxReco = cms.Sequence(
    process.inclusiveVertexFinderSoftDV *
    process.vertexMergerSoftDV *
    process.trackVertexArbitratorSoftDV *
    process.IVFSecondaryVerticesSoftDV
)

process.MiniAODPlot = cms.EDAnalyzer("MiniAODPlot",
        met_token = cms.untracked.InputTag('slimmedMETs'),
        muons_src = cms.untracked.InputTag('slimmedMuons'),
        vtx_token = cms.untracked.InputTag("IVFSecondaryVerticesSoftDV"),
        )

process.p = cms.Path(process.ecalBadCalibReducedMINIAODFilter + process.trig_filter + process.noise_filter + process.vtxReco + process.MiniAODPlot)
