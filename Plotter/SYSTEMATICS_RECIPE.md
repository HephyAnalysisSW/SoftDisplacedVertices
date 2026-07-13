# Recipe: JEC / JER / Pileup / Unclustered-MET systematic uncertainties for signal samples

This note describes how to evaluate the effect of the following systematic
uncertainties on the signal yields in the analysis regions
(`MET350SP3/SP2/SP1/SP0` defined in the `limitcalc_*` configs):

* Jet energy correction (JEC / JES)
* Jet energy resolution (JER)
* Pileup reweighting (PU)
* Unclustered MET energy (`CMS_EXO24033_scale_met_unclustered_energy`)

It is based on the current state of:

* `python/plotter.py`
* `autoplotter.py`
* `configs/AN-25-092_limitcalc_Run2.yaml` (2017 / 2018)
* `configs/AN-25-092_limitcalc_Run3.yaml` (2022Pre / 2022Post / 2023Pre / 2023Post / 2024)
* `RDF_JERC.h`, `data/JecConfigAK4.json`

> **STATUS: IMPLEMENTED.** All variations described below are now implemented in
> `python/plotter.py` and `RDF_JERC.h`, steered by a single config knob
> `corrections: JERC_syst:` with values
> `nom` (default) / `jes_up` / `jes_down` / `jer_up` / `jer_down` /
> `unclust_up` / `unclust_down`, plus the PU `mode` for pileup.
> Use `make_syst_configs.py` to (re)generate the variant configs from the
> nominal analysis configs:
>
> ```bash
> python3 make_syst_configs.py --config configs/AN-25-092_limitcalc_Run2.yaml configs/AN-25-092_limitcalc_Run3.yaml
> ```
>
> which produces `configs/AN-25-092_limitcalc_{Run2,Run3}_{puUp,puDown,jesUp,jesDown,jerUp,jerDown,unclUp,unclDown}.yaml`.
> Then run autoplotter on the signal samples with each variant config and a
> matching `--postfix`. The variant configs are **MC-only** (the plotter refuses
> to run them with `--data`). The sections below document what each variation
> does and where it is implemented.

---

## 0. General strategy

For every systematic, produce **one extra pair of histogram sets (Up / Down)**
per signal sample and year, in addition to the nominal one, and compare the
per-region yields:

```
unc(region) = ( N_var(region) - N_nom(region) ) / N_nom(region)
```

Practical points that hold for all three systematics:

* Use a **copied config** per variation (never edit the nominal config in
  place), e.g. `configs/AN-25-092_limitcalc_Run3_puUp.yaml`, and tag the output with
  `--postfix` (or a separate `--output` directory) so files are named
  `<sample>_hist_puUp.root` etc.
* The command is the usual autoplotter one, e.g. (Run 2, 2018):

  ```bash
  python3 autoplotter.py \
      --sample stop_M600_580_ct2_2018 \
      --output ./syst/puUp \
      --config configs/AN-25-092_limitcalc_Run2_puUp.yaml \
      --lumi 59683. \
      --json <your>.json --metadata <metadata>.yaml --datalabel <label> \
      --year 2018 --postfix _puUp
  ```

  and for Run 3 the same with `configs/AN-25-092_limitcalc_Run3_puUp.yaml`,
  `--year 2022Pre|2022Post|2023Pre|2023Post|2024` and the corresponding lumi.
  With `--submit` the same works through the batch machinery.
* Yields per region: take the integral of any always-filled event histogram
  (e.g. `MET_pt_corr` in the `<region>_evt` directory, including
  over/underflow), or the `evt_weight` sums in the pickle output (Run 3 config
  has `savepkl: evt_weight`). Then feed nominal/up/down into the datacard
  writer as `lnN` (or shape) nuisances.

Two qualitatively different mechanisms:

* **PU** only changes the *event weight* → no event migration, config-only.
* **JEC / JER** change *jet pT and MET* → events migrate across
  `MET_pt_corr>250/350`, `leadingjet_pt>100`, `nJet_sel>0`,
  `dphi_MET_jet0` cuts. The variation must therefore be applied to the
  kinematic variables **before** the selection, and propagated to MET.

---

## 1. Pileup (Run 2 **and** Run 3) — config-only, no code change

The PU weight is computed in `plotter.py::applyCorrections`:

```python
d = d.Define("puweight", 'pu->evaluate({Pileup_nTrueInt,"<mode>"})')
```

where `<mode>` comes from `corrections: PU: "<year>": mode:` in the YAML.
The LUM-POG `puWeights` correctionlib files (both the Run 2 UL
`Collisions17/18_UltraLegacy_goldenJSON` and the Run 3
`Collisions2022/2023/24_..._GoldenJson` sets) accept the systematic strings
`"nominal"`, `"up"`, `"down"`.

**Steps (identical for Run 2 and Run 3):**

1. Copy the config twice:
   * `AN-25-092_limitcalc_Run2_puUp.yaml` / `AN-25-092_limitcalc_Run2_puDown.yaml`
   * `AN-25-092_limitcalc_Run3_puUp.yaml` / `AN-25-092_limitcalc_Run3_puDown.yaml`
2. In each copy, change **every** year block under `corrections: PU:`:

   ```yaml
   corrections:
     PU:
       "2018":
         path: ...          # unchanged
         name: ...          # unchanged
         mode: "up"         # was "nominal"  ("down" in the Down config)
   ```
3. Run autoplotter on the signal samples with `--postfix _puUp` / `_puDown`.
4. Compare region yields to nominal. Since only the weight changes, migration
   is zero; the uncertainty is a pure normalisation effect per region.

---

## 2. JEC and JER — Run 3 (2022Pre/Post, 2023Pre/Post, 2024)

### How the nominal works today

For Run 3, `AN-25-092_limitcalc_Run3.yaml` has `corrections: JERC: True`, and
`plotter.py` recomputes jets and Type-1 MET on the fly:

* `setJERC()` (plotter.py:106) loads **only the nominal** evaluators —
  `jesmode = "JesNominal"`, `jermode = "JerNominal"` are hard-coded — into the
  C++ map `jerc_refs`.
* `AddJERCVars()` (plotter.py:264) defines
  `Jet_pt_corr` / `Jet_mass_corr` via `JERC_jet_MC(...)` and
  `MET_pt_corr` / `MET_phi_corr` via `JERC_MET_MC(...)` (in `RDF_JERC.h`).
* Everything downstream (`jet_sel_mapveto`, `presel`, the `MET350SP*`
  regions) uses `Jet_pt_corr` / `MET_pt_corr`, so **any variation implemented
  inside these two Defines propagates automatically to the whole analysis.**

The uncertainty inputs are *already prepared* in `data/JecConfigAK4.json`
under `ApplyOnMC` for every year:

* `JesUncertaintySet`:
  * `JesUncertaintySetTotal` → single source `CMS_scale_j_Total`
  * `JesUncertaintySetReduced` → 11 regrouped sources (`CMS_scale_j_Absolute`, …)
  * `JesUncertaintySetFull` → all ~28 sources
* `JerNominal.tagNameJerSFUncertainty` → JER-SF uncertainty tag
* `JerUncertaintySet`: eta/pt windows for split JER sources
  (`JerUncertaintySetTotal` → `CMS_res_j_<year>` covers all jets)

The plumbing in `plotter.py` / `RDF_JERC.h` is implemented as follows
(kept here as documentation of what the code does):

### Code changes (implemented)

1. **`plotter.py::setJERC`** — in the MC branch, additionally load the
   uncertainty refs into `jerc_refs`:

   ```python
   # JES total uncertainty
   jesunc_tag = jercconf[self.year]['ApplyOnMC']['JesUncertaintySet']['JesUncertaintySetTotal']['CMS_scale_j_Total']
   jercloadcmd += 'jerc_refs.insert({{"MC_jes_unc",jercf->at("{}")}});'.format(jesunc_tag)
   # JER SF uncertainty
   jersfunc_tag = jercconf[self.year]['ApplyOnMC']['JerNominal']['tagNameJerSFUncertainty']
   jercloadcmd += 'jerc_refs.insert({{"MC_jer_sf_unc",jercf->at("{}")}});'.format(jersfunc_tag)
   ```

2. **`RDF_JERC.h`** — add a `const std::string& syst` argument (values
   `"nom"`, `"jes_up"`, `"jes_down"`, `"jer_up"`, `"jer_down"`) to
   `JEC_jet`, `JER_jet_MC`, `JERC_jet_MC`, `JERC_MET` (+ the
   `JERC_MET_MC` wrapper):

   * **JES:** in `JEC_jet` (and in the corresponding block of `JERC_MET`,
     after the L2 step), for MC evaluate the fractional uncertainty and shift
     the fully-corrected pt/mass:

     ```cpp
     if (syst=="jes_up" || syst=="jes_down") {
         double delta = jerc.at("MC_jes_unc")->evaluate({jet_eta[i], pt_corr});
         double shift = (syst=="jes_up") ? (1.0+delta) : (1.0-delta);
         pt_corr   *= shift;
         mass_corr *= shift;
     }
     ```

     The shift must be applied **before** the JER smearing (so the smear uses
     the shifted pt) and, in `JERC_MET`, before `dpt = pt_corr - pt_corrL1`
     so that Type-1 MET picks it up consistently.

   * **JER:** in `JER_jet_MC` (and the JER block of `JERC_MET`), vary the
     scale factor before calling the smear evaluator. First check the SF
     correction's inputs (`python3 -c "import correctionlib; ..."` or
     `correction summary <json>`): if the `ScaleFactor` tag accepts a
     `systematic` string, use
     `sf = jer[1]->evaluate({jet_eta[i], jet_pt[i], "up"/"down"})`;
     otherwise use the loaded `MC_jer_sf_unc` tag and set
     `sf → sf ± sf_unc`.

3. **Config/CLI knob** — make the syst string reachable from the YAML, e.g.

   ```yaml
   corrections:
     JERC: True
     JERC_syst: "jes_up"     # nom / jes_up / jes_down / jer_up / jer_down
   ```

   and in `AddJERCVars` append it to the Define strings:

   ```python
   syst = self.cfg['corrections'].get('JERC_syst','nom')
   d = d.Define('JERC_jet_ptmass','JERC_jet_MC(jerc_refs, ..., "{}")'.format(syst))
   d = d.Define('JERC_MET_ptphi','JERC_MET_MC(jerc_refs, ..., "{}")'.format(syst))
   ```

### Running

1. Make four config copies of `AN-25-092_limitcalc_Run3.yaml`, differing only in
   `JERC_syst`: `_jesUp`, `_jesDown`, `_jerUp`, `_jerDown`.
2. Run autoplotter for each signal sample × year × variation with matching
   `--postfix`.
3. Compare per-region yields with nominal. Here both **normalisation and
   migration** effects are included, since the shifted
   `Jet_pt_corr`/`MET_pt_corr` feed the trigger-emulating cuts, `presel` and
   the region definitions.

For datacards with split sources, loop the same machinery over
`JesUncertaintySetReduced` (JES) and the `JerUncertaintySetFull` eta/pt
windows (JER: apply the SF variation only to jets inside the window);
`Total` is the recommended starting point for a first estimate.

### Implementation notes (as built)

* `jes_up/down` and `jer_up/down` are handled **inside**
  `JERC_jet_MC` / `JERC_MET_MC` (extra `syst` argument, default `"nom"`), so
  `Jet_pt_corr`, `Jet_mass_corr`, `MET_pt_corr`, `MET_phi_corr` are varied
  consistently. The `"nom"` path is bit-identical to the previous code.
* The Run 3 jet **selections** (`jet_sel`, `bjet*`, `leadingjet_pt`) cut on the
  *stored* `Jet_pt` (production JEC), not on `Jet_pt_corr`. For `jes_up/down`
  the stored `Jet_pt`/`Jet_mass` are therefore additionally shifted on top by
  the same total-JES delta (`JES_vary_onTop` + `Redefine` in
  `Plotter.ApplyJERCSystRun3`), so the selection migration is included.
* For `jer_up/down` the stored `Jet_pt` is deliberately **not** varied: the
  stored Run 3 jets are unsmeared, so no nominal smearing exists there to
  vary; the JER variation enters through `Jet_pt_corr` and `MET_pt_corr`.
* JER SF variation uses the `SFUncertainty` correction
  (`tagNameJerSFUncertainty` in `JecConfigAK4.json`):
  `sf_var = sf ± sf_unc` (inputs `(JetEta, JetPt)`, verified for all years).

---

## 3. JEC and JER — Run 2 (2017 / 2018)

### The situation is different

`AN-25-092_limitcalc_Run2.yaml` has `corrections: JERC: False`: no on-the-fly
recorrection. The Run 2 custom NanoAOD jets (`Jet_pt`) are **already fully
JEC-corrected and JER-smeared** at production time (AK4 **CHS** jets,
NanoAODv9), and `MET_pt_corr`/`MET_phi_corr` are simply the **xy-corrected**
stored MET (`SDV::METXYCorr_Met_MetPhi` in `AddVars`).

The variation must therefore be applied **on top of the stored, corrected
objects**, using **AK4PFchs** corrections (the NanoAODv15-recomputed entries
in `JecConfigAK4.json` are AK4PFPuppi and do not apply to these jets):

### Code changes (implemented)

1. **`data/JecConfigAK4.json`** — a `CHS` block per Run 2 year pointing to
   the official jsonpog-integration files
   (`/cvmfs/cms.cern.ch/rsync/cms-nanoAOD/jsonpog-integration/POG/JME/2017_UL(2018_UL)/jet_jerc.json.gz`),
   with the tags of the NanoAOD-tools recipe (`jetmetHelperRun2.py`):
   * `tagNameUncTotal`: `Summer19UL17_V5_MC_Total_AK4PFchs` /
     `Summer19UL18_V5_MC_Total_AK4PFchs` (JES `jesUncert="Total"`)
   * `tagNamePtResolution`, `tagNameJerScaleFactor`:
     `Summer19UL17_JRV2_MC` / `Summer19UL18_JRV2_MC` `AK4PFchs`

2. **`plotter.py::setJERC`** — Run 2 branch: for MC with a jes/jer variation
   requested, load `MC_jes_unc`, `MC_jer_reso`, `MC_jer_sf` from the `CHS`
   block (no nominal L1/L2 needed — jets are already corrected; no
   SFUncertainty — the CHS `ScaleFactor` correction provides the variations
   through its systematic-string input).

3. **`RDF_JERC.h`** — on-top helpers usable from RDF Defines:

   * `JES_vary_onTop(jerc, Jet_pt, Jet_eta, Jet_mass, dir)`:
     returns pt/mass scaled by `(1 ± delta(eta,pt))` from `MC_jes_unc`.

   * `JER_vary_onTop(...)`: standard "ratio of smear factors" method
     (the nominal smearing cannot be undone). For jets matched to a GenJet
     (`Jet_genJetIdx`, dR<0.2, |pt−genpt|<3σ):

     ```
     c_var = ( 1 + (sf_var − 1) · (pt − genpt)/pt )
           / ( 1 + (sf_nom − 1) · (pt − genpt)/pt )
     ```

     with `sf_nom = sf(eta,"nom")` and `sf_var = sf(eta,"up"/"down")`
     (Run 2 CHS systematic-string API). Unmatched (stochastically smeared)
     jets are left unvaried — deterministic and conservative.

   * `MET_shift_from_jets(...)`: shift MET by the vector sum of the jet-pt
     changes (Type-1-like, jets with pt>15, |eta|<5.2, EM fraction <0.9).

3. **`plotter.py::AddVars`** — for Run 2 MC, when a syst is requested
   (reuse the same `corrections: JERC_syst:` knob):
   * define `Jet_pt_var` (and use it in place of `Jet_pt`),
   * define the shifted raw MET via `MET_shift_from_jets`, and only then
     apply the MET-xy correction, so `MET_pt_corr`/`MET_phi_corr` are built
     from the varied MET.

4. **Config copies** — in `AN-25-092_limitcalc_Run2_jes*.yaml` / `_jer*.yaml`, set
   `JERC_syst` and replace `Jet_pt` → `Jet_pt_var` in the selection strings
   that cut on jet pt (`jet_sel`, `bjetmedium`, `bjettight`,
   `Jet_pt_sel`). Everything cutting on `MET_pt_corr`, `leadingjet_pt`,
   `dphi_MET_jet0` then follows automatically.

   (You cannot `Define` a column named `Jet_pt` — the branch already
   exists — hence the `_var` name and the config-side substitution.)

### Running

Same as Run 3: four variations (`_jesUp/_jesDown/_jerUp/_jerDown`) × signal
samples × {2017, 2018}, then yield comparison per region.

### CHS jets in 2017/2018 (NanoAODv9)

The 2017/2018 custom NanoAOD uses **AK4 CHS** jets from NanoAODv9, while the
NanoAODv15-recomputed JERC files referenced by the default `JecConfigAK4.json`
entries provide **AK4PFPuppi** corrections. Following the standard Run 2
NanoAOD-tools recipe (`jetmetHelperRun2.py`: JEC `Summer19UL17_V5_MC` /
`Summer19UL18_V5_MC`, JER `Summer19UL17_JRV2_MC` / `Summer19UL18_JRV2_MC`,
jet type `AK4PFchs`, `jesUncert="Total"`), the Run 2 systematic variations
instead load the **AK4PFchs** corrections from the official
jsonpog-integration files (`POG/JME/2017_UL(2018_UL)/jet_jerc.json.gz`),
configured in the `CHS` block of each Run 2 year in `JecConfigAK4.json`.
Note the Run 2 CHS JER `ScaleFactor` uses the systematic-string API
(`evaluate({eta, "nom"/"up"/"down"})`) instead of a separate SFUncertainty
correction.

---

## 4. Unclustered MET energy — Run 2 and Run 3

This is the `MET_UnclusterEn` /
`CMS_EXO24033_scale_met_unclustered_energy` nuisance already present in the
`limits/datacard_*.py` writers. It varies the part of MET that is not
clustered into jets; jets themselves are untouched, so only the
MET-dependent quantities (`MET_pt_corr`, `MET_phi_corr`, `dphi_MET_jet0`,
`SDVSecVtx_dphiMET`, region cuts) change.

### Inputs available in the NanoAOD (verified)

* **Run 3 custom NanoAOD, all years** — both Summer22/23 (NanoAODv12) and
  Summer24 (NanoAODv15) files contain the pre-varied Puppi MET branches:
  `PuppiMET_ptUnclusteredUp`, `PuppiMET_ptUnclusteredDown`,
  `PuppiMET_phiUnclusteredUp`, `PuppiMET_phiUnclusteredDown`
  (plus `PuppiMET_pt`, `PuppiMET_phi`).
* **Run 2** — the classic CHS-MET branches
  `MET_MetUnclustEnUpDeltaX`, `MET_MetUnclustEnUpDeltaY`
  (Down variation = minus the same delta).

### Run 3: combine the NanoAOD delta with the on-the-fly MET

The analysis MET in Run 3 is recomputed from `RawPuppiMET` with the
private JECs (`JERC_MET_MC`), while the `PuppiMET_*Unclustered*` branches
are varied versions of the *production* Type-1 PuppiMET. Taking the
**vector difference** between the varied and nominal production MET
isolates the pure unclustered-energy shift — the jet/Type-1 part cancels
exactly — so it can be added to the recomputed `MET_pt_corr`:

```
δx(Up) = PuppiMET_ptUnclusteredUp·cos(PuppiMET_phiUnclusteredUp) − PuppiMET_pt·cos(PuppiMET_phi)
δy(Up) = PuppiMET_ptUnclusteredUp·sin(PuppiMET_phiUnclusteredUp) − PuppiMET_pt·sin(PuppiMET_phi)
```

(and the same with `Down`). Implementation in `plotter.py::AddVars`,
**immediately after** the `AddJERCVars` call and **before** the
`new_variables` loop, reusing the `corrections: JERC_syst:` knob with two
new values `unclust_up` / `unclust_down`:

```python
syst = (self.cfg['corrections'] or {}).get('JERC_syst','nom')
if (not self.isData) and syst in ("unclust_up","unclust_down"):
    ud = "Up" if syst=="unclust_up" else "Down"
    d = d.Define("MET_px_uncl",
        "MET_pt_corr*cos(MET_phi_corr) + PuppiMET_ptUnclustered{0}*cos(PuppiMET_phiUnclustered{0})"
        " - PuppiMET_pt*cos(PuppiMET_phi)".format(ud))
    d = d.Define("MET_py_uncl",
        "MET_pt_corr*sin(MET_phi_corr) + PuppiMET_ptUnclustered{0}*sin(PuppiMET_phiUnclustered{0})"
        " - PuppiMET_pt*sin(PuppiMET_phi)".format(ud))
    d = d.Redefine("MET_pt_corr", "static_cast<float>(std::hypot(MET_px_uncl,MET_py_uncl))")
    d = d.Redefine("MET_phi_corr","static_cast<float>(std::atan2(MET_py_uncl,MET_px_uncl))")
```

Notes:

* `Redefine` (ROOT ≥ 6.26, available in CMSSW_15_0_5) overwrites the
  already-Defined `MET_pt_corr`/`MET_phi_corr`, so every downstream
  variable and cut picks up the variation automatically — no config
  changes to selections needed.
* The `static_cast<float>` is required: `Redefine` must preserve the
  column type (`JERC_MET_ptphi.first/second` are floats).
* Jets are deliberately untouched; `Jet_pt_corr`, `jet_sel`, b-tagging
  etc. stay nominal.
* MC only — for data the branches exist but the variation is not applied.

Then produce the two extra histogram sets with config copies
`AN-25-092_limitcalc_Run3_unclUp.yaml` / `AN-25-092_limitcalc_Run3_unclDown.yaml`
(`JERC_syst: "unclust_up"` / `"unclust_down"`) and postfixes
`_unclUp` / `_unclDown`, exactly as for JES/JER.

### Run 2: same trick with the CHS-MET delta branches

For 2017/2018 the analysis MET is the stored CHS `MET_pt` plus the xy
correction. Apply the same `Redefine` hook (after the `metxy` Define
block in `AddVars`), using the stored delta:

```python
sign = "+" if syst=="unclust_up" else "-"
d = d.Define("MET_px_uncl","MET_pt_corr*cos(MET_phi_corr) {0} MET_MetUnclustEnUpDeltaX".format(sign))
d = d.Define("MET_py_uncl","MET_pt_corr*sin(MET_phi_corr) {0} MET_MetUnclustEnUpDeltaY".format(sign))
# Redefine MET_pt_corr / MET_phi_corr as above
```

The xy correction is an additive npv-dependent shift, independent of the
MET value itself, so applying the unclustered delta before or after it is
equivalent.

### Sanity checks specific to this variation

* Nominal closure: `JERC_syst: "nom"` must reproduce the nominal yields
  bit-for-bit.
* The event-by-event shift |δ| is typically a few GeV up to a few tens of
  GeV; the yield effect in a MET>350 selection is usually at the level of
  a few % or less. Compare `MET_pt_corr` in the `<region>_evt` folders.
* Up and down shifts should move the yields in opposite directions
  (approximately symmetrically).

---

## 5. Extracting the numbers

For each systematic S, region R, sample and year:

1. `N_nom(R)`, `N_S_up(R)`, `N_S_down(R)` from the histogram integrals
   (or `sum(evt_weight)` from the pkl files).
2. Relative uncertainties
   `δ_up = N_up/N_nom − 1`, `δ_down = N_down/N_nom − 1`.
3. For the limit datacards: enter as asymmetric `lnN`
   (`1+δ_down / 1+δ_up`) per region, or symmetrize
   `δ = (|δ_up|+|δ_down|)/2` if up/down are compatible.
4. Correlation scheme: PU and JES(Total)/JER(Total) each one nuisance,
   correlated across regions within a year; JER is usually treated as
   uncorrelated between years (the `_<year>` suffix in
   `CMS_res_j_<year>`), the regrouped JES sources carry their correlation
   in the names (`CMS_scale_j_Absolute` correlated vs
   `CMS_scale_j_Absolute_<year>` uncorrelated).

## 6. Sanity checks

* **Nominal closure:** run the modified code with `JERC_syst: "nom"` and
  confirm bit-identical yields with the unmodified nominal — this validates
  the plumbing.
* **Direction:** JES-up must increase `leadingjet_pt` and (for
  signal-like topologies) `MET_pt_corr`; check the `<region>_evt`
  `MET_pt_corr` and `leadingjet_pt` histograms migrate the expected way.
* **Size:** total-JES effects on the yields of a MET>350 selection are
  typically a few %; PU typically ≲ 1–3%. Order-of-magnitude surprises
  usually mean the variation was applied after a cut, or MET was not
  propagated.
* **Statistics:** up/down and nominal run over the same events, so
  statistical fluctuations largely cancel; still, for small signal samples
  check the MC stat error on N_nom before quoting sub-% systematics.
