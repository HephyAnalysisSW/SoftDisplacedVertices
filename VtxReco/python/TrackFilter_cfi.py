import FWCore.ParameterSet.Config as cms

TrackFilter = cms.EDFilter("TrackFilter",
                        beamspot = cms.InputTag('offlineBeamSpot'),
                        primaryVertices = cms.InputTag('offlineSlimmedPrimaryVertices'),
                        packedPFCandidates = cms.InputTag("packedPFCandidates"),
                        lostTracks = cms.InputTag("lostTracks"),
                        generalTracks = cms.InputTag("generalTracks"),
                        pfIsolation_DR = cms.double(0.3),
                        pfIsolation_DZ = cms.double(0.1),
                        miniIsoParams = cms.vdouble(0.05, 0.2, 10.0), # (minDR, maxDR, kT) # dR for miniiso is max(minDR, min(maxDR, kT/pT))
                        min_track_nhits = cms.int32(6),
                        min_n_seed_tracks = cms.int32(0),
                        min_track_pt = cms.double(0.5), # 1.
                        min_track_dxy = cms.double(0),
                        min_track_nsigmadxy = cms.double(2),
                        max_track_normchi2 = cms.double(5),
                        max_track_dz = cms.double(999), # 4
                        max_track_sigmapt_ratio = cms.double(0.015),
                        histos = cms.bool(False),
                        )
