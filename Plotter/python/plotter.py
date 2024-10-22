import os
import yaml
import ROOT
import correctionlib
correctionlib.register_pyroot_binding()
import SoftDisplacedVertices.Samples.Samples as s
ROOT.gInterpreter.Declare('#include "{}/src/SoftDisplacedVertices/Plotter/RDFHelper.h"'.format(os.environ['CMSSW_BASE']))
ROOT.gInterpreter.Declare('#include "{}/src/SoftDisplacedVertices/Plotter/METxyCorrection.h"'.format(os.environ['CMSSW_BASE']))
ROOT.EnableImplicitMT(2)
# Maybe let ROOT decide the number of threads to use
# ROOT.EnableImplicitMT()
ROOT.gROOT.SetBatch(ROOT.kTRUE)
ROOT.TH1.SetDefaultSumw2(True)
ROOT.gStyle.SetOptStat(0)

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

  def setCorrections(self):
    if 'corrections' in self.cfg and self.cfg['corrections'] is not None:
      if 'PU' in self.cfg['corrections'] and self.cfg['corrections']['PU'] is not None:
        ROOT.gInterpreter.Declare('auto puf = correction::CorrectionSet::from_file("{}");'.format(self.cfg['corrections']['PU']['path']))
        ROOT.gInterpreter.Declare('auto pu = puf->at("{}");'.format(self.cfg['corrections']['PU']['name']))
      if 'electron' in self.cfg['corrections'] and self.cfg['corrections']['electron'] is not None:
        ROOT.gInterpreter.Declare('auto elec = correction::CorrectionSet::from_file("{}");'.format(self.cfg['corrections']['electron']['path']))
        ROOT.gInterpreter.Declare('auto elesf = elec->at("{}");'.format(self.cfg['corrections']['electron']['name']))
      if 'photon' in self.cfg['corrections'] and self.cfg['corrections']['photon'] is not None:
        ROOT.gInterpreter.Declare('auto phoc = correction::CorrectionSet::from_file("{}");'.format(self.cfg['corrections']['photon']['path']))
        ROOT.gInterpreter.Declare('auto phosf = phoc->at("{}");'.format(self.cfg['corrections']['photon']['name']))
      if 'muon' in self.cfg['corrections'] and self.cfg['corrections']['muon'] is not None:
        ROOT.gInterpreter.Declare('auto muc = correction::CorrectionSet::from_file("{}");'.format(self.cfg['corrections']['muon']['path']))
        ROOT.gInterpreter.Declare('auto musf = muc->at("{}");'.format(self.cfg['corrections']['muon']['name']))


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
          d = d.Define("puweight",('pu->evaluate({{Pileup_nTrueInt,"{0}"}})'.format(self.cfg['corrections']['PU']['mode'])))
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
    elif self.s is not None:
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
    with open(self.info_path,'r') as f_sample_info:
      sample_info = yaml.safe_load(f_sample_info)
    for i in sample_info:
      if not self.s.name in i:
        continue
      return sample_info[i]['totalsumWeights']
    print("No sum weight record found for {}!".format(self.s.name))
    return -1
  
  def AddVars(self,d):
      # MET xy corrections
      # d = d.Define("MET_corr",'SDV::METXYCorr_Met_MetPhi(MET_pt,MET_phi,run,"{}",{},PV_npvs)'.format(self.year,"false" if self.isData else "true"))
      # d = d.Define("MET_pt_corr",'MET_corr.first')
      # d = d.Define("MET_phi_corr",'MET_corr.second')
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
      if self.year=="2018" and self.isData:
        d = d.Define("nJetHEM", self.cfg['nJetHEM'])
      else:
        d = d.Define("nJetHEM", "0")
      return d
  
  def AddVarsWithSelection(self,d):
    if not self.cfg['objects']:
      return d
    for obj in self.cfg['objects']:
      selections = self.cfg['objects'][obj]['selections']
      variables  = self.cfg['objects'][obj]['variables']
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
  
  def getplots(self,d,weight,plots_1d,plots_2d,plots_nm1,varlabel):
    print('DEBUG: Getting...')
    print('DEBUG: d', d)
    print('DEBUG: weight', weight)
    print('DEBUG: plots_1d', plots_1d)
    print('DEBUG: plots_2d', plots_2d)
    print('DEBUG: plots_nm1', plots_nm1)
    print('DEBUG: varlabel', varlabel)
    hs = []
    if plots_1d is None:
      plots_1d = []
    if plots_2d is None:
      plots_2d = []
    if plots_nm1 is None:
      plots_nm1 = []

    for plt in plots_1d:
      if not plt in self.cfg['plot_setting']:
        print("{} not registered in plot setting!".format(plt))
      if self.isData:
        h = d.Histo1D(tuple(self.cfg['plot_setting'][plt]),plt+varlabel)
      else:
        h = d.Histo1D(tuple(self.cfg['plot_setting'][plt]),plt+varlabel,weight)
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
        if self.isData:
          h = d.Histo2D(hset,x2d,y2d)
        else:
          h = d.Histo2D(hset,x2d,y2d,weight)
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

  def makeHistFiles(self):
      if not os.path.exists(self.outputDir):
          os.makedirs(self.outputDir)
      fout = ROOT.TFile("{}/{}_hist{}.root".format(self.outputDir,self.s.name,self.postfix),"RECREATE")
      self.getFileList()
      d,w = self.getRDF()

      for sr in self.cfg['regions']:
        print(f"DEBUG: sr {sr}.")
        d_sr = d
        if self.cfg['regions'][sr] is not None:
          d_sr = d_sr.Filter(self.cfg['regions'][sr])
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
              hs = self.getplots(d=d_sr,weight="evt_weight",plots_1d=self.cfg['objects'][obj]['variables'],plots_2d=self.cfg['objects'][obj]['2d_plots'],plots_nm1=self.cfg['objects'][obj].get('nm1'),varlabel=sels)
              newd.cd()
              for h in hs:
                h.Write()
              #self.writeplots(newd,d=d_sr,weight="evt_weight",plots_1d=self.cfg['objects'][obj]['variables'],plots_2d=self.cfg['objects'][obj]['2d_plots'],varlabel=sels)

      fout.Close()
  
  
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

