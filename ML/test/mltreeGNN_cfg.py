import FWCore.ParameterSet.Config as cms

import HLTrigger.HLTfilters.hltHighLevel_cfi as hlt
from SoftDisplacedVertices.VtxReco.VertexReco_cff import VertexRecoSeq

useIVF = False
useGNN = False
useGNNIVF = False
useGNNAVR = False
useGNNAVRIVF = True

process = cms.Process('MLTree')

process.load('FWCore.MessageLogger.MessageLogger_cfi')
process.MessageLogger.cerr.FwkReport.reportEvery = 10000

# import of standard configurations
process.load('FWCore.MessageService.MessageLogger_cfi')
process.load('Configuration.EventContent.EventContent_cff')
process.load('Configuration.StandardSequences.Services_cff')
process.load('Configuration.StandardSequences.GeometryRecoDB_cff')
process.load('Configuration.StandardSequences.MagneticField_cff')
process.load('Configuration.StandardSequences.EndOfProcess_cff')
process.load('Configuration.StandardSequences.FrontierConditions_GlobalTag_cff')
process.load('SimGeneral.HepPDTESSource.pythiapdt_cfi')
process.load('SimGeneral.MixingModule.mixNoPU_cfi')
process.load('PhysicsTools.NanoAOD.nano_cff')

# Import vertex reconstruction configurations
process.load("SoftDisplacedVertices.VtxReco.VertexReco_cff")
process.load("SoftDisplacedVertices.VtxReco.GenProducer_cfi")
process.load("SoftDisplacedVertices.VtxReco.GenMatchedTracks_cfi")
process.load("TrackingTools/TransientTrack/TransientTrackBuilder_cfi")
process.load("SoftDisplacedVertices.ML.GNNVtxReco_cff")
process.load("SoftDisplacedVertices.ML.GNNInference_cfi")
process.load("SoftDisplacedVertices.ML.MLTree_cfi")

process.maxEvents = cms.untracked.PSet(
    input = cms.untracked.int32(-1)
)

MessageLogger = cms.Service("MessageLogger")


# Input source
process.source = cms.Source("PoolSource",
    fileNames = cms.untracked.vstring('file:/eos/vbc/experiments/cms/store/user/lian/CustomMiniAOD_v3_MLTraining_new/stop_M600_580_ct2_2018/output/out_MINIAODSIMoutput_0.root'),
    # fileNames = cms.untracked.vstring('file:/scratch-cbe/users/ang.li/SoftDV/MiniAOD_vtxreco/Stop_600_588_200/MINIAODSIMoutput_0.root'),
    #fileNames = cms.untracked.vstring('file:/eos/vbc/experiments/cms/store/user/liko/ZJetsToNuNu_HT-1200To2500_TuneCP5_13TeV-madgraphMLM-pythia8/ZJetsToNuNu_HT-1200To2500_MC_UL18_CustomMiniAODv1/231029_221242/0000/MiniAOD_1.root'),
    secondaryFileNames = cms.untracked.vstring()
)

process.options = cms.untracked.PSet(
    SkipEvent= cms.untracked.vstring("ProductNotFound"),
)

# Production Info
process.configurationMetadata = cms.untracked.PSet(
    annotation = cms.untracked.string('--python_filename nevts:-1'),
    name = cms.untracked.string('Applications'),
    version = cms.untracked.string('$Revision: 1.19 $')
)

# Other statements
from Configuration.AlCa.GlobalTag import GlobalTag
process.GlobalTag = GlobalTag(process.GlobalTag, '106X_upgrade2018_realistic_v16_L1v1', '')

if useIVF:
  process.vtxReco = cms.Sequence(
      process.inclusiveVertexFinderSoftDV *
      process.vertexMergerSoftDV *
      process.trackVertexArbitratorSoftDV *
      process.IVFSecondaryVerticesSoftDV
  )
  process.MLTree.vtx_token = cms.InputTag("IVFSecondaryVerticesSoftDV")
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
  process.MLTree.vtx_token = cms.InputTag("GNNVtxSoftDV")
elif useGNNIVF:
  process.vtxReco = cms.Sequence(
      process.vtxRecoGNN *
      process.inclusiveVertexFinderGNN * 
      process.vertexMergerGNN *
      process.trackVertexArbitratorGNN *
      process.GNNVtxSoftDV
  )
  process.MLTree.vtx_token = cms.InputTag("GNNVtxSoftDV")
elif useGNNAVR:
  process.GNNVtxSoftDV.secondaryVertices = cms.InputTag("vtxRecoGNN")
  process.vtxReco = cms.Sequence(
      process.vtxRecoGNN *
      process.GNNVtxSoftDV
  )
  process.MLTree.vtx_token = cms.InputTag("GNNVtxSoftDV")
elif useGNNAVRIVF:
  process.vertexMergerGNN.secondaryVertices = cms.InputTag("vtxRecoGNN")
  process.vtxReco = cms.Sequence(
      process.vtxRecoGNN *
      process.vertexMergerGNN *
      process.trackVertexArbitratorGNN *
      process.GNNVtxSoftDV
  )
  process.MLTree.vtx_token = cms.InputTag("GNNVtxSoftDV")
else:
  process.MFVSecondaryVerticesSoftDV = process.mfvVerticesMINIAOD.clone()
  process.vtxReco = cms.Sequence(
      process.MFVSecondaryVerticesSoftDV
  )
  process.MLTree.vtx_token = cms.InputTag("MFVSecondaryVerticesSoftDV")

## Output definition
#output_mod = cms.OutputModule("NanoAODOutputModule",
#    compressionAlgorithm = cms.untracked.string('LZMA'),
#    compressionLevel = cms.untracked.int32(9),
#    dataset = cms.untracked.PSet(
#        dataTier = cms.untracked.string('NANOAODSIM'),
#        filterName = cms.untracked.string('')
#    ),
#    fileName = cms.untracked.string('file:/users/ang.li/public/SoftDV/CMSSW_10_6_30/src/SoftDisplacedVertices/ML/test/NanoAOD.root'),
#    outputCommands = process.NANOAODSIMEventContent.outputCommands
#)
#
#process.NANOAODSIMoutput = output_mod

# Defining globally acessible service object that does not affect physics results.
import os
USER = os.environ.get('USER')
process.TFileService = cms.Service("TFileService", fileName = cms.string("/scratch-cbe/users/{0}/mltree.root".format(USER)))

process.reco_step = cms.Path(process.vtxReco + process.MLTree)
process.endjob_step = cms.EndPath(process.endOfProcess)

# Schedule definition
process.schedule = cms.Schedule(process.reco_step,
                                process.endjob_step
                                )


from PhysicsTools.PatAlgos.tools.helpers import associatePatAlgosToolsTask
associatePatAlgosToolsTask(process)
