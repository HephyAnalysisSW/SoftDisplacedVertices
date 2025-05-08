import os
import yaml
import ROOT
import SoftDisplacedVertices.Samples.Samples as s
ROOT.gInterpreter.Declare('#include "{}/src/SoftDisplacedVertices/Plotter/RDFHelper.h"'.format(os.environ['CMSSW_BASE']))
ROOT.EnableImplicitMT(4)
ROOT.gROOT.SetBatch(ROOT.kTRUE)
ROOT.TH1.SetDefaultSumw2(True)
ROOT.gStyle.SetOptStat(0)

def getSumWeight(s):
  info_path = os.path.join(os.environ['CMSSW_BASE'],'src/SoftDisplacedVertices/Plotter/CustomMiniAOD_v3_{}.yaml'.format(s.name))
  with open(info_path,'r') as f_sample_info:
    sample_info = yaml.safe_load(f_sample_info)
  for i in sample_info:
    if not s.name in i:
      continue
    return sample_info[i]['totalsumWeights']
  assert(False,"no record found for sum weights!")
  return -1



def getRDF(s,dvars=dict(),evt_sel=''):
  '''
  This functino gets RDataFrame for a given sample
  - Add desired variables
  - Filter events
  - Produce normalisation weights based on xsec
  
  Parameters:
    s: sample to retrieve
    dvars: a dictionary {variable postfix: (variables to add, selection)}
    evt_sel: event selection
  '''
  fns = s.getFileList(label,"")
  d = ROOT.RDataFrame("Events",fns)
  d = AddVars(d)
  for k in dvars:
    d = AddVarsWithSelection(d,dvars[k][0],dvars[k][1],k)
  #d = AddVarsWithSelection(d,variables,"SDVSecVtx_ParTScore>0.98","tag")
  #d = AddVarsWithSelection(d,variables,"SDVSecVtx_ParTScore<0.98","untag")
  #d = AddVarsWithSelection(d,variables,"SDVSecVtx_matchedLLPnDau_bydau>1","genmatch")
  #d = AddVarsWithSelection(d,variables,"SDVSecVtx_matchedLLPnDau_bydau>1 && SDVSecVtx_ParTScore>0.98","genmatchtag")
  #evt_sel = "MET_pt>200&&HLT_PFMET120_PFMHT120_IDTight && Jet_pt[0]>100 && !nMuon && !nPhoton && !nTau && !nElectron && Flag_METFilters && Jet_chHEF[0]>0.1 && Jet_neHEF[0]<0.8"
  d = FilterEvents(d,evt_sel)
  nevt = getSumWeight(s)
  xsec_weights = lumi*s.xsec/(nevt)
  #dw = ROOT.RDataFrame("Runs",fns)
  #nevt = dw.Sum("genEventSumw")
  #xsec_weights = lumi*s.xsec/(nevt.GetValue()/s.filter_eff) # FIXME: this does not work for samples with GenFilters
  d = AddWeights(d,xsec_weights)
  return d,xsec_weights

def makeHistFiles(samples,input_json,label):
  s.loadData(samples,os.path.join(os.environ['CMSSW_BASE'],'src/SoftDisplacedVertices/Samples/json/{}'.format(input_json)),label)
  
  for samp in samples:
    fout = ROOT.TFile("{}_{}_hist.root".format(samp.name,label),"RECREATE")
    d,w = getRDF(samp)
    hs = getplots(d,plots,plots_2d,"evt_weight",postfix="")
    for h in hs:
      h.Write()
    CCsel = "nSDVSecVtx_CCsel>0"
    MLsel = "nSDVSecVtx_MLsel>0"
    dCC = d.Filter(CCsel)
    dML = d.Filter(MLsel)
    for di,n in zip([dCC,dML],["CC","ML"]):
      hs = getplots(di,plots_div,plots_2d,"evt_weight",postfix=n)
      for h in hs:
        h.Write()
    fout.Close()

def makeHistFiles_METSlice(samples,input_json,label):
  s.loadData(samples,os.path.join(os.environ['CMSSW_BASE'],'src/SoftDisplacedVertices/Samples/json/{}'.format(input_json)),label)
  
  for samp in samples:
    fout = ROOT.TFile("{}_{}_hist.root".format(samp.name,label),"RECREATE")
    d,w = getRDF(samp)
    hs = getplots(d,plots,plots_2d,"evt_weight",postfix="")
    for h in hs:
      h.Write()
    MET_sel = {
        'lowMET':  "MET_pt<400 && MET_pt>200",
        'midMET':  "MET_pt<600 && MET_pt>400",
        'highMET': "MET_pt>600",
        }
    for metsel in MET_sel:
      dsel = d.Filter(MET_sel[metsel])
      hs = getplots(dsel,plots,plots_2d,"evt_weight",postfix=metsel)
      for h in hs:
        h.Write()

    fout.Close()

def AddWeights(d,weight):
    d = d.Define("evt_weight","Generator_weight*{0}".format(weight))
    return d

def VertexSelection(d):
    return d

def AddVars(d):
    d = d.Define("SDVTrack_isGoodTrack","( (abs(SDVTrack_dxy)/SDVTrack_dxyError)>4 ) && (SDVTrack_normalizedChi2 < 5) && (abs(SDVTrack_dz)<4.) && (SDVTrack_numberOfValidHits>13) && ( (SDVTrack_ptError/SDVTrack_pt)<0.015 ) && ( acos(cos(SDVTrack_phi-Jet_phi[0]))>1 ) && ( acos(cos(SDVTrack_phi-MET_phi))<1.5 )")
    d = d.Define("SDVSecVtx_nGoodTrack","SDVSecVtx_nGoodTrack(SDVIdxLUT_SecVtxIdx,SDVIdxLUT_TrackIdx,SDVTrack_isGoodTrack,nSDVSecVtx)")
    vtx_sel_CC = "( acos(cos(SDVSecVtx_L_phi-MET_phi))<1.5 )&&(SDVSecVtx_LxySig>=20.)&&(SDVSecVtx_pAngle>0.2)&&(SDVSecVtx_nGoodTrack>=2)&&( acos(cos(SDVSecVtx_L_phi-Jet_phi[0]))>1 ) && (SDVSecVtx_ndof>1)"
    vtx_sel_ML = "( acos(cos(SDVSecVtx_L_phi-MET_phi))<1.5 ) && (SDVSecVtx_ParTScore>0.98) && ( acos(cos(SDVSecVtx_L_phi-Jet_phi[0]))>1 )"
    d = d.Define("nSDVSecVtx_CCsel","Sum({})".format(vtx_sel_CC))
    d = d.Define("nSDVSecVtx_MLsel","Sum({})".format(vtx_sel_ML))

    d = d.Define("SDVSecVtx_dphi_L_MET","acos(cos(SDVSecVtx_L_phi-MET_phi))")
    d = d.Define("SDVSecVtx_dphi_L_jet0","acos(cos(SDVSecVtx_L_phi-Jet_phi[0]))")

    d = d.Define("SDVSecVtx_LxySig_CCsel_max","Max(SDVSecVtx_LxySig[{}])".format(vtx_sel_CC))
    d = d.Define("SDVSecVtx_LxySig_MLsel_max","Max(SDVSecVtx_LxySig[{}])".format(vtx_sel_ML))
    d = d.Define("SDVSecVtx_Lxy_err","SDVSecVtx_Lxy/SDVSecVtx_LxySig")
    d = d.Define("SDVSecVtx_dlen_err","SDVSecVtx_dlen/SDVSecVtx_dlenSig")
    d = d.Define("SDVSecVtx_L_eta_abs","abs(SDVSecVtx_L_eta)")

    d = d.Define("SDVSecVtx_TkMaxdphi","SDV_TkMaxdphi(SDVIdxLUT_TrackIdx, SDVIdxLUT_SecVtxIdx, nSDVSecVtx, SDVTrack_phi)")
    d = d.Define("SDVSecVtx_TkMindphi","SDV_TkMindphi(SDVIdxLUT_TrackIdx, SDVIdxLUT_SecVtxIdx, nSDVSecVtx, SDVTrack_phi)")
    d = d.Define("SDVSecVtx_TkMaxdeta","SDV_TkMaxdphi(SDVIdxLUT_TrackIdx, SDVIdxLUT_SecVtxIdx, nSDVSecVtx, SDVTrack_eta)")
    d = d.Define("SDVSecVtx_TkMindeta","SDV_TkMindphi(SDVIdxLUT_TrackIdx, SDVIdxLUT_SecVtxIdx, nSDVSecVtx, SDVTrack_eta)")
    d = d.Define("SDVSecVtx_TkMaxdR","SDV_TkMaxdR(SDVIdxLUT_TrackIdx, SDVIdxLUT_SecVtxIdx, nSDVSecVtx, SDVTrack_eta, SDVTrack_phi)")
    d = d.Define("SDVSecVtx_TkMindR","SDV_TkMindR(SDVIdxLUT_TrackIdx, SDVIdxLUT_SecVtxIdx, nSDVSecVtx, SDVTrack_eta, SDVTrack_phi)")
    return d

def AddVarsWithSelection(d,variables,selection,postfix):
  for v in variables:
    d = d.Define(v+postfix,"{0}[{1}]".format(v,selection))
  return d

def FilterEvents(d,cuts):
  d = d.Filter(cuts)
  return d

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

def getplots(d,plots,plots_2d,weight,postfix=""):
  hs = []
  for plt in plots:
    h = d.Histo1D(plots[plt],plt,weight)
    hs.append(h)

  for x in plots_2d:
    for y in plots_2d[x]:
      xax = plots[x]
      yax = plots[y]
      xtitle_idx0 = xax[1].find(';')
      xtitle_idx1 = xax[1].find(';',xtitle_idx0+1)
      xtitle = xax[1][xtitle_idx0+1:xtitle_idx1]
      ytitle_idx0 = yax[1].find(';')
      ytitle_idx1 = yax[1].find(';',ytitle_idx0+1)
      ytitle = yax[1][ytitle_idx0+1:ytitle_idx1]
      hset = (xax[0]+'_vs_'+yax[0],";{0};{1}".format(xtitle,ytitle),xax[2],xax[3],xax[4],yax[2],yax[3],yax[4])
      h = d.Histo2D(hset,x,y,weight)
      hs.append(h)

  for i in range(len(hs)):
    hs[i] = hs[i].Clone()
    hs[i].SetName(hs[i].GetName()+postfix)

  return hs


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

plots_div = {
    'MET_pt':('MET_pt',";MET (GeV);A.U.",100,0,1000),
    'SDVSecVtx_LxySig_CCsel_max':('SDVSecVtx_LxySig_CCsel_max',";max vertex (CC) L_{xy}/#sigma_{L_{xy}};A.U.",100,0,100),
    'SDVSecVtx_LxySig_MLsel_max':('SDVSecVtx_LxySig_MLsel_max',";max vertex (ML) L_{xy}/#sigma_{L_{xy}};A.U.",100,0,100),
    }

plots = {
    'nSDVSecVtx_CCsel':('nSDVSecVtx_CCsel',";Number of vertices (CC);A.U.",20,0,20),
    'nSDVSecVtx_MLsel':('nSDVSecVtx_MLsel',";Number of vertices (ML);A.U.",20,0,20),
    'SDVSecVtx_ParTScore':('SDVSecVtx_ParTScore',";ParTScore;A.U.",50,0,1),
    'SDVSecVtx_LxySig_CCsel_max':('SDVSecVtx_LxySig_CCsel_max',";max vertex (CC) L_{xy}/#sigma_{L_{xy}};A.U.",100,0,100),
    'SDVSecVtx_LxySig_MLsel_max':('SDVSecVtx_LxySig_MLsel_max',";max vertex (ML) L_{xy}/#sigma_{L_{xy}};A.U.",100,0,100),
    'SDVSecVtx_Lxy':('SDVSecVtx_Lxy',";vertex L_{xy} (cm);A.U.",100,0,10),
    'SDVSecVtx_Lxy_err':('SDVSecVtx_Lxy_err',";vertex #sigmaL_{xy} (cm);A.U.",100,0,0.5),
    'SDVSecVtx_LxySig':('SDVSecVtx_LxySig',";vertex L_{xy}/#sigmaL_{xy};A.U.",500,0,100),
    'SDVSecVtx_dphi_L_MET':('SDVSecVtx_dphi_L_MET',";#Delta#phi(Lxy,MET)",64,0,3.2),
    'SDVSecVtx_dphi_L_jet0':('SDVSecVtx_dphi_L_jet0',";#Delta#phi(Lxy,jet0)",64,0,3.2),
    'SDVSecVtx_pAngle':('SDVSecVtx_pAngle',";vertex pAngle;A.U.",64,0,3.2),
    'SDVSecVtx_dlen':('SDVSecVtx_dlen',";vertex dlen (cm);A.U.",100,0,10),
    'SDVSecVtx_dlen_err':('SDVSecVtx_dlen_err',";vertex #sigmadlen (cm);A.U.",100,0,0.5),
    'SDVSecVtx_dlenSig':('SDVSecVtx_dlenSig',";vertex dlen/#sigmadlen;A.U.",500,0,100),
    'SDVSecVtx_nTracks':('SDVSecVtx_nTracks',";vertex nTracks;A.U.",20,0,20),
    'SDVSecVtx_nGoodTrack':('SDVSecVtx_nGoodTrack',";vertex ngoodTrack;A.U.",20,0,20),
    #'SDVSecVtx_nMatchedTk':('SDVSecVtx_nMatchedTk',";vertex nTrack matched with LLP;A.U.",20,0,20),
    'SDVSecVtx_chi2':('SDVSecVtx_chi2',";vertex chi2;A.U.",50,0,10),
    'SDVSecVtx_normalizedChi2':('SDVSecVtx_normalizedChi2',";vertex norm chi2;A.U.",50,0,10),
    'SDVSecVtx_ndof':('SDVSecVtx_ndof',";vertex ndof;A.U.",20,0,20),
    'SDVSecVtx_L_eta_abs':('SDVSecVtx_L_eta_abs',";vertex |#eta|;A.U.",200,0,10),
    'SDVSecVtx_matchedLLPIdx_bydau':('SDVSecVtx_matchedLLPIdx_bydau',";vertex matched LLP idx;A.U.",5,-1,4),
    'SDVSecVtx_matchedLLPnDau_bydau':('SDVSecVtx_matchedLLPnDau_bydau',";vertex number of tracks matched with LLP;A.U.",10,0,10),
    'SDVSecVtx_TkMaxdphi':('SDVSecVtx_TkMaxdphi',";vertex track max(d#phi);A.U.",64,0,3.2),
    'SDVSecVtx_TkMindphi':('SDVSecVtx_TkMindphi',";vertex track min(d#phi);A.U.",64,0,3.2),
    'SDVSecVtx_TkMaxdeta':('SDVSecVtx_TkMaxdeta',";vertex track max(d#eta);A.U.",100,0,5),
    'SDVSecVtx_TkMindeta':('SDVSecVtx_TkMindeta',";vertex track min(d#eta);A.U.",100,0,5),
    'SDVSecVtx_TkMaxdR':('SDVSecVtx_TkMaxdR',";vertex track max(dR);A.U.",100,0,5),
    'SDVSecVtx_TkMindR':('SDVSecVtx_TkMindR',";vertex track min(dR);A.U.",100,0,5),
    'MET_pt':('MET_pt',";MET (GeV);A.U.",100,0,1000),

    }

plots_2d = {
    #'SDVSecVtx_dlen':['SDVSecVtx_Lxy','SDVSecVtx_Lxy_err','SDVSecVtx_LxySig','SDVSecVtx_pAngle','SDVSecVtx_dlen_err','SDVSecVtx_dlenSig','SDVSecVtx_nTracks','SDVSecVtx_ngoodTrack','SDVSecVtx_chi2','SDVSecVtx_normalizedChi2','SDVSecVtx_ndof','SDVSecVtx_L_eta_abs'],
    #'SDVSecVtx_Lxy':['SDVSecVtx_L_eta_abs','SDVSecVtx_dlen']
    }

evt_sel = "MET_pt>200&&HLT_PFMET120_PFMHT120_IDTight && Jet_pt[0]>100 && !nMuon && !nPhoton && !nTau && !nElectron && Flag_METFilters && Jet_chHEF[0]>0.1 && Jet_neHEF[0]<0.8"

variables = ["SDVSecVtx_nTracks","SDVSecVtx_pAngle","SDVSecVtx_nGoodTrack","SDVSecVtx_dlen","SDVSecVtx_dlenSig","SDVSecVtx_dlen_err","SDVSecVtx_Lxy","SDVSecVtx_LxySig","SDVSecVtx_Lxy_err","SDVSecVtx_chi2","SDVSecVtx_normalizedChi2","SDVSecVtx_ndof","SDVSecVtx_L_eta_abs","SDVSecVtx_matchedLLPIdx_bydau","SDVSecVtx_matchedLLPnDau_bydau","SDVSecVtx_TkMaxdphi","SDVSecVtx_TkMindphi","SDVSecVtx_TkMaxdeta","SDVSecVtx_TkMindeta","SDVSecVtx_TkMaxdR","SDVSecVtx_TkMindR","SDVSecVtx_dphi_L_MET","SDVSecVtx_dphi_L_jet0"]

#plots = {
#    'SDVSecVtx_nGoodTrack':('SDVSecVtx_nGoodTrack',";vertex ngoodTrack;A.U.",20,0,20),
#    'MET_pt':('MET_pt',";MET (GeV);A.U.",100,0,1000),
#    }
#
#variables = ["SDVSecVtx_nGoodTrack"]
for v in variables:
  for pf in ['tag',"untag","genmatch","genmatchtag"]:
    pset = list(plots[v])
    pset[0] = v+pf
    pset = tuple(pset)
    plots[v+pf] = pset

ds = {}
ws = {}

lumi = 59683. # units in pb-1

label = "MLNanoAODv2"
input_json = "MLNanoAOD.json"
ss = s.stop_2018
makeHistFiles(ss,input_json,label)
#makeHistFiles_METSlice(ss,input_json,label)

#scale = 1.23
#lumi = lumi*scale
#ss = s.wlnu_2018 + s.znunu_2018
#makeHistFiles(ss,input_json,label)
##makeHistFiles_METSlice(ss,input_json,label)

