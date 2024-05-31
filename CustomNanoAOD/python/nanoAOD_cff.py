import FWCore.ParameterSet.Config as cms
from PhysicsTools.NanoAOD.common_cff import *

isN2N3 = False
useIVF = False
useGNN = True

def nanoAOD_customise_SoftDisplacedVertices(process, isMC=None):
    assert not (useIVF and useGNN)

    process.load("SoftDisplacedVertices.VtxReco.VertexReco_cff")
    process.load("SoftDisplacedVertices.VtxReco.Vertexer_cfi")
    process.load("SoftDisplacedVertices.ML.GNNInference_cfi")
  
    if useIVF:
      process.vtxReco = cms.Sequence(
          process.inclusiveVertexFinderSoftDV *
          process.vertexMergerSoftDV *
          process.trackVertexArbitratorSoftDV *
          process.IVFSecondaryVerticesSoftDV
      )
    elif useGNN:
      process.GNNVtxSoftDV = process.GNNInference.clone()
      process.vtxReco = cms.Sequence(
          process.GNNVtxSoftDV
      )
    else:
      process.MFVSecondaryVerticesSoftDV = process.mfvVerticesMINIAOD.clone()
      process.vtxReco = cms.Sequence(
          process.MFVSecondaryVerticesSoftDV
      )

    process.load("SoftDisplacedVertices.CustomNanoAOD.SVTrackTable_cfi")
    process.load("SoftDisplacedVertices.CustomNanoAOD.RecoTrackTableProducer_cfi")

    if useGNN:
      process.SVTrackTable.svSrc = cms.InputTag("GNNVtxSoftDV")
    elif (not useIVF):
      process.SVTrackTable.svSrc = cms.InputTag("MFVSecondaryVerticesSoftDV")
    
#   have care when running on data
    if isMC:
      process.nanoSequenceMC = cms.Sequence(process.nanoSequenceMC + process.recoTrackTable + process.vtxReco + process.SVTrackTable)
    else:
      process.nanoSequence = cms.Sequence(process.nanoSequence + process.recoTrackTable + process.vtxReco + process.SVTrackTable)
    
    return process

def nanoAOD_customise_SoftDisplacedVerticesMC(process):

    process = nanoAOD_customise_SoftDisplacedVertices(process, "MC")

    process.finalGenParticlesWithStableCharged = process.finalGenParticles.clone(
        src = cms.InputTag("prunedGenParticles")
    )
    process.finalGenParticlesWithStableCharged.select.append('keep status==1 && abs(charge) == 1')

    process.genParticleForSDVTable = process.genParticleTable.clone(
        #src = cms.InputTag("finalGenParticlesWithStableCharged"),
        src = cms.InputTag("genParticles"),
        name = cms.string("SDVGenPart")
    )

    process.load('SoftDisplacedVertices.CustomNanoAOD.GenSecondaryVertexTableProducer_cff')
    process.load('SoftDisplacedVertices.CustomNanoAOD.LLPTable_cfi')

    if isN2N3:
      process.LLPTable.LLPid_ = cms.vint32(1000023, 1000025)
    if useGNN:
      process.LLPTable.svToken = cms.InputTag("GNNVtxSoftDV")
    elif (not useIVF):
      process.LLPTable.svToken = cms.InputTag("MFVSecondaryVerticesSoftDV")

    process.sdvSequence = cms.Sequence(
        process.finalGenParticlesWithStableCharged
        + process.genParticleForSDVTable
        + process.genSecondaryVertexTable
        + process.LLPTable
    )
    process.nanoSequenceMC = cms.Sequence(process.nanoSequenceMC + process.sdvSequence)  
    
    return process

def nanoAOD_filter_SoftDisplacedVertices(process):
    process.load("SoftDisplacedVertices.CustomNanoAOD.LumiFilter_cfi")
    process.passLumiFilter = cms.Path(process.LumiFilter)
    process.schedule.insert(0,process.passLumiFilter)

    if hasattr(process, 'NANOAODoutput'):
        process.NANOAODoutput.SelectEvents = cms.untracked.PSet(SelectEvents = cms.vstring('passLumiFilter'))
    elif hasattr(process, 'NANOAODSIMoutput'):
        process.NANOAODSIMoutput.SelectEvents = cms.untracked.PSet(SelectEvents = cms.vstring('passLumiFilter'))
    else:
        print("WARNING: No NANOAOD[SIM]output definition")

    return process
