import os
import yaml
import json
import numpy as np
import pickle
import ROOT
import correctionlib
correctionlib.register_pyroot_binding()
import SoftDisplacedVertices.Samples.Samples as s
ROOT.gInterpreter.Declare('#include "{}/src/SoftDisplacedVertices/Plotter/RDFHelper.h"'.format(os.environ['CMSSW_BASE']))
ROOT.gInterpreter.Declare('#include "{}/src/SoftDisplacedVertices/Plotter/METxyCorrection.h"'.format(os.environ['CMSSW_BASE']))
ROOT.gInterpreter.Declare('#include "{}/src/SoftDisplacedVertices/Plotter/RDF_JERC.h"'.format(os.environ['CMSSW_BASE']))
#ROOT.EnableImplicitMT(4)
# Maybe let ROOT decide the number of threads to use
# FIXME: getting numpy arrays with MT results in unmatched columns in arrays
ROOT.EnableImplicitMT()
ROOT.gROOT.SetBatch(ROOT.kTRUE)
ROOT.TH1.SetDefaultSumw2(True)
ROOT.gStyle.SetOptStat(0)

# Per-object weight lookup for custom reweighting: for each element of x, return the
# content of the weight histogram bin it falls in (under/overflow clamped to the edge
# bins). FindFixBin is FindBin without the axis-extension side effect (const-safe).
ROOT.gInterpreter.Declare('''
#ifndef CUSTOM_WEIGHT_LOOKUP
#define CUSTOM_WEIGHT_LOOKUP
template <typename T>
ROOT::VecOps::RVec<double> CustomWeightLookup(const TH1* h, const ROOT::VecOps::RVec<T>& x) {
  ROOT::VecOps::RVec<double> w(x.size());
  for (size_t i = 0; i < x.size(); ++i) {
    int b = h->GetXaxis()->FindFixBin(x[i]);
    if (b < 1) b = 1;
    if (b > h->GetNbinsX()) b = h->GetNbinsX();
    w[i] = h->GetBinContent(b);
  }
  return w;
}
#endif
''')

class Plotter:
    def __init__(self,s=None,datalabel="",outputDir="./",lumi=1,info_path="",input_json="",input_filelist=None,config="",year="",isData=False,postfix=""):
        self.s = None
        self.datalabel = datalabel
        self.outputDir = outputDir
        self.lumi = lumi
        self.info_path = info_path
        self.input_json = input_json
        self.input_filelist = input_filelist
        self.year = year
        self.isData = isData
        self.postfix = postfix
        with open(config, "r") as f_cfg:
            cfg = yaml.load(f_cfg, Loader=yaml.FullLoader)
        self.cfg = cfg
        # JERC systematic variation knob (config: corrections -> JERC_syst)
        self.jerc_syst = 'nom'
        if ('corrections' in cfg) and (cfg['corrections'] is not None) and ('JERC_syst' in cfg['corrections']) and cfg['corrections']['JERC_syst']:
            self.jerc_syst = cfg['corrections']['JERC_syst']
        # jer_nom (Run 2 only): recompute JEC+JER with the nominal SF -- the smeared
        # reference against which jer_up/jer_down are compared (the stored Run 2 jets
        # are unsmeared, so the stored-jet nominal is not a valid JER baseline)
        valid_systs = ['nom','jes_up','jes_down','jer_up','jer_down','jer_nom','unclust_up','unclust_down']
        assert self.jerc_syst in valid_systs, "JERC_syst {} not valid! Choose from {}".format(self.jerc_syst,valid_systs)
        if self.jerc_syst != 'nom':
            assert not self.isData, "JERC_syst variations are MC-only, do not use them on data!"
            if ('2022' in str(self.year)) or ('2023' in str(self.year)) or ('2024' in str(self.year)):
                assert cfg['corrections'].get('JERC'), "JERC_syst for Run3 requires corrections: JERC: True!"
                assert self.jerc_syst != 'jer_nom', "jer_nom is Run2-only (the Run3 nominal already includes JER smearing)!"
        self.setJERC()
        if not self.isData:
            self.setCorrections()
            if ('new_variables_mc' in self.cfg) and (self.cfg['new_variables_mc'] is not None):
                if ('new_variables' in self.cfg):
                    for v in self.cfg['new_variables_mc']:
                        self.cfg['new_variables'][v] = self.cfg['new_variables_mc'][v]
                else:
                    self.cfg['new_variables'] = self.cfg['new_variables_mc']
            if ('event_variables_mc' in self.cfg) and (self.cfg['event_variables_mc'] is not None):
                if ('event_variables' in self.cfg):
                    self.cfg['event_variables'] += self.cfg['event_variables_mc']
                else:
                    self.cfg['event_variables'] = self.cfg['event_variables_mc']
            if ('objects' in self.cfg) and (self.cfg['objects'] is not None):
                for o in self.cfg['objects']:
                    if ('variables_mc' in self.cfg['objects'][o]) and (self.cfg['objects'][o]['variables_mc'] is not None):
                        if ('variables' in self.cfg['objects'][o]):
                            self.cfg['objects'][o]['variables'] += self.cfg['objects'][o]['variables_mc']
                        else:
                            self.cfg['objects'][o]['variables'] = self.cfg['objects'][o]['variables_mc']
        else:
            if ('new_variables_data' in self.cfg) and (self.cfg['new_variables_data'] is not None):
                if ('new_variables' in self.cfg):
                    for v in self.cfg['new_variables_data']:
                        self.cfg['new_variables'][v] = self.cfg['new_variables_data'][v]
                else:
                    self.cfg['new_variables'] = self.cfg['new_variables_data']
            if ('event_variables_data' in self.cfg) and (self.cfg['event_variables_data'] is not None):
                if ('event_variables' in self.cfg):
                    self.cfg['event_variables'] += self.cfg['event_variables_data']
                else:
                    self.cfg['event_variables'] = self.cfg['event_variables_data']
            if ('objects' in self.cfg) and (self.cfg['objects'] is not None):
                for o in self.cfg['objects']:
                    if ('variables_data' in self.cfg['objects'][o]) and (self.cfg['objects'][o]['variables_data'] is not None):
                        if ('variables' in self.cfg['objects'][o]):
                            self.cfg['objects'][o]['variables'] += self.cfg['objects'][o]['variables_data']
                        else:
                            self.cfg['objects'][o]['variables'] = self.cfg['objects'][o]['variables_data']

        if ('mapveto' in self.cfg):
            mappath = ''
            if self.isData:
                assert 'data_path' in self.cfg['mapveto'], "data_path not available in config!"
                mappath = self.cfg['mapveto']['data_path']
                if type(mappath)==dict:
                    assert self.year in mappath, "Material map (data) of year {} not available in config!".format(self.year)
                    mappath = self.cfg['mapveto']['data_path'][self.year]
            else:
                assert 'mc_path' in self.cfg['mapveto'], "mc_path not available in config!"
                mappath = self.cfg['mapveto']['mc_path']
                if type(mappath)==dict:
                    assert self.year in mappath, "Material map (MC) of year {} not available in config!".format(self.year)
                    mappath = self.cfg['mapveto']['mc_path'][self.year]
            self.f1 = ROOT.TFile.Open(mappath)
            ROOT.gInterpreter.ProcessLine("auto h_mm = material_map; h_mm->SetDirectory(0);")
            self.f1.Close()

        if self.cfg['corrections'] is not None:
            if 'jetid' in self.cfg['corrections'] and self.cfg['corrections']['jetid'] is not None:
                if str(self.year)=="2024":
                    assert str(self.year) in self.cfg['corrections']['jetid'], "Year {} not defined in jetid!".format(self.year)
                    ROOT.gInterpreter.ProcessLine('auto jetidf = correction::CorrectionSet::from_file("{}");'.format(self.cfg['corrections']['jetid'][str(self.year)]['path']))
                    ROOT.gInterpreter.ProcessLine('auto jetideva = jetidf->at("{}");'.format(self.cfg['corrections']['jetid'][str(self.year)]['name']))
            if 'jetmapveto' in self.cfg['corrections'] and self.cfg['corrections']['jetmapveto'] is not None:
                assert str(self.year) in self.cfg['corrections']['jetmapveto'], "Year {} not defined in jetmapveto!".format(self.year)
                ROOT.gInterpreter.ProcessLine('auto jetmepvetof = correction::CorrectionSet::from_file("{}");'.format(self.cfg['corrections']['jetmapveto'][str(self.year)]['path']))
                ROOT.gInterpreter.ProcessLine('auto jetmapvetoeva = jetmepvetof->at("{}");'.format(self.cfg['corrections']['jetmapveto'][str(self.year)]['name']))

        self.setCustomWeights()

    def _perYear(self, value):
        '''Resolve a config value that may be year-dependent. If value is a dict it is
        treated as a {year: value} map and the entry for self.year is returned (asserting
        it exists); otherwise value is returned unchanged (same for every year).'''
        if isinstance(value, dict):
            assert self.year in value, "Year {} not configured (have {})!".format(self.year, list(value.keys()))
            return value[self.year]
        return value

    def setCustomWeights(self):
        '''Load custom per-object weight histograms for reweighting object-level plots.

        Config (per object, weights derived e.g. with deriveWeights.py):
          objects:
            SDVSecVtx:
              custom_weights:
                - file: /path/to/weights.root
                  hist: w_SDVSecVtx_Lxy         # name in the file (optional if unique)
                  var: SDVSecVtx_Lxy            # column/expression the weight is looked up on
        Each of file/hist/var may instead be a {year: value} map to apply different
        weights per year, e.g.
                - file:
                    2022Pre: /path/to/weights_2022Pre.root
                    2022Post: /path/to/weights_2022Post.root
                  var: SDVSecVtx_Lxy
        the entry matching self.year is used. Multiple entries per object are multiplied.
        The lookup variable must be the full-length (unselected) per-object column; the
        object selections are applied to the weight column automatically. MC only: data
        histograms stay unweighted, as everywhere else. Note: custom weights are not
        applied to N-1 plots (their per-variable masks differ from the object selection).
        '''
        self.custom_weights = {}
        if self.isData or not self.cfg.get('objects'):
            return
        for obj in self.cfg['objects']:
            weight_cfgs = self.cfg['objects'][obj].get('custom_weights')
            if not weight_cfgs:
                continue
            resolved_cfgs = []
            for i, wcfg in enumerate(weight_cfgs):
                path = self._perYear(wcfg['file'])
                assert os.path.exists(path), "Custom weight file {} does not exist!".format(path)
                fw = ROOT.TFile.Open(path)
                histname = self._perYear(wcfg.get('hist'))
                if histname is None:
                    keys = [k.GetName() for k in fw.GetListOfKeys()]
                    assert len(keys)==1, "'hist' not specified and {} has multiple objects: {}".format(path, keys)
                    histname = keys[0]
                assert fw.Get(histname), "Histogram {} not found in {}!".format(histname, path)
                hname = 'h_customweight_{}_{}'.format(obj, i)
                ROOT.gInterpreter.ProcessLine('auto {n} = (TH1*)gDirectory->Get("{h}"); {n}->SetDirectory(0);'.format(n=hname, h=histname))
                fw.Close()
                resolved_cfgs.append({'file': path, 'hist': histname, 'var': self._perYear(wcfg['var'])})
            self.custom_weights[obj] = resolved_cfgs

    def AddCustomWeights(self, d):
        '''Define the per-object custom weight column <obj>_customweight (full length,
        aligned with the unselected object columns).'''
        for obj, weight_cfgs in self.custom_weights.items():
            terms = []
            for i, wcfg in enumerate(weight_cfgs):
                wcol = '{}_customweight_{}'.format(obj, i)
                d = d.Define(wcol, 'CustomWeightLookup(h_customweight_{}_{}, {})'.format(obj, i, wcfg['var']))
                terms.append(wcol)
            d = d.Define('{}_customweight'.format(obj), ' * '.join(terms))
        return d

    def AddObjectPlotWeights(self, d):
        '''Combine the event weight with the selection-masked custom object weights into
        the per-object histogram weight <obj>_plotweight<sel>. MC only: data histograms
        stay unweighted, as everywhere else.'''
        if self.isData:
            return d
        for obj in self.custom_weights:
            for sel in self.cfg['objects'][obj]['selections']:
                d = d.Define('{}_plotweight{}'.format(obj, sel), 'evt_weight * {}_customweight{}'.format(obj, sel))
        return d

    def setJERC(self):
        # read the config file that includes the path and tag names of the corrections
        jerc_config = "{}/src/SoftDisplacedVertices/Plotter/data/JecConfigAK4.json".format(os.environ['CMSSW_BASE'])
        assert os.path.exists(jerc_config), "JERC config {} does not exist!".format(jerc_config)
        with open(jerc_config,'r') as jercf:
            jercconf = json.load(jercf)

        # set up the evaluators
        jesmode = "JesNominal" # this is the nominal jes without syst
        #jestagname = "tagNameL1L2L3Res" # this is the tag name of the jes
        jestagname = {
                "L1": "tagNameL1FastJet",
                "L2": "tagNameL2Relative",
                "L2L3": "tagNameL2L3Residual", # this is for data only
                }
        jermode = "JerNominal" # this is the nominal jer without syst
        jerresotagname = "tagNamePtResolution"
        jersftagname = "tagNameJerScaleFactor"
        # path of the smear factor calculation
        jersmear_jsonpath = "{}/src/SoftDisplacedVertices/Plotter/data/jer_smear.json.gz".format(os.environ["CMSSW_BASE"])
        if self.year in ["2022Pre","2022Post","2023Pre","2023Post","2024"]:
            assert self.year in jercconf, "Year {} not available in JERC!".format(self.year)
            assert "jercJsonPath" in jercconf[self.year], "jercJsonPath does not exist in JERC for {}!".format(self.year)
            jsonpath = jercconf[self.year]["jercJsonPath"]
            jercloadcmd = 'auto jercf = correction::CorrectionSet::from_file("{}");'.format(jsonpath)
            jercloadcmd += 'std::map<std::string,correction::Correction::Ref> jerc_refs;'
            if self.isData:
                for era in jercconf[self.year]['ApplyOnData'][jesmode]:
                    for itag in jestagname:
                        tagname = jercconf[self.year]['ApplyOnData'][jesmode][era][jestagname[itag]]
                        jercloadcmd += 'jerc_refs.insert({{"data_jes_{}_{}",jercf->at("{}")}});'.format(itag,era,tagname)

            else:
                for itag in jestagname:
                    if itag=="L2L3":
                        continue
                    tagname = jercconf[self.year]['ApplyOnMC'][jesmode][jestagname[itag]]
                    jercloadcmd += 'jerc_refs.insert({{"MC_jes_{}",jercf->at("{}")}});'.format(itag,tagname)
                jercloadcmd += 'jerc_refs.insert({{"MC_jer_reso",jercf->at("{}")}});'.format(jercconf[self.year]['ApplyOnMC'][jermode][jerresotagname])
                jercloadcmd += 'jerc_refs.insert({{"MC_jer_sf",jercf->at("{}")}});'.format(jercconf[self.year]['ApplyOnMC'][jermode][jersftagname])
                jercloadcmd += 'auto jersmearf = correction::CorrectionSet::from_file("{}");'.format(jersmear_jsonpath)
                jercloadcmd += 'jerc_refs.insert({{"MC_jer_smear",jersmearf->at("{}")}});'.format("JERSmear")
                # uncertainty evaluators for the systematic variations
                jercloadcmd += 'jerc_refs.insert({{"MC_jes_unc",jercf->at("{}")}});'.format(jercconf[self.year]['ApplyOnMC']['JesUncertaintySet']['JesUncertaintySetTotal']['CMS_scale_j_Total'])
                jercloadcmd += 'jerc_refs.insert({{"MC_jer_sf_unc",jercf->at("{}")}});'.format(jercconf[self.year]['ApplyOnMC'][jermode]['tagNameJerSFUncertainty'])

            ROOT.gInterpreter.ProcessLine(jercloadcmd)
        elif self.year in ["2016Pre","2016Post","2017","2018"]:
            # Run 2: jets in the NanoAOD (v9) are AK4 CHS with the up-to-date JEC
            # applied but NO JER smearing (verified: L1L2L3 on the raw pt reproduces
            # the stored pt to ~0.1%). The systematic variations therefore recompute
            # the jets from raw (JERC_jet_MC_run2), which needs the full L1/L2/L3
            # chain plus the JER inputs. The NanoAODv15-recomputed JERC entries above
            # are AK4PFPuppi only; following the Run 2 NanoAOD-tools recipe
            # (jetmetHelperRun2: Summer19UL1x_V5_MC / Summer19UL1x_JRV2_MC, AK4PFchs,
            # jesUncert="Total"), the AK4PFchs corrections are loaded from the
            # jsonpog-integration files configured in the "CHS" block. Note: the CHS
            # JER ScaleFactor uses the systematic-string API (eta, "nom"/"up"/"down"),
            # there is no separate SFUncertainty correction.
            if (not self.isData) and (self.jerc_syst in ["jes_up","jes_down","jer_up","jer_down","jer_nom"]):
                assert self.year in jercconf, "Year {} not available in JERC!".format(self.year)
                assert 'CHS' in jercconf[self.year], "CHS JERC block not configured for {}!".format(self.year)
                chsconf = jercconf[self.year]['CHS']
                jercloadcmd = 'auto jercf = correction::CorrectionSet::from_file("{}");'.format(chsconf["jercJsonPath"])
                jercloadcmd += 'std::map<std::string,correction::Correction::Ref> jerc_refs;'
                jercloadcmd += 'jerc_refs.insert({{"MC_jes_L1",jercf->at("{}")}});'.format(chsconf['tagNameL1FastJet'])
                jercloadcmd += 'jerc_refs.insert({{"MC_jes_L2",jercf->at("{}")}});'.format(chsconf['tagNameL2Relative'])
                jercloadcmd += 'jerc_refs.insert({{"MC_jes_L3",jercf->at("{}")}});'.format(chsconf['tagNameL3Absolute'])
                jercloadcmd += 'jerc_refs.insert({{"MC_jes_unc",jercf->at("{}")}});'.format(chsconf['tagNameUncTotal'])
                jercloadcmd += 'jerc_refs.insert({{"MC_jer_reso",jercf->at("{}")}});'.format(chsconf['tagNamePtResolution'])
                jercloadcmd += 'jerc_refs.insert({{"MC_jer_sf",jercf->at("{}")}});'.format(chsconf['tagNameJerScaleFactor'])
                jercloadcmd += 'auto jersmearf = correction::CorrectionSet::from_file("{}");'.format(jersmear_jsonpath)
                jercloadcmd += 'jerc_refs.insert({{"MC_jer_smear",jersmearf->at("JERSmear")}});'
                ROOT.gInterpreter.ProcessLine(jercloadcmd)

    def setCorrections(self):
      if 'corrections' in self.cfg and self.cfg['corrections'] is not None:
        if 'PU' in self.cfg['corrections'] and self.cfg['corrections']['PU'] is not None:
          assert str(self.year) in self.cfg['corrections']['PU'], "Year {} not defined in PU correction!".format(self.year)
          ROOT.gInterpreter.ProcessLine('auto puf = correction::CorrectionSet::from_file("{}");'.format(self.cfg['corrections']['PU'][str(self.year)]['path']))
          ROOT.gInterpreter.ProcessLine('auto pu = puf->at("{}");'.format(self.cfg['corrections']['PU'][str(self.year)]['name']))
        if 'electron' in self.cfg['corrections'] and self.cfg['corrections']['electron'] is not None:
          assert str(self.year) in self.cfg['corrections']['electron'], "Year {} not defined in electron correction!".format(self.year)
          ROOT.gInterpreter.ProcessLine('auto elec = correction::CorrectionSet::from_file("{}");'.format(self.cfg['corrections']['electron'][str(self.year)]['path']))
          ROOT.gInterpreter.ProcessLine('auto elesf = elec->at("{}");'.format(self.cfg['corrections']['electron'][str(self.year)]['name']))
        if 'photon' in self.cfg['corrections'] and self.cfg['corrections']['photon'] is not None:
          ROOT.gInterpreter.ProcessLine('auto phoc = correction::CorrectionSet::from_file("{}");'.format(self.cfg['corrections']['photon'][str(self.year)]['path']))
          ROOT.gInterpreter.ProcessLine('auto phosf = phoc->at("{}");'.format(self.cfg['corrections']['photon'][str(self.year)]['name']))
        if 'muon' in self.cfg['corrections'] and self.cfg['corrections']['muon'] is not None:
          ROOT.gInterpreter.ProcessLine('auto muc = correction::CorrectionSet::from_file("{}");'.format(self.cfg['corrections']['muon'][str(self.year)]['path']))
          ROOT.gInterpreter.ProcessLine('auto musf = muc->at("{}");'.format(self.cfg['corrections']['muon'][str(self.year)]['name']))

    def applyCorrections(self,d):
      self.weightstr = ''
      if self.isData:
        d = d.Define("puweight","1")
        if ('weights' in self.cfg) and (self.cfg['weights'] is not None):
          for w in self.cfg['weights']:
            self.weightstr += ' * {}'.format(w)
      else:
        if self.cfg['corrections'] is not None:
          if 'PU' in self.cfg['corrections'] and  self.cfg['corrections']['PU'] is not None:
            d = d.Define("puweight",('pu->evaluate({{Pileup_nTrueInt,"{0}"}})'.format(self.cfg['corrections']['PU'][str(self.year)]['mode'])))
            self.weightstr += ' * puweight'
          if 'electron' in self.cfg['corrections'] and  self.cfg['corrections']['electron'] is not None:
            d = d.Define("eleweight",'EGamma_weight(elesf,Electron_pt[{0}],Electron_eta[{0}],"{1}","Veto","{2}","electron")'.format(self.cfg['ele_sel'],self.cfg['corrections']['electron']['mode'],str(self.year)))
            self.weightstr += ' * eleweight'
          if 'photon' in self.cfg['corrections'] and  self.cfg['corrections']['photon'] is not None:
            d = d.Define("phoweight",'EGamma_weight(phosf,Photon_pt[{0}],Photon_eta[{0}],"{1}","Loose","{2}","photon")'.format(self.cfg['photon_sel'],self.cfg['corrections']['photon']['mode'],str(self.year)))
            self.weightstr += ' * phoweight'
          if 'muon' in self.cfg['corrections'] and  self.cfg['corrections']['muon'] is not None:
            d = d.Define("muweight",'Muon_weight(musf,Muon_pt[{0}],Muon_eta[{0}],"{1}")'.format(self.cfg['muon_sel'],self.cfg['corrections']['muon']['mode'],str(self.year)))
            self.weightstr += ' * muweight'
          if 'met' in self.cfg['corrections'] and  self.cfg['corrections']['met'] is not None:
            d = d.Define("metweight",'METweight(MET_pt_corr, "{}", "{}")'.format(str(self.year),self.cfg['corrections']['met']['mode']))
            self.weightstr += ' * metweight'
          if 'vtx' in self.cfg['corrections'] and  self.cfg['corrections']['vtx'] is not None:
            d = d.Define("vtxweight",'SDVSecVtx_evtweight(LeadingVtx_Lxy, "{}", "{}")'.format(str(self.year),self.cfg['corrections']['vtx']['mode']))
            self.weightstr += ' * vtxweight'
        if ('weights' in self.cfg) and (self.cfg['weights'] is not None):
          for w in self.cfg['weights']:
            self.weightstr += ' * {}'.format(w)
        if ('mcweights' in self.cfg) and (self.cfg['mcweights'] is not None):
          for w in self.cfg['mcweights']:
            self.weightstr += ' * {}'.format(w)

      return d

    def setLumi(self,lumi):
      self.lumi = lumi

    def setSample(self,s):
      self.s = s

    def valid(self):
      if self.s is None:
        return False
      return True

    def setSampleInfo(self,info_path):
      self.info_path = info_path

    def setJson(self,input_json):
      self.input_json = input_json

    def getFileList(self):
      self.filelist = []
      # First try to get the input file list from the txt file
      if (self.input_filelist is not None) and (os.path.exists( self.input_filelist )) and (os.path.isfile( self.input_filelist )):
        with open( self.input_filelist, 'r') as inputfile:
            for line in inputfile.readlines():
                line = line.rstrip('\n').rstrip()
                if line.endswith('.root'):
                    self.filelist.append(line)
      elif (self.s is not None) and (self.input_filelist is None):
        self.filelist = self.s.getFileList(self.datalabel,"")
      if len(self.filelist)==0:
        print("No files provided as input!")


    def getSumWeight(self):
      if self.s is None:
        print("Sample not provided, cannot get SumWeight.")
        return -1
      nevt = self.s.getNEvents(self.datalabel)
      if nevt != -1:
        return nevt
      print(self.info_path)
      with open(self.info_path,'r') as f_sample_info:
        sample_info = yaml.safe_load(f_sample_info)
      for i in sample_info:
        if not self.s.name in i:
          continue
        return sample_info[i]['totalsumWeights']
      print("No sum weight record found for {}!".format(self.s.name))
      return -1

    def ApplyNoiseFilters(self,d):
        if ('2022' in self.year) or ('2023' in self.year):
            d = d.Filter("Flag_goodVertices && Flag_globalSuperTightHalo2016Filter && Flag_EcalDeadCellTriggerPrimitiveFilter && Flag_BadPFMuonFilter && Flag_BadPFMuonDzFilter && Flag_hfNoisyHitsFilter && Flag_eeBadScFilter")
        elif ('2024' in self.year):
            d = d.Filter("Flag_goodVertices && Flag_globalSuperTightHalo2016Filter && Flag_EcalDeadCellTriggerPrimitiveFilter && Flag_BadPFMuonFilter && Flag_BadPFMuonDzFilter && Flag_hfNoisyHitsFilter && Flag_eeBadScFilter && Flag_ecalBadCalibFilter")
        elif ('2017' in self.year) or ('2018' in self.year):
            d = d.Filter("Flag_goodVertices && Flag_globalSuperTightHalo2016Filter && Flag_HBHENoiseFilter && Flag_HBHENoiseIsoFilter && Flag_EcalDeadCellTriggerPrimitiveFilter && Flag_BadPFMuonFilter && Flag_BadPFMuonDzFilter && Flag_hfNoisyHitsFilter && Flag_eeBadScFilter && Flag_ecalBadCalibFilter")
        else:
            raise Exception("No noise filters implemented for year {}!".format(self.year))
        return d
    
    def AddJERCVars(self,d):
        if not (('2022' in self.year) or ('2023' in self.year) or ('2024' in self.year)):
            raise Exception("Recalculating JERC variables not implemented for year {}!".format(self.year))
        d = d.Define('CorrT1METJet_rawFactor','ROOT::VecOps::RVec<float>(CorrT1METJet_area.size(),0)')
        d = d.Define('CorrT1METJet_chEmEF','ROOT::VecOps::RVec<float>(CorrT1METJet_area.size(),0)')
        d = d.Define('CorrT1METJet_neEmEF','ROOT::VecOps::RVec<float>(CorrT1METJet_area.size(),0)')
        d = d.Define('METJet_area','ROOT::VecOps::Concatenate(Jet_area,CorrT1METJet_area)')
        d = d.Define('METJet_eta','ROOT::VecOps::Concatenate(Jet_eta,CorrT1METJet_eta)')
        d = d.Define('METJet_phi','ROOT::VecOps::Concatenate(Jet_phi,CorrT1METJet_phi)')
        d = d.Define('METJet_pt','ROOT::VecOps::Concatenate(Jet_pt,CorrT1METJet_rawPt)')
        d = d.Define('METJet_rawFactor','ROOT::VecOps::Concatenate(Jet_rawFactor,CorrT1METJet_rawFactor)')
        d = d.Define('METJet_muonSubtrFactor','ROOT::VecOps::Concatenate(Jet_muonSubtrFactor, CorrT1METJet_muonSubtrFactor)')
        d = d.Define('METJet_chEmEF','ROOT::VecOps::Concatenate(Jet_chEmEF,CorrT1METJet_chEmEF)')
        d = d.Define('METJet_neEmEF','ROOT::VecOps::Concatenate(Jet_neEmEF,CorrT1METJet_neEmEF)')
        if self.isData:
            d = d.Define('JERC_jet_ptmass','JERC_jet_data(jerc_refs, year, run, event, Jet_area, Jet_eta, Jet_phi, Jet_pt, Jet_mass, Jet_rawFactor, Rho_fixedGridRhoFastjetAll)')
            d = d.Define('JERC_MET_ptphi','JERC_MET_data(jerc_refs, year, run, event, RawPuppiMET_pt, RawPuppiMET_phi, METJet_area, METJet_eta, METJet_phi, METJet_pt, METJet_rawFactor, METJet_muonSubtrFactor, METJet_chEmEF, METJet_neEmEF, Rho_fixedGridRhoFastjetAll)')
        else:
            # jes/jer variations are handled inside the JERC functions; unclust is applied afterwards
            jerc_syst_cpp = self.jerc_syst if self.jerc_syst in ('jes_up','jes_down','jer_up','jer_down') else 'nom'
            d = d.Define('CorrT1METJet_genJetIdx','genJetIdx_CorrT1METJet(CorrT1METJet_eta, CorrT1METJet_phi, GenJet_eta, GenJet_phi)')
            d = d.Define('METJet_genJetIdx','ROOT::VecOps::Concatenate(Jet_genJetIdx,CorrT1METJet_genJetIdx)')
            d = d.Define('JERC_jet_ptmass','JERC_jet_MC(jerc_refs, year, run, event, Jet_area, Jet_eta, Jet_phi, Jet_pt, Jet_mass, Jet_rawFactor, Rho_fixedGridRhoFastjetAll, Jet_genJetIdx, GenJet_pt, GenJet_eta, GenJet_phi, "{}")'.format(jerc_syst_cpp))
            d = d.Define('JERC_MET_ptphi','JERC_MET_MC(jerc_refs, year, run, event, RawPuppiMET_pt, RawPuppiMET_phi, METJet_area, METJet_eta, METJet_phi, METJet_pt, METJet_rawFactor, METJet_muonSubtrFactor, METJet_chEmEF, METJet_neEmEF, Rho_fixedGridRhoFastjetAll, METJet_genJetIdx, GenJet_pt, GenJet_eta, GenJet_phi, "{}")'.format(jerc_syst_cpp))

        d = d.Define('Jet_pt_corr','JERC_jet_ptmass.first')
        d = d.Define('Jet_mass_corr','JERC_jet_ptmass.second')
        d = d.Define('MET_pt_corr','JERC_MET_ptphi.first')
        d = d.Define('MET_phi_corr','JERC_MET_ptphi.second')

        return d

    def ApplyJERCSystRun3(self,d):
        '''Run 3 systematic variations that are not handled inside the JERC recompute:
        - unclust_up/down: shift the recomputed MET by the unclustered-energy delta taken
          from the NanoAOD PuppiMET_*Unclustered* branches (the production Type-1 part
          cancels in the difference). Jets are untouched.
        jes_up/down and jer_up/down are fully handled inside JERC_jet_MC / JERC_MET_MC:
        all jet selections in the configs must cut on the recomputed Jet_pt_corr (never
        on the stored Jet_pt), so the variations propagate through Jet_pt_corr and
        MET_pt_corr alone.'''
        if self.isData or self.jerc_syst=='nom':
            return d
        if self.jerc_syst in ('unclust_up','unclust_down'):
            ud = 'Up' if self.jerc_syst=='unclust_up' else 'Down'
            d = d.Define('MET_px_uncl','MET_pt_corr*cos(MET_phi_corr) + PuppiMET_ptUnclustered{0}*cos(PuppiMET_phiUnclustered{0}) - PuppiMET_pt*cos(PuppiMET_phi)'.format(ud))
            d = d.Define('MET_py_uncl','MET_pt_corr*sin(MET_phi_corr) + PuppiMET_ptUnclustered{0}*sin(PuppiMET_phiUnclustered{0}) - PuppiMET_pt*sin(PuppiMET_phi)'.format(ud))
            d = d.Redefine('MET_pt_corr','static_cast<float>(std::hypot(MET_px_uncl,MET_py_uncl))')
            d = d.Redefine('MET_phi_corr','static_cast<float>(std::atan2(MET_py_uncl,MET_px_uncl))')
        return d

    def ApplyJERCSystRun2(self,d):
        '''Run 2 systematic variations, applied before the MET xy correction. The stored
        Jet_pt/Jet_mass carry the up-to-date JEC but no JER smearing, so:
        - jes_up/down / jer_up/down / jer_nom: recompute the jets from raw pt/mass
          (JERC_jet_MC_run2: rawFactor -> L1L2L3 -> optional JES shift -> JER smearing
          with the nominal/varied SF) and propagate the pt change to MET (Type-1-like,
          relative to the stored, JEC-only Jet_pt). jer_nom is the smeared reference
          for the jer_up/jer_down comparison.
        - unclust_up/down: shift MET by the stored unclustered-energy delta
          (MET_MetUnclustEnUpDeltaX/Y); Down = minus the same delta.'''
        if self.isData or self.jerc_syst=='nom':
            return d
        if self.jerc_syst in ('jes_up','jes_down','jer_up','jer_down','jer_nom'):
            syst_cpp = 'nom' if self.jerc_syst=='jer_nom' else self.jerc_syst
            d = d.Define('Jet_ptmass_var','JERC_jet_MC_run2(jerc_refs, event, Jet_area, Jet_eta, Jet_phi, Jet_pt, Jet_mass, Jet_rawFactor, fixedGridRhoFastjetAll, Jet_genJetIdx, GenJet_pt, GenJet_eta, GenJet_phi, "{}")'.format(syst_cpp))
            d = d.Define('MET_ptphi_var','MET_shift_from_jets(MET_pt, MET_phi, Jet_pt, Jet_ptmass_var.first, Jet_eta, Jet_phi, Jet_chEmEF, Jet_neEmEF)')
            d = d.Redefine('Jet_pt','Jet_ptmass_var.first')
            d = d.Redefine('Jet_mass','Jet_ptmass_var.second')
            d = d.Redefine('MET_pt','MET_ptphi_var.first')
            d = d.Redefine('MET_phi','MET_ptphi_var.second')
        elif self.jerc_syst in ('unclust_up','unclust_down'):
            sign = '+' if self.jerc_syst=='unclust_up' else '-'
            d = d.Define('MET_px_uncl','MET_pt*cos(MET_phi) {} MET_MetUnclustEnUpDeltaX'.format(sign))
            d = d.Define('MET_py_uncl','MET_pt*sin(MET_phi) {} MET_MetUnclustEnUpDeltaY'.format(sign))
            d = d.Redefine('MET_pt','static_cast<float>(std::hypot(MET_px_uncl,MET_py_uncl))')
            d = d.Redefine('MET_phi','static_cast<float>(std::atan2(MET_py_uncl,MET_px_uncl))')
        return d

    def AddJetID(self,d):
        if not (('2022' in self.year) or ('2023' in self.year) or ('2024' in self.year)):
            raise Exception("Recalculating JetID not implemented for year {}!".format(self.year))
        if "2024" in self.year:
            d = d.Define("Jet_jetId_TightLepVeto","GetJetID(jetideva,Jet_eta,Jet_chHEF,Jet_neHEF,Jet_chEmEF,Jet_neEmEF,Jet_muEF,Jet_chMultiplicity,Jet_neMultiplicity)")
        elif ("2022" in self.year) or ("2023" in self.year):
            d = d.Define("Jet_jetId_TightLepVeto","GetJetID(Jet_jetId,Jet_eta,Jet_neHEF,Jet_chEmEF,Jet_neEmEF,Jet_muEF)")
        return d

    def applyJvm(self,d):
        if not (('2022' in self.year) or ('2023' in self.year) or ('2024' in self.year)):
            raise Exception("Jet map veto not implemented for year {}!".format(self.year))
        d = d.Define('Jet_mapveto','GetJetVeto(jetmapvetoeva, "jetvetomap", Jet_eta, Jet_phi)')
        d = d.Define('Jet_sel_mapveto','(Jet_jetId_TightLepVeto) && (Jet_neEmEF+Jet_chEmEF<0.9) && (Jet_pt_corr>15)')
        d = d.Define('nJet_mapvetoed','Sum(Jet_mapveto[Jet_sel_mapveto])')

        d = d.Filter('nJet_mapvetoed==0')
        return d

    def addBTag(self,d):
        d_wp = { #tight, medium ,loose
                '2017': [0.7476, 0.3040, 0.0532],
                '2018': [0.7100, 0.2783, 0.0490],
                '2022Pre': [0.7183, 0.3086, 0.0583],
                '2022Post': [0.73, 0.3196, 0.0614],
                '2023Pre': [0.6553, 0.2431, 0.0479],
                '2023Post': [0.6563, 0.2435, 0.048],
                '2024': [0.4648, 0.1272, 0.0246],
                }

        btagvar = "Jet_btagDeepFlavB"
        if "2024" in self.year:
            btagvar = "Jet_btagUParTAK4B"
        d = d.Define("Jet_btag_loose","{0}>{1}".format(btagvar,d_wp[self.year][2]))
        d = d.Define("Jet_btag_medium","{0}>{1}".format(btagvar,d_wp[self.year][1]))
        d = d.Define("Jet_btag_tight","{0}>{1}".format(btagvar,d_wp[self.year][0]))

        return d

    def AddVars(self,d):
        d = self.ApplyNoiseFilters(d)
        # Add years first
        d = d.DefinePerSample("year",'"{}"'.format(self.year))
        d = d.DefinePerSample("isData",'{}'.format(1 if self.isData else 0))
        # Apply JERC 
        if ('2022' in self.year) or ('2023' in self.year) or ('2024' in self.year):
            if ("corrections" in self.cfg) and (self.cfg['corrections'] is not None) and ('JERC' in self.cfg['corrections']) and (self.cfg['corrections']['JERC']):
                d = self.AddJERCVars(d)
                d = self.ApplyJERCSystRun3(d)
            d = self.AddJetID(d)
            if ("corrections" in self.cfg) and ('jetmapveto' in self.cfg['corrections']) and (self.cfg['corrections']['jetmapveto'] is not None) and ('use' in self.cfg['corrections']['jetmapveto']) and (self.cfg['corrections']['jetmapveto']['use']):
                d = self.applyJvm(d)
        d = self.addBTag(d)
        # Run 2 on-top JERC/unclustered systematic variations (before the MET xy correction)
        if ('2017' in self.year) or ('2018' in self.year):
            d = self.ApplyJERCSystRun2(d)
        # MET xy corrections
        # FIXME: Is this needed for run3?
        if ("corrections" in self.cfg) and (self.cfg['corrections'] is not None) and ('metxy' in self.cfg['corrections']) and (self.cfg['corrections']['metxy']):
            if ('2017' in self.year) or ('2018' in self.year):
                d = d.Define("MET_corr",'SDV::METXYCorr_Met_MetPhi(MET_pt,MET_phi,run,"{}",{},PV_npvs)'.format(self.year,"false" if self.isData else "true"))
                d = d.Define("MET_pt_corr",'MET_corr.first')
                d = d.Define("MET_phi_corr",'MET_corr.second')
        if ('mapveto' in self.cfg):
          d = d.Define("SDVSecVtx_mapveto","return ROOT::VecOps::Map(SDVSecVtx_x,SDVSecVtx_y, [](float x, float y){return h_mm->GetBinContent(h_mm->FindBin(x,y)) > 0.01;})")
        vars_to_define = ['new_variables']
        for v in vars_to_define:
          if (not v in self.cfg) or (self.cfg[v] is None):
            continue 
          if self.cfg[v] is not None:
            for newvar in self.cfg[v]:
              if isinstance(self.cfg[v][newvar],list):
                formatstr = [self.cfg[self.cfg[v][newvar][i]] for i in range(1,len(self.cfg[v][newvar]))]
                var_define = self.cfg[v][newvar][0].format(*formatstr)
              elif isinstance(self.cfg[v][newvar],str):
                var_define = self.cfg[v][newvar]
              d = d.Define(newvar,var_define)
        # HEM veto for 2018 data
        #if self.year=="2018" and self.isData:
        #  d = d.Define("nJetHEM", self.cfg['nJetHEM'])
        #else:
        #  d = d.Define("nJetHEM", "0")
        return d
    
    def AddVarsWithSelection(self,d):
      if not self.cfg['objects']:
        return d
      for obj in self.cfg['objects']:
        selections = self.cfg['objects'][obj]['selections']
        variables  = self.cfg['objects'][obj]['variables']
        if obj in self.custom_weights:
          # mask the custom weight column like any other object variable so it stays
          # aligned with the selected object columns
          variables = list(variables) + ['{}_customweight'.format(obj)]
        for sel in selections:
          for v in variables:
            if selections[sel]:
              d = d.Define(v+sel,"{0}[{1}]".format(v,selections[sel]))
            else:
              d = d.Define(v+sel,"{0}".format(v))
          if ('nm1' in self.cfg['objects'][obj]) and (self.cfg['objects'][obj]['nm1']):
            nm1s = self.cfg['objects'][obj]['nm1']
            cutstr_objsel = ""
            if selections[sel]:
              cutstr_objsel = "({}) && ".format(selections[sel])
            for i in range(len(nm1s)):
              cutstrs = []
              for j in range(len(nm1s)):
                if j==i:
                  continue
                cutstrs.append("({})".format(''.join(nm1s[j])))
              cutstr = "&&".join(cutstrs)
              cutstr = cutstr_objsel + "({})".format(cutstr)
              d = d.Define(nm1s[i][0]+sel+'_nm1',"{0}[{1}]".format(nm1s[i][0],cutstr))
              #print("define {}: {}".format(nm1s[i][0]+sel+'_nm1',"{0}[{1}]".format(nm1s[i][0],cutstr)))

      return d
    
    def FilterEvents(self,d):
      d_filter = d.Filter(self.presel)
      return d_filter

    def AddWeights(self,d,weight):
      if self.isData:
        d = self.applyCorrections(d)
        d = d.Define("evt_weight","{0}{1}".format(weight,self.weightstr))
      else:
        d = self.applyCorrections(d)
        d = d.Define("evt_weight","Generator_weight*{0}{1}".format(weight,self.weightstr))
      return d
    
    def getRDF(self):
      '''
      This function gets RDataFrame for a given sample
      - Add desired variables
      - Filter events
      - Produce normalisation weights based on xsec
      '''
      d = ROOT.RDataFrame("Events",self.filelist)
      d = self.AddVars(d)
      d = self.AddCustomWeights(d)
      d = self.AddVarsWithSelection(d)
      if self.cfg['presel'] is not None:
        d = d.Filter(self.cfg['presel'])
      if self.lumi==-1:
        xsec_weights = 1
      else:
        nevt = self.getSumWeight()
        if nevt==-1:
          print("No sum weight record, using total events in NanoAOD... This is deprecated because it could introduce a problem when splitting a sample into multiple jobs.")
          dw = ROOT.RDataFrame("Runs",self.filelist)
          nevt = dw.Sum("genEventSumw")
          nevt = nevt.GetValue()
          print("Total events in NanoAOD {}".format(nevt))
        xsec_weights = self.lumi*self.s.xsec/(nevt)
        print("Total gen events {}, xsec {}, weight {}".format(nevt,self.s.xsec,xsec_weights))
      d = self.AddWeights(d,xsec_weights)
      d = self.AddObjectPlotWeights(d)
      return d,xsec_weights

    def getplotsOld(self,d,weight):
      dhs = dict()
      for varlabel in self.dplots:
        hs = []
        plots = self.dplots[varlabel][0]
        plots_2d = self.dplots[varlabel][1]
        for plt in plots:
          if self.isData:
            h = d.Histo1D(tuple(self.cfg['plot_setting'][plt]),plt+varlabel)
          else:
            h = d.Histo1D(tuple(self.cfg['plot_setting'][plt]),plt+varlabel,weight)
          hs.append(h)
    
        for x in plots_2d:
          for y in plots_2d[x]:
            xax = tuple(self.cfg['plot_setting'][x])
            yax = tuple(self.cfg['plot_setting'][y])
            xtitle_idx0 = xax[1].find(';')
            xtitle_idx1 = xax[1].find(';',xtitle_idx0+1)
            xtitle = xax[1][xtitle_idx0+1:xtitle_idx1]
            ytitle_idx0 = yax[1].find(';')
            ytitle_idx1 = yax[1].find(';',ytitle_idx0+1)
            ytitle = yax[1][ytitle_idx0+1:ytitle_idx1]
            hset = (xax[0]+'_vs_'+yax[0],";{0};{1}".format(xtitle,ytitle),xax[2],xax[3],xax[4],yax[2],yax[3],yax[4])
            if self.isData:
              h = d.Histo2D(hset,x+varlabel,y_varlabel)
            else:
              h = d.Histo2D(hset,x+varlabel,y_varlabel,weight)
            hs.append(h)
    
        for i in range(len(hs)):
          hs[i] = hs[i].Clone()
          hs[i].SetName(hs[i].GetName())

        dhs[varlabel] = hs
    
      return dhs
    
    def getplots(self,d,weight,plots_1d,plots_2d,plots_nm1,varlabel,obj_weight=None):
      hs = []
      if plots_1d is None:
        plots_1d = []
      if plots_2d is None:
        plots_2d = []
      if plots_nm1 is None:
        plots_nm1 = []

      # per-object custom weight column: overrides the event weight for the 1D/2D plots
      # (MC only, like all weights; data histograms stay unweighted); N-1 plots keep
      # the event weight (their masks differ from the object selection)
      plot_weight = None
      if not self.isData:
        plot_weight = obj_weight if obj_weight is not None else weight

      for plt in plots_1d:
        if not plt in self.cfg['plot_setting']:
          print("{} not registered in plot setting!".format(plt))
        if plot_weight is None:
          h = d.Histo1D(tuple(self.cfg['plot_setting'][plt]),plt+varlabel)
        else:
          h = d.Histo1D(tuple(self.cfg['plot_setting'][plt]),plt+varlabel,plot_weight)
        hs.append(h)

      for plt in plots_nm1:
        nm1_setting = (self.cfg['plot_setting'][plt[0]]).copy()
        nm1_setting[0] += 'nm1'
        nm1_setting = tuple(nm1_setting)
        if self.isData:
          h = d.Histo1D(nm1_setting,plt[0]+varlabel+'_nm1')
        else:
          h = d.Histo1D(nm1_setting,plt[0]+varlabel+'_nm1',weight)
        hs.append(h)
    
      for x,y in plots_2d:
          xax = tuple(self.cfg['plot_setting'][x])
          yax = tuple(self.cfg['plot_setting'][y])
          xtitle_idx0 = xax[1].find(';')
          xtitle_idx1 = xax[1].find(';',xtitle_idx0+1)
          xtitle = xax[1][xtitle_idx0+1:xtitle_idx1]
          ytitle_idx0 = yax[1].find(';')
          ytitle_idx1 = yax[1].find(';',ytitle_idx0+1)
          ytitle = yax[1][ytitle_idx0+1:ytitle_idx1]
          hset = (xax[0]+'_vs_'+yax[0],";{0};{1}".format(xtitle,ytitle),xax[2],xax[3],xax[4],yax[2],yax[3],yax[4])
          x2d = x+varlabel
          if x not in plots_1d:
            print("Warning! Variable {} not registered in this level!".format(x))
            x2d = x
          y2d = y+varlabel
          if y not in plots_1d:
            print("Warning! Variable {} not registered in this level!".format(y))
            y2d = y
          #h = d.Histo2D(hset,x+varlabel,y+varlabel,weight)
          if plot_weight is None:
            h = d.Histo2D(hset,x2d,y2d)
          else:
            h = d.Histo2D(hset,x2d,y2d,plot_weight)
          hs.append(h)
    
      for i in range(len(hs)):
        hs[i] = hs[i].Clone()
        hs[i].SetName(hs[i].GetName())

      return hs

    def writeplots(self,rootdir,d,weight,plots_1d,plots_2d,varlabel):
      hs = self.getplots(d,weight,plots_1d,plots_2d,varlabel)
      rootdir.cd()
      for h in hs:
        h.Write()

    def getpklData(self,d):
      output = {}
      if 'savepkl' in self.cfg:
        for ii in self.cfg['savepkl']:
          temparr = d.Take[d.GetColumnType(ii)](ii)
          output[ii] = np.array(temparr.GetValue())

      return output


    def makeHistFiles(self):
        if not os.path.exists(self.outputDir):
            os.makedirs(self.outputDir)
        fout = ROOT.TFile("{}/{}_hist{}.root".format(self.outputDir,self.s.name,self.postfix),"RECREATE")
        self.getFileList()
        d,w = self.getRDF()

        d_pkl = {}

        for sr in self.cfg['regions']:
          print("Plotting region {}".format(sr))
          d_sr = d
          if self.cfg['regions'][sr] is not None:
            d_sr = d_sr.Filter(self.cfg['regions'][sr])
          #ROOT.RDF.Experimental.AddProgressBar(d_sr)

          # Prepare data to pickle file
          d_pkl[sr] = self.getpklData(d_sr)

          newd_evt = fout.mkdir("{}_evt".format(sr))
          hs = self.getplots(d_sr,weight="evt_weight",plots_1d=self.cfg['event_variables'],plots_2d=self.cfg['event_2d_plots'],plots_nm1=self.cfg.get('event_nm1'),varlabel="")
          newd_evt.cd()
          for h in hs:
            h.Write()
          #self.writeplots(newd_evt,d=d_sr,weight="evt_weight",plots_1d=self.cfg['event_variables'],plots_2d=self.cfg['event_2d_plots'],varlabel="")
          if self.cfg['objects']:
            for obj in self.cfg['objects']:
              for sels in self.cfg['objects'][obj]['selections']:
                newd = fout.mkdir("{}_{}_{}".format(sr,obj,sels))
                obj_weight = None
                if obj in self.custom_weights:  # MC only: empty for data
                  obj_weight = '{}_plotweight{}'.format(obj,sels)
                hs = self.getplots(d=d_sr,weight="evt_weight",plots_1d=self.cfg['objects'][obj]['variables'],plots_2d=self.cfg['objects'][obj]['2d_plots'],plots_nm1=self.cfg['objects'][obj].get('nm1'),varlabel=sels,obj_weight=obj_weight)
                newd.cd()
                for h in hs:
                  h.Write()
                #self.writeplots(newd,d=d_sr,weight="evt_weight",plots_1d=self.cfg['objects'][obj]['variables'],plots_2d=self.cfg['objects'][obj]['2d_plots'],varlabel=sels)

        fout.Close()
        with open("{}/{}_hist{}.pkl".format(self.outputDir,self.s.name,self.postfix), "wb") as f:
          pickle.dump(d_pkl,f)
  
  
def AddHists(hs,ws):
  assert len(hs)==len(ws)
  for i in range(len(hs)):
    hs[i].Scale(ws[i])
    if i>0:
      hs[0].Add(hs[i])
  return hs[0]

def StackHists(hs,ws):
  assert len(hs)==len(ws)
  h = ROOT.THStack("h","")
  for i in range(len(hs)):
    hs[i].Scale(ws[i])
    hs[i].SetLineColor(i+1)
    hs[i].SetFillColor(i+1)
    h.Add(hs[i])
  return h



def comparehists(name,hs,legend,colors,scale):
  c = ROOT.TCanvas("c"+name,"c"+name,600,600)
  l = ROOT.TLegend(0.6,0.7,0.9,0.9)
  y_max = 0
  for i in range(len(hs)):
    if scale:
      hs[i].Scale(1./hs[i].Integral())
    hs[i].SetLineWidth(2)
    hs[i].SetLineColor(colors[i])
    y_max = max(y_max,hs[i].GetMaximum())

  for i in range(len(hs)):
    if i==0:
      hs[i].SetMaximum(1.2*y_max)
      hs[i].DrawClone()
    else:
      hs[i].DrawClone("same")
    l.AddEntry(hs[i],legend[i])

  l.Draw()
  c.Update()
  c.SaveAs("{}.pdf".format(name))

