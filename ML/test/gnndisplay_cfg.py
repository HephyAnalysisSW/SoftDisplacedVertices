import FWCore.ParameterSet.Config as cms

import HLTrigger.HLTfilters.hltHighLevel_cfi as hlt
from SoftDisplacedVertices.VtxReco.VertexReco_cff import VertexRecoSeq

process = cms.Process('MLTree')

process.load('FWCore.MessageLogger.MessageLogger_cfi')
process.MessageLogger.cerr.FwkReport.reportEvery = 1

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
process.load("SoftDisplacedVertices.ML.GNNInference_cfi")
process.load("SoftDisplacedVertices.ML.GNNDisplay_cfi")

process.maxEvents = cms.untracked.PSet(
    input = cms.untracked.int32(100)
)

MessageLogger = cms.Service("MessageLogger")


# Input source
process.source = cms.Source("PoolSource",
    fileNames = cms.untracked.vstring(
      #'file:/eos/vbc/experiments/cms/store/user/lian/CustomMiniAOD_v3/stop_M600_588_ct200_2018/output/out_MINIAODSIMoutput_0.root',
      'file:/eos/vbc/experiments/cms/store/user/lian/CustomMiniAOD_v3_1/stop_M600_588_ct200_2018/output/out_MINIAODSIMoutput_0.root',
      #'file:/eos/vbc/experiments/cms/store/user/aguven/WJetsToLNu_HT-400To600_TuneCP5_13TeV-madgraphMLM-pythia8/WJetsToLNu_HT-400To600/240222_183335/0000/output_1.root',
      ),
    #fileNames = cms.untracked.vstring('file:/eos/vbc/experiments/cms/store/user/lian/CustomMiniAOD_v3_MLTraining_new/stop_M600_580_ct2_2018/output/out_MINIAODSIMoutput_0.root'),
    # fileNames = cms.untracked.vstring('file:/scratch-cbe/users/ang.li/SoftDV/MiniAOD_vtxreco/Stop_600_588_200/MINIAODSIMoutput_0.root'),
    #fileNames = cms.untracked.vstring('file:/eos/vbc/experiments/cms/store/user/liko/ZJetsToNuNu_HT-1200To2500_TuneCP5_13TeV-madgraphMLM-pythia8/ZJetsToNuNu_HT-1200To2500_MC_UL18_CustomMiniAODv1/231029_221242/0000/MiniAOD_1.root'),
    secondaryFileNames = cms.untracked.vstring()
)

process.options = cms.untracked.PSet(
    SkipEvent= cms.untracked.vstring("ProductNotFound"),
)

SimpleMemoryCheck = cms.Service("SimpleMemoryCheck",ignoreTotal = cms.untracked.int32(1) )

# Production Info
process.configurationMetadata = cms.untracked.PSet(
    annotation = cms.untracked.string('--python_filename nevts:-1'),
    name = cms.untracked.string('Applications'),
    version = cms.untracked.string('$Revision: 1.19 $')
)

# Other statements
from Configuration.AlCa.GlobalTag import GlobalTag
process.GlobalTag = GlobalTag(process.GlobalTag, '106X_upgrade2018_realistic_v16_L1v1', '')

process.TFileService = cms.Service("TFileService", fileName = cms.string("GNNTree.root") )

# Output definition
process.out = cms.OutputModule("PoolOutputModule",
    fileName = cms.untracked.string('vtxreco.root'),
    SelectEvents = cms.untracked.PSet(
      SelectEvents = cms.vstring('p'),
      ),
    outputCommands = cms.untracked.vstring(
      'keep *',
      )
)

# Defining globally acessible service object that does not affect physics results.
import os
USER = os.environ.get('USER')

#process.p = cms.Path(process.GNNInference)
process.p = cms.Path(process.GNNDisplay)

process.outp = cms.EndPath(process.out)

# Schedule definition
process.schedule = cms.Schedule(process.p,
                                process.outp,
                                )


from PhysicsTools.PatAlgos.tools.helpers import associatePatAlgosToolsTask
associatePatAlgosToolsTask(process)
