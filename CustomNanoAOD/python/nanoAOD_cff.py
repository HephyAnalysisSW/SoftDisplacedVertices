import FWCore.ParameterSet.Config as cms
from PhysicsTools.NanoAOD.common_cff import *

isN2N3 = False
useIVF = True

def nanoAOD_customise_SoftDisplacedVertices(process):

    process.load("SoftDisplacedVertices.VtxReco.VertexReco_cff")
    process.load("SoftDisplacedVertices.VtxReco.Vertexer_cfi")
  
    if useIVF:
      process.vtxReco = cms.Sequence(
          process.inclusiveVertexFinderSoftDV *
          process.vertexMergerSoftDV *
          process.trackVertexArbitratorSoftDV *
          process.IVFSecondaryVerticesSoftDV
      )
    else:
      process.MFVSecondaryVerticesSoftDV = process.mfvVerticesMINIAOD.clone()
      process.vtxReco = cms.Sequence(
          process.MFVSecondaryVerticesSoftDV
      )

    process.load("SoftDisplacedVertices.CustomNanoAOD.SVTrackTable_cfi")
    process.load("SoftDisplacedVertices.CustomNanoAOD.RecoTrackTableProducer_cfi")

    if not useIVF:
      process.SVTrackTable.svSrc = cms.InputTag("MFVSecondaryVerticesSoftDV")
    
#   have care when running on data
    print(process.nanoSequenceMC)
    process.nanoSequenceMC = cms.Sequence(process.nanoSequenceMC + process.recoTrackTable + process.vtxReco + process.SVTrackTable)
    
    return process

def nanoAOD_customise_SoftDisplacedVerticesMC(process):

    process = nanoAOD_customise_SoftDisplacedVertices(process)
    
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
    if not useIVF:
      process.LLPTable.svToken = cms.InputTag("MFVSecondaryVerticesSoftDV")

    process.sdvSequence = cms.Sequence(
        process.finalGenParticlesWithStableCharged
        + process.genParticleForSDVTable
        + process.genSecondaryVertexTable
        + process.LLPTable
    )
    process.nanoSequenceMC = cms.Sequence(process.nanoSequenceMC + process.sdvSequence)  
    
    return process


