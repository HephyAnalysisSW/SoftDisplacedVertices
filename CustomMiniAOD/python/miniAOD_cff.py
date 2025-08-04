import FWCore.ParameterSet.Config as cms

from PhysicsTools.PatAlgos.tools.helpers import getPatAlgosToolsTask

# # Commented out with as part of first attempt.
# from PhysicsTools.PatAlgos.slimming.isolatedTracks_cfi import isolatedTracks

def miniAOD_customise_SoftDisplacedVertices(process):

    task = getPatAlgosToolsTask(process)
    process.load('SoftDisplacedVertices.VtxReco.TrackFilter_cfi')
    process.TrackFilter.histos = cms.bool(False)
 
    task.add(process.TrackFilter)

    process.MINIAODEventContent.outputCommands.append('keep *_TrackFilter*_*_*')
    process.MINIAODSIMEventContent.outputCommands.append('keep *_TrackFilter*_*_*')

    # # First implementation: Clone here, match the isolated tracks with filtered tracks in the nanoAOD.
    # # add a new isolated tracks object.
    # process.isolatedTracksSoftDV = isolatedTracks.clone(
    #     pT_cut = cms.double(0.5),
    #     generalTracks = cms.InputTag("generalTracks"),
    # )
    # process.MINIAODEventContent.outputCommands.append('keep *_isolatedTracksSoftDV*_*_*')
    # process.MINIAODSIMEventContent.outputCommands.append('keep *_isolatedTracksSoftDV*_*_*')
    # task.add(process.isolatedTracksSoftDV)


    # Second attempt: Use a separate track filter and store isolation independently
    #                   in the same order as filtered tracks.
    # process.load('SoftDisplacedVertices.CustomMiniAOD.FilterIsolateTracks_cfi')
    # process.FilterIsolateTracks.histos = cms.bool(False)
    # task.add(process.FilterIsolateTracks)
    # process.MINIAODEventContent.outputCommands.append('keep *_FilterIso*_*_*')
    # process.MINIAODSIMEventContent.outputCommands.append('keep *_FilterIso*_*_*')


    # Get track isolations according to https://cmssdt.cern.ch/lxr/source/PhysicsTools/IsolationAlgos/python/goodTrackIsolations_cfi.py
    process.load('SoftDisplacedVertices.CustomMiniAOD.TrackPtIsolation_cfi')
    task.add(process.TrackPtIsolation)
    process.MINIAODEventContent.outputCommands.append('keep *_TrackPtIsolation_*_*')
    process.MINIAODSIMEventContent.outputCommands.append('keep *_TrackPtIsolation_*_*')

    return process

def miniAOD_customise_SoftDisplacedVerticesMC(process):

    process = miniAOD_customise_SoftDisplacedVertices(process)

    process.prunedGenParticlesWithStableCharged = process.prunedGenParticles.clone()
    process.prunedGenParticlesWithStableCharged.select.append("keep status == 1 && abs(charge) == 1 && pt > 0.5 && abs(eta) < 2.5")
    process.MINIAODSIMEventContent.outputCommands.append('keep recoGenParticles_prunedGenParticlesWithStableCharged_*_*')
    process.MINIAODSIMEventContent.outputCommands.append('keep recoGenParticles_genParticles_*_*')

    task = getPatAlgosToolsTask(process)
    task.add(process.prunedGenParticlesWithStableCharged)

    return process

def miniAOD_filter_SoftDisplacedVertices(process):

    process.pfMETSkim = cms.EDFilter(
        "METFilter",
        src = cms.InputTag("pfMet"),
        minMET = cms.double(140.),
    )
    process.Flag_pfMETSkim = cms.Path(process.pfMETSkim)
    process.schedule.append(process.Flag_pfMETSkim)

    # at this point one does not understand why that did not work ...
    
    # process.pfMETSelectorHighMETSkim = cms.EDFilter(
    #     "CandViewSelector",
    #     src = cms.InputTag("pfMet"),
    #     cut = cms.string( "pt()>200" ),
    #     filter = cms.untracked.bool(True)
    # )
    # process.Flag_pfMETSelectorHighMETSkim = cms.Path(process.pfMETSelectorHighMETSkim)
    # process.schedule.append(process.Flag_pfMETSelectorHighMETSkim)

    # process.MINIAODSIMoutput.SelectEvents = cms.untracked.PSet(SelectEvents = cms.vstring('Flag_pfMETSelectorHighMETSkim'))

    if hasattr(process, 'MINIAODoutput'):
        process.MINIAODoutput.SelectEvents = cms.untracked.PSet(SelectEvents = cms.vstring('Flag_pfMETSkim'))
    elif hasattr(process, 'MINIAODSIMoutput'):
        process.MINIAODSIMoutput.SelectEvents = cms.untracked.PSet(SelectEvents = cms.vstring('Flag_pfMETSkim'))
    else:
        print("WARNING: No MINIAOD[SIM]output definition")

    return process

def miniAOD_trigger_isomu(process):
    process.load("HLTrigger.HLTfilters.hltHighLevel_cfi")
    process.hltHighLevel = process.hltHighLevel.clone(
        HLTPaths = ['HLT_IsoMu24_v*', 'HLT_IsoMu27_v*'],
        throw = False,
        eventSetupPathsKey = '',
        andOr = True,  # True means OR, False means AND
    )
    process.Flag_HLT_IsoMu24_27 = cms.Path(process.hltHighLevel)
    process.schedule.append(process.Flag_HLT_IsoMu24_27)

    if hasattr(process, 'MINIAODoutput'):
        process.MINIAODoutput.SelectEvents = cms.untracked.PSet(SelectEvents = cms.vstring('Flag_HLT_IsoMu24_27'))
    elif hasattr(process, 'MINIAODSIMoutput'):
        process.MINIAODSIMoutput.SelectEvents = cms.untracked.PSet(SelectEvents = cms.vstring('Flag_HLT_IsoMu24_27'))
    else:
        print("WARNING: No MINIAOD[SIM]output definition")

    return process



