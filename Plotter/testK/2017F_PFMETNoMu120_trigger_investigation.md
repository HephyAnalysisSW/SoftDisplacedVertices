# Investigation of the 2017F `HLT_PFMETNoMu120_PFMHTNoMu120_IDTight` inefficiency

## Scope

This note documents the event-level investigation of the apparent high-recoil
inefficiency of
`HLT_PFMETNoMu120_PFMHTNoMu120_IDTight` in the 2017F SingleMuon data.

The input sample is the `isomu2017f` directory specified in
`/eos/vbc/experiments/cms/store/user/wuzh/finaljson/Data_IsoMu2017.json`:

```text
/eos/vbc/experiments/cms/store/user/wuzh/SingleMuon/Run2017F_nano_v1
```

The scan covered 543 NanoAOD files and 199,503,358 event entries. All files
were read successfully.

The event selection reproduced the Run-2 trigger-efficiency configuration:

- all standard MET cleaning filters;
- exactly one tight muon with `pt > 30 GeV` and `abs(eta) < 2.4`;
- `HLT_IsoMu27`;
- the 2017F MET XY correction;
- offline muon-subtracted MET above 800 GeV;
- a false `HLT_PFMETNoMu120_PFMHTNoMu120_IDTight` decision.

Here, the offline muon-subtracted MET is formed by adding the selected tight
muon momentum to the corrected PF MET. Additional non-tight muons are not
added back.

## Event counts

There are 477 selected events above 800 GeV. The exact 120 GeV path accepts
442 and rejects 35, giving a raw path efficiency of 92.66%.

| Classification of the 35 rejected events | Events |
|---|---:|
| `HLT_PFMETNoMu140_PFMHTNoMu140_IDTight` accepts | 25 |
| A different high-MET trigger accepts | 2 |
| No inspected high-MET trigger accepts | 8 |

The 120-or-140 no-muon trigger OR accepts 467/477 events (97.90%). Including
the other high-MET paths accepts 469/477 events (98.32%). These OR efficiencies
are diagnostic numbers rather than substitutes for a luminosity-section-aware
trigger definition.

## Prescale pattern in 2017F

The supplied prescale map is:

```text
/users/alikaan.gueven/.codex/attachments/bd8214ff-d0e2-4bce-b7ef-25a5e82b01dd/
HLT_PFMETNoMu120_PFMHTNoMu120_IDTight_v_runlumis_allprescales.json
```

Although the file covers several data-taking years, only values 0 and 1 occur
in the nominal 2017F run range:

- `0`: the path is masked or disabled;
- `1`: the path is active and unprescaled.

The integer convention is an inverse acceptance fraction. A prescale `N > 1`
accepts approximately one in every `N` events passing the trigger conditions;
it never makes an event failing those conditions pass. The trigger decision is
the logical AND of the physics filters and the prescale gate.

Among the 137 2017F runs represented in the prescale file:

| Run behaviour | Runs |
|---|---:|
| Always unprescaled | 82 |
| Always disabled | 13 |
| Contains both disabled and unprescaled luminosity sections | 42 |

Representative transitions are:

- run 305282: prescale 0 in LS 1--72 and prescale 1 from LS 73;
- run 306125: prescale 0 in LS 1--342 and prescale 1 from LS 343;
- run 306456: prescale 0 in LS 1--483 and prescale 1 from LS 484.

CMS uses predefined prescale columns for different instantaneous-luminosity
and pileup conditions. The active column may change between luminosity
sections. Near the beginning of a high-luminosity fill, a lower-threshold path
can be disabled to control the trigger rate and storage bandwidth. As the
luminosity decreases, the path can be enabled without exceeding the rate
budget. The CMS Run-2 HLT paper describes this operational strategy in
Sections 2 and 3.3 [1]. The CMS Level-1 trigger paper describes the analogous
prescale columns used to maintain the Level-1 rate below approximately 100 kHz
[2]. The CMSSW HLT documentation gives the luminosity-section granularity and
the relation between the Level-1 and HLT prescale sets [3].

Matching the 35 rejected events to the supplied prescale map gives:

| Event category | Prescale 0 | Prescale 1 |
|---|---:|---:|
| No-muon 140 path accepts | 25 | 0 |
| Another high-MET path accepts | 0 | 2 |
| No high-MET path accepts | 2 | 6 |

Thus, all 25 events accepted by the no-muon 140 path occur while the exact
120 path is disabled. The prescale map directly explains their false 120-path
bits. Restricting the efficiency denominator to prescale-1 luminosity sections
leaves 450 events, of which 442 pass: 98.22%.

## The eight events not accepted by another high-MET path

| Run:lumi:event | Prescale | No-muon MET [GeV] | CaloMET [GeV] | Approx. muon-subtracted jet MHT [GeV] | Leading jet pT [GeV] | Leading-jet `muonSubtrFactor` |
|---|---:|---:|---:|---:|---:|---:|
| 305186:74:103852996 | 1 | 853 | 48 | 10 | 913 | 0.98 |
| 305247:171:242451041 | 1 | 18,017 | 46 | 203 | 18,304 | 0.99 |
| 305312:6:9670671 | 1 | 6,207 | 49 | 103 | 6,960 | 0.98 |
| 305377:546:988323676 | 1 | 1,489 | 64 | 34 | 1,627 | 0.99 |
| 305636:121:141290740 | 1 | 1,175 | 38 | 115 | 1,333 | 0.98 |
| 306125:811:1470178737 | 1 | 3,503 | 66 | 10 | 3,846 | 0.99 |
| 306135:41:76258419 | 0 | 1,097 | 67 | 20 | 1,173 | 0.98 |
| 306456:257:454340704 | 0 | 993 | 40 | 13 | 1,073 | 0.99 |

All eight events have low CaloMET and a leading jet whose momentum is almost
entirely removed by the NanoAOD muon-subtraction prescription. The nominal
high recoil is track or PF driven rather than calorimetric. Six remain relevant
after requiring prescale 1.

These events also have no inspected Level-1 ETM or ETMHF decision. This is
consistent with the absence of genuine calorimetric recoil; it is not evidence
that a TeV-scale calorimeter object was lost at Level 1.

## Clear prescale-1 pathology

### Run 305247, LS 171, event 242451041

Source:

```text
/eos/vbc/experiments/cms/store/user/wuzh/SingleMuon/Run2017F_nano_v1/
250925_115029/0000/output_126.root, Events entry 289997
```

This event has an unprescaled 120 path. Its reconstructed 18.3 TeV jet and
80.7 TeV jet energy are impossible in a 13 TeV collision, so it is a useful
unambiguous control example.

| Object | pT [GeV] | eta | phi | Approx. energy [GeV] | Interpretation |
|---|---:|---:|---:|---:|---|
| Tight trigger muon | 69.0 | -1.944 | 2.109 | 246 | Good isolated muon |
| Second muon candidate | 66.7 | -2.159 | 0.008 | 293 | Bad, non-PF muon |
| Pathological jet | 18,304 | -2.164 | 0.013 | 80,733 | Unphysical track-driven object |
| Largest ordinary jet | 65.8 | -1.710 | -0.351 | 188 | Modest hadronic activity |

The selected muon is tight and high purity, has a relative pT uncertainty of
2.9%, PF relative isolation 0.0023, and a matching HLT muon object. It is not
the pathology.

The second muon fails loose, medium and tight identification. It is not a PF
candidate or high-purity track, has a relative pT uncertainty of 118%,
`dxy = 1.28 cm`, `dz = 15.0 cm`, and lies within `DeltaR = 0.008` of the
pathological jet.

The PF MET is 17,989 GeV and is opposite the pathological jet,
`DeltaPhi = 3.139`. CaloMET is only 45.9 GeV. There is no independent jet
balancing the apparent 18 TeV momentum.

## Less obvious prescale-1 pathology

### Run 305636, LS 121, event 141290740

Source:

```text
/eos/vbc/experiments/cms/store/user/wuzh/SingleMuon/Run2017F_nano_v1/
250925_115029/0000/output_278.root, Events entry 52574
```

This event also has prescale 1. The nominal 1.33 TeV leading jet is
kinematically possible, the standard bad-PF-muon filters pass, and the event
contains a genuine 163 GeV hadronic jet. It is therefore a more subtle case.

| Object | pT [GeV] | eta | phi | Approx. energy [GeV] | Interpretation |
|---|---:|---:|---:|---:|---|
| Selected tight muon | 206.5 | 1.143 | 2.669 | 357 | Good isolated trigger muon |
| Additional muon | 1,221.5 | -0.174 | -2.423 | 1,240 | Poor-quality high-pT muon |
| Leading jet | 1,333 | -0.173 | -2.423 | 1,354 | Dominated by additional muon |
| Tight-muon jet | 248 | 1.145 | 2.673 | 430 | Dominated by selected muon |
| Genuine hadronic jet | 163 | 0.412 | -0.231 | 177 | Real but insufficient recoil |

The 206.5 GeV trigger muon passes tight and high-pT identification, has a
high-purity track, PF relative isolation consistent with zero, a relative pT
uncertainty of 2.8%, and a matching trigger object. The 248 GeV jet at the same
direction is 95.3% muon energy. It is not an independent hadronic jet. Jet
clustering includes the muon itself, while the isolation calculation excludes
the muon from the surrounding-energy sum.

The additional 1.22 TeV muon is PF and loose but fails medium, tight and
high-pT identification. It is not high purity, has only three tracker layers,
`dxy = 0.146 cm`, `dz = -0.190 cm`, `sip3d = 49.4`, and a relative pT
uncertainty of 25%. Its very small numerical isolation does not validate it:
an isolated, catastrophically mismeasured track can still have zero surrounding
activity.

The leading jet is aligned with this additional muon to
`DeltaR = 0.00053`. Its muon energy fraction and `muonSubtrFactor` are both
98.4%. Removing the associated muon leaves only about 19 GeV of raw jet pT.
The independent 163 GeV jet is separated from it by `DeltaPhi = 2.19` and
cannot balance the apparent TeV momentum.

The event-level missing-momentum values are:

| Quantity | Magnitude [GeV] | phi |
|---|---:|---:|
| NanoAOD PF MET | 1,240.1 | 0.709 |
| XY-corrected PF MET | 1,240.3 | 0.699 |
| Offline no-muon MET using only the selected tight muon | 1,175.5 | 0.862 |
| CaloMET | 37.5 | - |

The PF MET is almost opposite the additional muon,
`DeltaPhi = 3.122`. Adding both PF muons back to the corrected PF MET reduces
the inferred no-muon recoil to approximately 177 GeV. The independently
constructed muon-subtracted jet MHT is approximately 115 GeV.

The selected isolated muon is therefore not a jet misidentified as a muon.
The event contains a separate poor-quality muon or track that is clustered
into a nominal jet and creates fake PF MET. NanoAOD alone cannot determine
whether its detector origin is a cosmic muon, a decay in flight, hadronic
punch-through, or another tracking failure; AOD-level track and hit information
would be required.

## L1 prefiring interpretation

Appendix A of the CMS Level-1 trigger paper describes a 2016--2017 ECAL timing
shift that can assign forward ECAL trigger primitives to BX-1 [2]. A full
BX-1 Level-1 accept can prevent the BX0 event from being recorded. Such events
cannot be recovered from an `IsoMu27`-recorded sample. A residual effect is
possible when early trigger primitives do not cause a BX-1 accept but bias the
BX0 Level-1 objects.

The observed 2017F candidates do not support prefiring as their principal
cause:

- the 25 genuine-recoil events accepted by the no-muon 140 path all occur at
  prescale 0 for the 120 path;
- the six prescale-1 events accepted by no high-MET path have low CaloMET and
  muon-dominated leading jets;
- their large PF MET disappears when the additional bad-muon contribution is
  removed;
- the ECAL nominal non-prefiring weight is 1.0 for the less obvious event.

Residual ECAL prefiring remains a legitimate trigger-efficiency uncertainty,
but it does not explain the identified 2017F tail.

## Analysis implications

1. Measure the exact-path efficiency only in luminosity sections where its
   effective prescale is 1.
2. Do not count prescale-0 decisions as trigger inefficiency.
3. Treat a trigger OR using luminosity-section-aware availability and effective
   luminosities rather than a year-wide Boolean OR alone.
4. Construct the offline no-muon recoil using all relevant PF muons, or add a
   dedicated rejection for jets with extreme `muonSubtrFactor`.
5. Inspect PF MET, track MET and CaloMET together when diagnosing the high-MET
   tail. A large PF and track MET accompanied by small CaloMET is a strong sign
   of a track-driven pathology.

## References

1. CMS Collaboration, *Performance of the CMS high-level trigger during LHC
   Run 2*, JINST 19 (2024) P11021,
   <https://arxiv.org/abs/2410.17038>.
2. CMS Collaboration, *Performance of the CMS Level-1 trigger in proton-proton
   collisions at sqrt(s) = 13 TeV*, JINST 15 (2020) P10017,
   <https://arxiv.org/abs/2006.10165>.
3. CMS, *SWGuideHighLevelTrigger: HLT Prescales*,
   <https://twiki.cern.ch/twiki/bin/view/CMSPublic/SWGuideHighLevelTrigger#HLT_Prescales>.
4. CMS CMSSW NanoAOD DQM definition of `muonSubtrFactor`,
   <https://github.com/cms-sw/cmssw/blob/master/PhysicsTools/NanoAOD/python/nanoDQM_cfi.py>.
