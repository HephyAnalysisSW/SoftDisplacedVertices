# SoftDisplacedVertices
Framework for Soft Displaced Vertices analysis.

This branch `CMSSW_13_0_16` is used to submit **Run3** processings which require version 13_0_16 of CMSSW. So far only 2022, and 2023 data & MC are processed. One should check if the same setup works also for 2024 or not.

Multiple tools are developed to ensure all the lumi sections are processed well, and not to give rise to any duplicates. Inconsistencies can show up at any stage. Some examples could be:
- CRAB might show the data transfer postproc. has failed, but in reality the files might have reached the destination: https://cms-talk.web.cern.ch/t/crab-generates-more-outputs-than-the-ones-listed-in-dataset/51490
- CRAB can produce corrupted files and might not show that the job has failed: https://cms-talk.web.cern.ch/t/crab-produces-corrupted-file-and-does-not-fail/45888
- TAPERECALL jobs might stall for site related issues for a long time: https://cms-talk.web.cern.ch/t/crab-is-not-aware-that-the-dataset-is-replicated/45305/2

Some of these cannot be avoided but can be checked manually. You can use the directory `CustomMiniAOD/testK/checks` for this.

You can also find some addtional documentations here if you need them: https://github.com/alikaanguven/CMS_helpers/tree/main


## Instructions to Install
```
cmsrel CMSSW_13_0_16
cd CMSSW_13_0_16/src
cmsenv
git clone git@github.com:HephyAnalysisSW/SoftDisplacedVertices.git
git checkout CMSSW_13_0_16
scram b -j4
```
