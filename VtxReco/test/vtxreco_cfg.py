# import standard CMSSW modules
import FWCore.ParameterSet.Config as cms
import FWCore.Utilities.FileUtils as FileUtils
import HLTrigger.HLTfilters.hltHighLevel_cfi as hlt

# import Ang's custom CMSSW modules
from SoftDisplacedVertices.VtxReco.VertexReco_cff import VertexRecoSeq

# Set some Flags.
useMINIAOD = False
useIVF = True

#set up a process named VtxReco
process = cms.Process("VtxReco")


process.maxEvents = cms.untracked.PSet( input = cms.untracked.int32(3) )

inputDatafileList = FileUtils.loadListFromFile('/users/ang.li/public/SoftDV/CMSSW_10_6_30/src/SoftDisplacedVertices/VtxReco/test/filelist_stop4b_600_588_200.txt')

# configures the source that reads the input files
process.source = cms.Source("PoolSource",
  fileNames = cms.untracked.vstring(
    'file:/scratch-cbe/users/ang.li/antrag/stop4b_600_588_200/TestAntragIVF1_AODSIM_600_588_200_0.root',
    #'file:/users/ang.li/public/SoftDV/CMSSW_10_6_30/src/SoftDisplacedVertices/VtxReco/test/splitSUSY_M2000_1950_ctau1p0_AOD_2017.root',
    #'root://cms-xrd-global.cern.ch//store/mc/RunIISummer20UL17MiniAODv2/splitSUSY_M2000_1950_ctau1p0_TuneCP2_13TeV-pythia8/MINIAODSIM/106X_mc2017_realistic_v9-v2/80000/03435A66-8AC7-7B4C-9744-0D774D27E48B.root',
    #'root://cms-xrd-global.cern.ch//store/mc/RunIISummer20UL17MiniAODv2/splitSUSY_M2000_1950_ctau1p0_TuneCP2_13TeV-pythia8/MINIAODSIM/106X_mc2017_realistic_v9-v2/80000/12B0D985-23FA-1B45-B3F9-51E4F20B630B.root',
    #'root://cms-xrd-global.cern.ch//store/mc/RunIISummer20UL17MiniAOD/ZJetsToNuNu_HT-800To1200_TuneCP5_13TeV-madgraphMLM-pythia8/MINIAODSIM/106X_mc2017_realistic_v6-v1/00000/E5DF4692-A6EA-0545-B901-D071F3385AAB.root',
    #cms.untracked.vstring( *inputDatafileList)
  )
)
#process.source.duplicateCheckMode = cms.untracked.string('noDuplicateCheck')


# HLT trigger requirement
process.trig_filter = hlt.hltHighLevel.clone(
    HLTPaths = ['HLT_PFMET120_PFMHT120_IDTight_v*'],
    throw = False
    )


# load some modules
if useMINIAOD:
  process.load("SoftDisplacedVertices.VtxReco.TracksMiniAOD_cfi")
process.load("SoftDisplacedVertices.VtxReco.VertexReco_cff")
#process.load("SoftDisplacedVertices.VtxReco.Vertexer_cfi")

process.load("FWCore.MessageService.MessageLogger_cfi")
process.load("TrackingTools/TransientTrack/TransientTrackBuilder_cfi")
process.load('Configuration.StandardSequences.GeometryRecoDB_cff')
#process.load("Configuration.Geometry.GeometryIdeal_cff")
process.load("Configuration.StandardSequences.MagneticField_cff")
process.load('Configuration.StandardSequences.FrontierConditions_GlobalTag_cff')
#process.GlobalTag.globaltag = '106X_mc2017_realistic_v10'
process.GlobalTag.globaltag = '102X_upgrade2018_realistic_v15'

process.out.outputCommands.append('drop *')
if useMINIAOD:
  process.out.outputCommands.append('keep *_slimmedMETs_*_*')
  process.out.outputCommands.append('keep *_slimmedJets_*_*')
  process.out.outputCommands.append('keep *_offlineSlimmedPrimaryVertices_*_*')
else:
  process.out.outputCommands.append('keep *_pfMet_*_*')
  process.out.outputCommands.append('keep *_ak4PFJets_*_*')
  process.out.outputCommands.append('keep *_offlinePrimaryVertices_*_*')
  process.out.outputCommands.append('keep *_generalTracks_*_*')
process.out.outputCommands.append('keep *_offlineBeamSpot_*_*')
process.out.outputCommands.append('keep *_VertexTracks*_*_*')

if useIVF:
  process.out.outputCommands.append('keep *_inclusiveVertexFinderSoftDV_*_*')
  process.out.outputCommands.append('keep *_vertexMergerSoftDV_*_*')
  process.out.outputCommands.append('keep *_trackVertexArbitratorSoftDV_*_*')
  process.out.outputCommands.append('keep *_IVFSecondaryVerticesSoftDV_*_*')
else:
  process.out.outputCommands.append('keep *_MFVSecondaryVerticesSoftDV_*_*')

#process.out.outputCommands.append('keep *')

process.TFileService = cms.Service("TFileService", fileName = cms.string("vtxreco_histos.root") )


VertexRecoSeq(process, useMINIAOD=useMINIAOD, useIVF=useIVF)


# talk to output module
process.out = cms.OutputModule("PoolOutputModule",
    fileName = cms.untracked.string('vtxreco.root'),
    SelectEvents = cms.untracked.PSet(
      SelectEvents = cms.vstring('p'),
      ),
    outputCommands = cms.untracked.vstring(
      'drop *',
      )
)


# Defines which modules and sequences to run
process.p = cms.Path(process.trig_filter + process.vtxreco)

# A list of analyzers or output modules to be run after all paths have been run.
process.outp = cms.EndPath(process.out)
