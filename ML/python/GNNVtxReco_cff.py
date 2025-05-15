import FWCore.ParameterSet.Config as cms

from RecoVertex.AdaptiveVertexFinder.inclusiveVertexFinder_cfi import *
from RecoVertex.AdaptiveVertexFinder.vertexMerger_cfi import *
from RecoVertex.AdaptiveVertexFinder.trackVertexArbitrator_cfi import *
from SoftDisplacedVertices.ML.GNNInference_cfi import GNNInference

vtxRecoGNN = GNNInference.clone()

inclusiveVertexFinderGNN = inclusiveVertexFinder.clone(
    primaryVertices = cms.InputTag('offlineSlimmedPrimaryVertices'),
    tracks = cms.InputTag("vtxRecoGNN"),
    #tracks = cms.InputTag("TrackFilter","seed"),
    minPt = 0.5,
    )

vertexMergerGNN = vertexMerger.clone(
    #secondaryVertices = cms.InputTag("vtxRecoGNN"),
    secondaryVertices = cms.InputTag("inclusiveVertexFinderGNN"),
    )

trackVertexArbitratorGNN = trackVertexArbitrator.clone(
    primaryVertices = cms.InputTag('offlineSlimmedPrimaryVertices'),
    secondaryVertices = cms.InputTag("vertexMergerGNN"),
    #tracks = cms.InputTag("TrackFilter","seed"),
    tracks = cms.InputTag("vtxRecoGNN"),
    )

GNNVtxSoftDV = vertexMerger.clone(
    #secondaryVertices = "trackVertexArbitratorGNN",
    secondaryVertices = "vtxRecoGNN",
    maxFraction = 0.2,
    minSignificance = 10.,
)

inclusiveVertexFinderGNN.minPt = cms.double(0.5)
inclusiveVertexFinderGNN.minHits = cms.uint32(6)
inclusiveVertexFinderGNN.maximumLongitudinalImpactParameter = cms.double(20.)
inclusiveVertexFinderGNN.vertexMinAngleCosine = cms.double(0.00001)
inclusiveVertexFinderGNN.clusterizer.clusterMinAngleCosine = cms.double(0.00001) #new
inclusiveVertexFinderGNN.clusterizer.distanceRatio = cms.double(1) #new
#trackVertexArbitratorGNN.distCut = cms.double(0.1)
trackVertexArbitratorGNN.trackMinPixels = cms.int32(0)
trackVertexArbitratorGNN.dRCut = cms.double(5.0)
trackVertexArbitratorGNN.sigCut = cms.double(999)
trackVertexArbitratorGNN.distCut = cms.double(999)
trackVertexArbitratorGNN.dLenFraction = cms.double(1.2)
trackVertexArbitratorGNN.trackMinPixels = cms.int32(0)
