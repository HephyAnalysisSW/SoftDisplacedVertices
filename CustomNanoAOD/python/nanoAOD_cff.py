import FWCore.ParameterSet.Config as cms
from PhysicsTools.NanoAOD.common_cff import *

useIVF = False
useGNN = False
useGNNIVF = False
useGNNAVR = False
useGNNAVRIVF = True

def nanoAOD_customise_SoftDisplacedVertices(process, isMC=None):
    assert not (useIVF and useGNN)

    process.load("SoftDisplacedVertices.VtxReco.VertexReco_cff")
    process.load("SoftDisplacedVertices.VtxReco.Vertexer_cfi")
    process.load("SoftDisplacedVertices.ML.GNNVtxReco_cff")
    process.load("SoftDisplacedVertices.ML.GNNInference_cfi")
    process.load("SoftDisplacedVertices.ML.GNNGenInfo_cfi")
  
    if useIVF:
      process.vtxReco = cms.Sequence(
          process.inclusiveVertexFinderSoftDV *
          process.vertexMergerSoftDV *
          process.trackVertexArbitratorSoftDV *
          process.IVFSecondaryVerticesSoftDV
      )
    elif useGNN:
      ##process.GNNVtxSoftDV = process.GNNInference.clone()
      ##process.GNNVtxSoftDV0 = process.GNNInference.clone()
      ##process.GNNVtxSoftDV0 = process.GNNGenInfo.clone()
      #process.GNNVtxSoftDV = process.vtxRecoGNN.clone()
      #process.vtxReco = cms.Sequence(
      #    #process.vtxRecoGNN *
      #    #process.inclusiveVertexFinderGNN * 
      #    #process.vertexMergerGNN *
      #    #process.trackVertexArbitratorGNN *
      #    process.GNNVtxSoftDV
      #)
      #process.GNNVtxSoftDV = process.mfvVerticesMINIAOD.clone(
      #    seed_tracks_src = cms.InputTag('vtxRecoGNN'),
      #    )
      process.GNNVtxSoftDV = process.vtxRecoGNN.clone()
      process.vtxReco = cms.Sequence(
          #process.vtxRecoGNN *
          process.GNNVtxSoftDV
          )
    else:
      process.MFVSecondaryVerticesSoftDV = process.mfvVerticesMINIAOD.clone()
      process.vtxReco = cms.Sequence(
          process.MFVSecondaryVerticesSoftDV
      )
    if useIVF:
      process.vtxReco = cms.Sequence(
          process.inclusiveVertexFinderSoftDV *
          process.vertexMergerSoftDV *
          process.trackVertexArbitratorSoftDV *
          process.IVFSecondaryVerticesSoftDV
      )
    elif useGNN:
      ##process.GNNVtxSoftDV = process.GNNInference.clone()
      ##process.GNNVtxSoftDV0 = process.GNNInference.clone()
      ##process.GNNVtxSoftDV0 = process.GNNGenInfo.clone()
      #process.GNNVtxSoftDV = process.vtxRecoGNN.clone()
      #process.vtxReco = cms.Sequence(
      #    #process.vtxRecoGNN *
      #    #process.inclusiveVertexFinderGNN * 
      #    #process.vertexMergerGNN *
      #    #process.trackVertexArbitratorGNN *
      #    process.GNNVtxSoftDV
      #)
      #process.GNNVtxSoftDV = process.mfvVerticesMINIAOD.clone(
      #    seed_tracks_src = cms.InputTag('vtxRecoGNN'),
      #    )
      process.GNNVtxSoftDV = process.vtxRecoGNN.clone()
      process.vtxReco = cms.Sequence(
          #process.vtxRecoGNN *
          process.GNNVtxSoftDV
          )
    elif useGNNIVF:
      process.vtxReco = cms.Sequence(
          process.vtxRecoGNN *
          process.inclusiveVertexFinderGNN * 
          process.vertexMergerGNN *
          process.trackVertexArbitratorGNN *
          process.GNNVtxSoftDV
      )
    elif useGNNAVR:
      process.GNNVtxSoftDV.secondaryVertices = cms.InputTag("vtxRecoGNN")
      process.vtxReco = cms.Sequence(
          process.vtxRecoGNN *
          process.GNNVtxSoftDV
      )
    elif useGNNAVRIVF:
      process.vertexMergerGNN.secondaryVertices = cms.InputTag("vtxRecoGNN")
      process.vtxReco = cms.Sequence(
          process.vtxRecoGNN *
          process.vertexMergerGNN *
          process.trackVertexArbitratorGNN *
          process.GNNVtxSoftDV
      )
    else:
      process.MFVSecondaryVerticesSoftDV = process.mfvVerticesMINIAOD.clone()
      process.vtxReco = cms.Sequence(
          process.MFVSecondaryVerticesSoftDV
      )

    process.load("SoftDisplacedVertices.CustomNanoAOD.SVTrackTable_cfi")
    process.load("SoftDisplacedVertices.CustomNanoAOD.RecoTrackTableProducer_cfi")

    if useGNN or useGNNIVF or useGNNAVRIVF or useGNNAVR:
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


    # Get total sum of weights from NanoAOD instead of going back to MiniAOD.
    process.genFilterTable.variables.sumWeights     = Var("sumWeights()",     float, doc = "generator filter: sum of pass event weights", precision = -1)
    process.genFilterTable.variables.sumPassWeights = Var("sumPassWeights()", float, doc = "generator filter: sum of event weights",      precision = -1)

    process.finalGenParticlesWithStableCharged = process.finalGenParticles.clone(
        src = cms.InputTag("prunedGenParticles")
    )
    process.finalGenParticlesWithStableCharged.select.append('keep status==1 && abs(charge) == 1')

    process.genParticleForSDVTable = process.genParticleTable.clone(
        # src = cms.InputTag("finalGenParticlesWithStableCharged"),
        src = cms.InputTag("genParticles"),
        name = cms.string("SDVGenPart"),
        externalVariables = None
    )

    process.load('SoftDisplacedVertices.CustomNanoAOD.GenSecondaryVertexTableProducer_cff')
    process.load('SoftDisplacedVertices.CustomNanoAOD.LLPTable_cfi')

    if useGNN or useGNNIVF or useGNNAVRIVF or useGNNAVR:
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
