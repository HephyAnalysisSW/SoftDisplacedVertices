import FWCore.ParameterSet.Config as cms

useMINIAOD = False
useIVF = True

process = cms.Process("Histos")

process.load("FWCore.MessageService.MessageLogger_cfi")

process.maxEvents = cms.untracked.PSet( input = cms.untracked.int32(-1) )

process.source = cms.Source("PoolSource",
  fileNames = cms.untracked.vstring(
    'file:/users/ang.li/public/SoftDV/CMSSW_10_6_30/src/SoftDisplacedVertices/VtxReco/test/TestRun/vtxreco.root'
  )
)
process.source.duplicateCheckMode = cms.untracked.string('noDuplicateCheck')

process.TFileService = cms.Service("TFileService", fileName = cms.string("tree.root") )

process.EventTreeAOD = cms.EDAnalyzer("EventTreeAOD",
    beamspot_token = cms.InputTag('offlineBeamSpot'),
    primary_vertex_token = cms.InputTag('offlinePrimaryVertices'),
    jet_token = cms.InputTag('ak4PFJets'),
    met_token = cms.InputTag('pfMet'),
    vtx_token = cms.InputTag('IVFSecondaryVerticesSoftDV'),
    llp_gen_token = cms.InputTag('GenInfo'),
    gen_matched_track_token = cms.InputTag('GenMatchedTracks'),
    debug = cms.bool(False),
)

process.EventTreeMINIAOD = cms.EDAnalyzer("EventTreeMINIAOD",
    beamspot_token = cms.InputTag('offlineBeamSpot'),
    primary_vertex_token = cms.InputTag('offlineSlimmedPrimaryVertices'),
    jet_token = cms.InputTag('slimmedJets'),
    met_token = cms.InputTag('slimmedMETs'),
    vtx_token = cms.InputTag('IVFSecondaryVerticesSoftDV'),
    llp_gen_token = cms.InputTag('GenInfo'),
    gen_matched_track_token = cms.InputTag('GenMatchedTracks'),
    debug = cms.bool(False),
)

if not useIVF:
  process.EventTreeAOD.vtx_token = cms.InputTag('MFVSecondaryVerticesSoftDV')
  process.EventTreeMINIAOD.vtx_token = cms.InputTag('MFVSecondaryVerticesSoftDV')

process.options = cms.untracked.PSet(
    SkipEvent= cms.untracked.vstring("ProductNotFound"), # make this exception fatal
)

if useIVF:
  #process.EventTreeMINIAOD.vtx_token = cms.InputTag('inclusiveVertexFinderSoftDV')
  #process.EventTreeMINIAOD.vtx_token = cms.InputTag('trackVertexArbitratorSoftDV')
  #process.EventTreeMINIAOD.vtx_token = cms.InputTag('vertexMergerSoftDV')
  process.EventTreeMINIAOD.vtx_token = cms.InputTag('IVFSecondaryVerticesSoftDV')

process.p = cms.Path()
if useMINIAOD:
  process.p = cms.Path(process.EventTreeMINIAOD)
else:
  process.p = cms.Path(process.EventTreeAOD)
