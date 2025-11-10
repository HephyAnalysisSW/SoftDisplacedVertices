#### Cornell vertex finder


import FWCore.ParameterSet.Config as cms

kvr_params = cms.PSet(
    maxDistance = cms.double(0.01),
    maxNbrOfIterations = cms.int32(10),
    doSmoothing = cms.bool(True),
)

MFVGenAOD = cms.EDProducer('MFVRecowithGenAOD',
                             kvr_params = kvr_params,
                             do_track_refinement = cms.bool(False), # remove tracks + trim out tracks with IP significance larger than trackrefine_sigmacut and trackrefine_trimmax, respectively   
                             resolve_split_vertices_loose = cms.bool(False), # an alternative merging routine with `loose` criteria, to merge any nearby vertices within a given dist or significance
                             resolve_split_vertices_tight = cms.bool(True), # merging routine, based on vtx dphi and dVV 
                             investigate_merged_vertices = cms.bool(False), # investigate quality cuts on merged vertices from tight merging 
                             resolve_shared_jets = cms.bool(True),       # shared-jet mitigation
                             resolve_shared_jets_src = cms.InputTag('ak4PFJets'), 
                             beamspot_src = cms.InputTag('offlineBeamSpot'),
                             seed_tracks_src = cms.InputTag('TrackFilter', 'seed'),
                             n_tracks_per_seed_vertex = cms.int32(2),
                             max_seed_vertex_chi2 = cms.double(5),
                             use_2d_vertex_dist = cms.bool(False),
                             use_2d_track_dist = cms.bool(False),
                             merge_anyway_dist = cms.double(-1),
                             merge_anyway_sig = cms.double(4), # merging criteria for loose merging (*only* if resolve_split_vertices_loose is True)
                             merge_shared_dist = cms.double(-1),
                             merge_shared_sig = cms.double(4), # default merging shared-track vertices  
                             max_track_vertex_dist = cms.double(-1),
                             max_track_vertex_sig = cms.double(5), # default track arbitration
                             min_track_vertex_sig_to_remove = cms.double(1.5), # default track arbitration
                             remove_one_track_at_a_time = cms.bool(True),
                             max_nm1_refit_dist3 = cms.double(-1),
                             max_nm1_refit_distz = cms.double(0.005),
                             max_nm1_refit_count = cms.int32(-1),
                             trackrefine_sigmacut = cms.double(5), # track refinement criteria (*only* if do_track_refinement = True)
                             trackrefine_trimmax = cms.double(5), # track refinement criteria (*only* if do_track_refinement = True)
                             histos = cms.untracked.bool(True),
                             histos_noshare = cms.untracked.bool(True),   # make plots of no shared-track vertices 
                             histos_output_afterdzfit = cms.untracked.bool(False),   # make plots of output vertices after the default vertexing 
                             histos_output_aftermerge = cms.untracked.bool(False),   # make plots of output vertices after the default vertexing  + tight merging routine turned on
                             histos_output_aftersharedjets = cms.untracked.bool(True),   # make plots of output vertices after the default vertexing  + tight merging routine turned on  + shared-jet mitigation turned on 
                             verbose = cms.untracked.bool(False),
                             gensrc = cms.InputTag("genParticles"),
                             pvToken = cms.InputTag("offlineSlimmedPrimaryVertices"),
                             )

MFVGenMINIAOD = cms.EDProducer('MFVRecowithGenMINIAOD',
                             kvr_params = kvr_params,
                             do_track_refinement = cms.bool(False), # remove tracks + trim out tracks with IP significance larger than trackrefine_sigmacut and trackrefine_trimmax, respectively   
                             resolve_split_vertices_loose = cms.bool(False), # an alternative merging routine with `loose` criteria, to merge any nearby vertices within a given dist or significance
                             resolve_split_vertices_tight = cms.bool(True), # merging routine, based on vtx dphi and dVV 
                             investigate_merged_vertices = cms.bool(False), # investigate quality cuts on merged vertices from tight merging 
                             resolve_shared_jets = cms.bool(True),       # shared-jet mitigation
                             resolve_shared_jets_src = cms.InputTag('slimmedJets'), 
                             beamspot_src = cms.InputTag('offlineBeamSpot'),
                             seed_tracks_src = cms.InputTag('TrackFilter', 'seed'),
                             n_tracks_per_seed_vertex = cms.int32(2),
                             max_seed_vertex_chi2 = cms.double(5),
                             use_2d_vertex_dist = cms.bool(False),
                             use_2d_track_dist = cms.bool(False),
                             merge_anyway_dist = cms.double(-1),
                             merge_anyway_sig = cms.double(4), # merging criteria for loose merging (*only* if resolve_split_vertices_loose is True)
                             merge_shared_dist = cms.double(-1),
                             merge_shared_sig = cms.double(4), # default merging shared-track vertices  
                             max_track_vertex_dist = cms.double(-1),
                             max_track_vertex_sig = cms.double(5), # default track arbitration
                             min_track_vertex_sig_to_remove = cms.double(1.5), # default track arbitration
                             remove_one_track_at_a_time = cms.bool(True),
                             max_nm1_refit_dist3 = cms.double(-1),
                             max_nm1_refit_distz = cms.double(0.005),
                             max_nm1_refit_count = cms.int32(-1),
                             trackrefine_sigmacut = cms.double(5), # track refinement criteria (*only* if do_track_refinement = True)
                             trackrefine_trimmax = cms.double(5), # track refinement criteria (*only* if do_track_refinement = True)
                             histos = cms.untracked.bool(True),
                             histos_noshare = cms.untracked.bool(True),   # make plots of no shared-track vertices 
                             histos_output_afterdzfit = cms.untracked.bool(False),   # make plots of output vertices after the default vertexing 
                             histos_output_aftermerge = cms.untracked.bool(False),   # make plots of output vertices after the default vertexing  + tight merging routine turned on
                             histos_output_aftersharedjets = cms.untracked.bool(True),   # make plots of output vertices after the default vertexing  + tight merging routine turned on  + shared-jet mitigation turned on 
                             verbose = cms.untracked.bool(False),
                             gensrc = cms.InputTag("genParticles"),
                             pvToken = cms.InputTag("offlineSlimmedPrimaryVertices"),
                             )
