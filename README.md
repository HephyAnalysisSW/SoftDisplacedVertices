# SoftDisplacedVertices
Framework for Soft Displaced Vertices analysis.

This package is currently in a preliminary stage. Tracks are selected and passed to the **InclusiveVertexFinder** to reconstruct secondary vertices.

The extension of standard MiniAOD and NanoAOD is done by applying the same set of conditions, calibrations, and alignments in the standard processing chain.  
For instance our 2018 RunII MC reprocessing chain is based on the following:  
 [SUS-chain_RunIISummer20UL18wmLHEGEN_flowRunIISummer20UL18SIM_flowRunIISummer20UL18DIGIPremix_flowRunIISummer20UL18HLT_flowRunIISummer20UL18RECO_flowRunIISummer20UL18MiniAODv2_flowRunIISummer20UL18NanoAODv9-00066](https://cms-pdmv.cern.ch/mcm/chained_requests?prepid=SUS-chain_RunIISummer20UL18wmLHEGEN_flowRunIISummer20UL18SIM_flowRunIISummer20UL18DIGIPremix_flowRunIISummer20UL18HLT_flowRunIISummer20UL18RECO_flowRunIISummer20UL18MiniAODv2_flowRunIISummer20UL18NanoAODv9-00066).

We first generate a customised version of [SUS-RunIISummer20UL18MiniAODv2-00068](https://cms-pdmv.cern.ch/mcm/requests?prepid=SUS-RunIISummer20UL18MiniAODv2-00068&page=0), \
and then a customised version of [SUS-RunIISummer20UL18NanoAODv9-00068](https://cms-pdmv.cern.ch/mcm/requests?prepid=SUS-RunIISummer20UL18NanoAODv9-00068&page=0).

For different MC files it might be worth checking:
 - [History of MC Production Campaigns](https://twiki.cern.ch/twiki/bin/viewauth/CMS/PdmVMcCampaigns)
 - [NanoAOD Specific Explanations for the MC Campaigns](https://gitlab.cern.ch/cms-nanoAOD/nanoaod-doc/-/wikis/home)
  
  
Check out the subdirectories of this repository to find more about the production.

## Instructions to Install
```
cmsrel CMSSW_10_6_30
cd CMSSW_10_6_30/src
cmsenv
git clone git@github.com:HephyAnalysisSW/SoftDisplacedVertices.git
git checkout new_CMSSW_2025March
scram b -j4
```

&nbsp;

## JME Uncertainty Calculations
To add the JME shifted variables to nanoAOD, do the following:
```
cd CMSSW_10_6_30/src
git clone git@github.com:alikaanguven/jetmet-uncertainties.git PhysicsTools/NanoAODTools
cd PhysicsTools/NanoAODTools
cmsenv
scram b
```
Then, follow the **README** of `jetmet-uncertainties` repository.