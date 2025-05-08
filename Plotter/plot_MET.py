import os
import ROOT
import SoftDisplacedVertices.Samples.Samples as s
ROOT.gInterpreter.Declare('#include "{}/src/SoftDisplacedVertices/Plotter/RDFHelper.h"'.format(os.environ['CMSSW_BASE']))
ROOT.EnableImplicitMT(4)
ROOT.gROOT.SetBatch(ROOT.kTRUE)
ROOT.TH1.SetDefaultSumw2(True)
ROOT.gStyle.SetOptStat(0)

def getRDF(s):
  fns = s.getFileList(label,"NANO")
  d = ROOT.RDataFrame("Events",fns)
  d = AddVars(d)
  d = AddVarsWithSelection(d,variables,"SDVSecVtx_ngoodTrack>=2 & SDVSecVtx_LxySig>=20","sel")
  d = AddVarsWithSelection(d,variables,"SDVSecVtx_matchedLLPIdx_bydau>=0","mat")
  d = FilterEvents(d)
  dw = ROOT.RDataFrame("Runs",fns)
  nevt = dw.Sum("genEventSumw")
  xsec_weights = lumi*s.xsec/nevt.GetValue() # FIXME: this does not work for samples with GenFilters
  d = AddWeights(d,xsec_weights)
  return d,xsec_weights

def makeHistFiles(samples,input_json,label,postfix=""):
  s.loadData(samples,os.path.join(os.environ['CMSSW_BASE'],'src/SoftDisplacedVertices/Samples/json/{}'.format(input_json)),label)
  
  for samp in samples:
    d,w = getRDF(samp)
    hs = getplots(d,plots,plots_2d,"evt_weight")
    fout = ROOT.TFile("{}_{}{}_hist.root".format(samp.name,label,postfix),"RECREATE")
    for h in hs:
      h.Write()
    fout.Close()

def AddWeights(d,weight):
    d = d.Define("evt_weight","Generator_weight*{0}".format(weight))
    return d

def VertexSelection(d):
    return d

def AddVars(d):
    d = d.Define("LLP_Lxy","sqrt((LLP_decay_x-PV_x)*(LLP_decay_x-PV_x)+(LLP_decay_y-PV_y)*(LLP_decay_y-PV_y))")
    d = d.Define("LLP_Lxy_genreconstructable", "LLP_Lxy[LLP_ngentk>=2]")
    d = d.Define("LLP_Lxy_reconstructable", "LLP_Lxy[LLP_ngentk>=2 & LLP_nrecotk>=2]")
    d = d.Define("LLP_Lxy_match_dau", "LLP_Lxy[LLP_ngentk>=2 & LLP_nrecotk>=2 & LLP_matchedSDVIdx_bydau>=0 & LLP_matchedSDVnDau_bydau>=2]")

    d = d.Define("LLP_vtx_dist","LLP_matchedSDVDist_bydau[LLP_matchedSDVIdx_bydau>=0]")

    d = d.Define("SDVSecVtx_nMatchedTk","NMatchedTracksinSDV(SDVTrack_LLPIdx,nSDVSecVtx,SDVIdxLUT_SecVtxIdx,SDVIdxLUT_TrackIdx)")
    d = d.Define("nMatchedSDV","SDVSecVtx_nMatchedTk[SDVSecVtx_nMatchedTk>=1].size()")

    d = d.Define("LLP_matched","SDVIdxinLLP(SDVTrack_LLPIdx, SDVIdxLUT_SecVtxIdx, SDVIdxLUT_TrackIdx, nLLP, nSDVSecVtx, SDVTrack_pt, SDVTrack_eta, SDVTrack_phi)")

    d = d.Define("LLP_nmacheddau_dau", "LLP_matchedSDVnDau_bydau[LLP_matchedSDVIdx_bydau>=0]")

    d = d.Define("LLP_Lxy_match_dist", "LLP_Lxy[LLP_matchedSDVIdx_bydist>=0 & LLP_matchedSDVDist_bydist<=10]")

    d = d.Define("LLP_ntk_genreconstructable", "LLP_ngentk[LLP_ngentk>=2]")
    d = d.Define("LLP_ntk_reconstructable", "LLP_ngentk[LLP_ngentk>=2 & LLP_nrecotk>=2]")
    d = d.Define("LLP_ntk_match_dau", "LLP_ngentk[LLP_ngentk>=2 & LLP_nrecotk>=2 & LLP_matchedSDVIdx_bydau>=0 & LLP_matchedSDVnDau_bydau>=2]")

    d = d.Define("LLP_gentk_sumpt", "LLP_GenTkSumpT(SDVGenPart_isGentk,SDVGenPart_LLPIdx,nLLP,SDVGenPart_pt,SDVGenPart_eta,SDVGenPart_phi,SDVGenPart_mass)")
    d = d.Define("LLP_gentk_sumpt_genreconstructable", "LLP_gentk_sumpt[LLP_ngentk>=2]")
    d = d.Define("LLP_gentk_sumpt_reconstructable", "LLP_gentk_sumpt[LLP_ngentk>=2 & LLP_nrecotk>=2]")
    d = d.Define("LLP_gentk_sumpt_match_dau", "LLP_gentk_sumpt[LLP_ngentk>=2 & LLP_nrecotk>=2 & LLP_matchedSDVIdx_bydau>=0 & LLP_matchedSDVnDau_bydau>=2]")

    d = d.Define("LLP_gentk_maxpt", "LLP_GenTkMaxpT(SDVGenPart_isGentk,SDVGenPart_LLPIdx,nLLP,SDVGenPart_pt,SDVGenPart_eta,SDVGenPart_phi,SDVGenPart_mass)")
    d = d.Define("LLP_gentk_maxpt_genreconstructable", "LLP_gentk_maxpt[LLP_ngentk>=2]")
    d = d.Define("LLP_gentk_maxpt_reconstructable", "LLP_gentk_maxpt[LLP_ngentk>=2 & LLP_nrecotk>=2]")
    d = d.Define("LLP_gentk_maxpt_match_dau", "LLP_gentk_maxpt[LLP_ngentk>=2 & LLP_nrecotk>=2 & LLP_matchedSDVIdx_bydau>=0 & LLP_matchedSDVnDau_bydau>=2]")

    d = d.Define("LLP_gentk_minpt", "LLP_GenTkMinpT(SDVGenPart_isGentk,SDVGenPart_LLPIdx,nLLP,SDVGenPart_pt,SDVGenPart_eta,SDVGenPart_phi,SDVGenPart_mass)")
    d = d.Define("LLP_gentk_minpt_genreconstructable", "LLP_gentk_minpt[LLP_ngentk>=2]")
    d = d.Define("LLP_gentk_minpt_reconstructable", "LLP_gentk_minpt[LLP_ngentk>=2 & LLP_nrecotk>=2]")
    d = d.Define("LLP_gentk_minpt_match_dau", "LLP_gentk_minpt[LLP_ngentk>=2 & LLP_nrecotk>=2 & LLP_matchedSDVIdx_bydau>=0 & LLP_matchedSDVnDau_bydau>=2]")

    d = d.Define("SDVSecVtx_Lxy_err","SDVSecVtx_Lxy/SDVSecVtx_LxySig")
    d = d.Define("SDVSecVtx_dlen_err","SDVSecVtx_dlen/SDVSecVtx_dlenSig")
    d = d.Define("SDVSecVtx_L_eta_abs","abs(SDVSecVtx_L_eta)")

    d = d.Define("SDVSecVtx_TkMaxdphi","SDV_TkMaxdphi(SDVIdxLUT_TrackIdx, SDVIdxLUT_SecVtxIdx, nSDVSecVtx, SDVTrack_phi)")
    d = d.Define("SDVSecVtx_TkMindphi","SDV_TkMindphi(SDVIdxLUT_TrackIdx, SDVIdxLUT_SecVtxIdx, nSDVSecVtx, SDVTrack_phi)")
    d = d.Define("SDVSecVtx_TkMaxdeta","SDV_TkMaxdphi(SDVIdxLUT_TrackIdx, SDVIdxLUT_SecVtxIdx, nSDVSecVtx, SDVTrack_eta)")
    d = d.Define("SDVSecVtx_TkMindeta","SDV_TkMindphi(SDVIdxLUT_TrackIdx, SDVIdxLUT_SecVtxIdx, nSDVSecVtx, SDVTrack_eta)")
    d = d.Define("SDVSecVtx_TkMaxdR","SDV_TkMaxdR(SDVIdxLUT_TrackIdx, SDVIdxLUT_SecVtxIdx, nSDVSecVtx, SDVTrack_eta, SDVTrack_phi)")
    d = d.Define("SDVSecVtx_TkMindR","SDV_TkMindR(SDVIdxLUT_TrackIdx, SDVIdxLUT_SecVtxIdx, nSDVSecVtx, SDVTrack_eta, SDVTrack_phi)")

    d = d.Define("SDVSecVtx_nTracks_match","SDVSecVtx_nTracks[SDVSecVtx_matchedLLPIdx_bydau>=0]")
    d = d.Define("SDVSecVtx_pAngle_match","SDVSecVtx_pAngle[SDVSecVtx_matchedLLPIdx_bydau>=0]")
    d = d.Define("SDVSecVtx_ngoodTrack_match","SDVSecVtx_ngoodTrack[SDVSecVtx_matchedLLPIdx_bydau>=0]")
    d = d.Define("SDVSecVtx_dlen_match","SDVSecVtx_dlen[SDVSecVtx_matchedLLPIdx_bydau>=0]")
    d = d.Define("SDVSecVtx_dlenSig_match","SDVSecVtx_dlenSig[SDVSecVtx_matchedLLPIdx_bydau>=0]")
    d = d.Define("SDVSecVtx_dlen_err_match","SDVSecVtx_dlen_match/SDVSecVtx_dlenSig_match")
    d = d.Define("SDVSecVtx_Lxy_match","SDVSecVtx_Lxy[SDVSecVtx_matchedLLPIdx_bydau>=0]")
    d = d.Define("SDVSecVtx_LxySig_match","SDVSecVtx_LxySig[SDVSecVtx_matchedLLPIdx_bydau>=0]")
    d = d.Define("SDVSecVtx_Lxy_err_match","SDVSecVtx_Lxy_match/SDVSecVtx_LxySig_match")
    d = d.Define("SDVSecVtx_chi2_match","SDVSecVtx_chi2[SDVSecVtx_matchedLLPIdx_bydau>=0]")
    d = d.Define("SDVSecVtx_normalizedChi2_match","SDVSecVtx_normalizedChi2[SDVSecVtx_matchedLLPIdx_bydau>=0]")
    d = d.Define("SDVSecVtx_ndof_match","SDVSecVtx_ndof[SDVSecVtx_matchedLLPIdx_bydau>=0]")

    d = d.Define("nPassSDV","SDVSecVtx_Lxy[SDVSecVtx_ngoodTrack>=2 & SDVSecVtx_LxySig>=20].size()")
    return d

def AddVarsWithSelection(d,variables,selection,postfix):
  for v in variables:
    d = d.Define(v+postfix,"{0}[{1}]".format(v,selection))
  return d

def FilterEvents(d):
  d = d.Filter("RawMET_pt>100")
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

def getplots(d,plots,plots_2d,weight):
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

plots = {
    #'nSDVSecVtx':('nSDVSecVtx',";Number of vertices;A.U.",20,0,20),
    #'SDVSecVtx_Lxy':('SDVSecVtx_Lxy',";vertex L_{xy} (cm);A.U.",100,0,10),
    #'SDVSecVtx_Lxy_err':('SDVSecVtx_Lxy_err',";vertex #sigmaL_{xy} (cm);A.U.",100,0,0.5),
    #'SDVSecVtx_LxySig':('SDVSecVtx_LxySig',";vertex L_{xy}/#sigmaL_{xy};A.U.",500,0,100),
    #'SDVSecVtx_pAngle':('SDVSecVtx_pAngle',";vertex pAngle;A.U.",64,0,3.2),
    #'SDVSecVtx_dlen':('SDVSecVtx_dlen',";vertex dlen (cm);A.U.",100,0,10),
    #'SDVSecVtx_dlen_err':('SDVSecVtx_dlen_err',";vertex #sigmadlen (cm);A.U.",100,0,0.5),
    #'SDVSecVtx_dlenSig':('SDVSecVtx_dlenSig',";vertex dlen/#sigmadlen;A.U.",500,0,100),
    #'SDVSecVtx_nTracks':('SDVSecVtx_nTracks',";vertex nTracks;A.U.",20,0,20),
    #'SDVSecVtx_ngoodTrack':('SDVSecVtx_ngoodTrack',";vertex ngoodTrack;A.U.",20,0,20),
    #'SDVSecVtx_nMatchedTk':('SDVSecVtx_nMatchedTk',";vertex nTrack matched with LLP;A.U.",20,0,20),
    #'SDVSecVtx_chi2':('SDVSecVtx_chi2',";vertex chi2;A.U.",50,0,10),
    #'SDVSecVtx_normalizedChi2':('SDVSecVtx_normalizedChi2',";vertex norm chi2;A.U.",50,0,10),
    #'SDVSecVtx_ndof':('SDVSecVtx_ndof',";vertex ndof;A.U.",20,0,20),
    #'SDVSecVtx_L_eta_abs':('SDVSecVtx_L_eta_abs',";vertex |#eta|;A.U.",200,0,10),
    #'SDVSecVtx_matchedLLPIdx_bydau':('SDVSecVtx_matchedLLPIdx_bydau',";vertex matched LLP idx;A.U.",5,-1,4),
    #'SDVSecVtx_TkMaxdphi':('SDVSecVtx_TkMaxdphi',";vertex track max(d#phi);A.U.",64,0,3.2),
    #'SDVSecVtx_TkMindphi':('SDVSecVtx_TkMindphi',";vertex track min(d#phi);A.U.",64,0,3.2),
    #'SDVSecVtx_TkMaxdeta':('SDVSecVtx_TkMaxdeta',";vertex track max(d#eta);A.U.",100,0,5),
    #'SDVSecVtx_TkMindeta':('SDVSecVtx_TkMindeta',";vertex track min(d#eta);A.U.",100,0,5),
    #'SDVSecVtx_TkMaxdR':('SDVSecVtx_TkMaxdR',";vertex track max(dR);A.U.",100,0,5),
    #'SDVSecVtx_TkMindR':('SDVSecVtx_TkMindR',";vertex track min(dR);A.U.",100,0,5),
    #'nMatchedSDV':('nMatchedSDV',";number of vertices matched with LLP;A.U.",5,0,5),
    #'nPassSDV':('nPassSDV',";number of selected vertices;A.U.",20,0,20),
    'MET_pt':('MET_pt',";MET (GeV);A.U.",125,50,300),
    'RawMET_pt':('RawMET_pt',";RawMET (GeV);A.U.",125,50,300),

    #'LLP_vtx_dist':('LLP_vtx_dist',";dist(LLP,matched reco vtx)/#sigma;A.U.",100,0,10),
    }

plots_2d = {
    'MET_pt':['RawMET_pt'],
    #'SDVSecVtx_dlen':['SDVSecVtx_Lxy','SDVSecVtx_Lxy_err','SDVSecVtx_LxySig','SDVSecVtx_pAngle','SDVSecVtx_dlen_err','SDVSecVtx_dlenSig','SDVSecVtx_nTracks','SDVSecVtx_ngoodTrack','SDVSecVtx_chi2','SDVSecVtx_normalizedChi2','SDVSecVtx_ndof','SDVSecVtx_L_eta_abs'],
    #'SDVSecVtx_Lxy':['SDVSecVtx_L_eta_abs','SDVSecVtx_dlen']
    }

variables = ["SDVSecVtx_nTracks","SDVSecVtx_pAngle","SDVSecVtx_ngoodTrack","SDVSecVtx_dlen","SDVSecVtx_dlenSig","SDVSecVtx_dlen_err","SDVSecVtx_Lxy","SDVSecVtx_LxySig","SDVSecVtx_Lxy_err","SDVSecVtx_chi2","SDVSecVtx_normalizedChi2","SDVSecVtx_ndof","SDVSecVtx_L_eta_abs","SDVSecVtx_matchedLLPIdx_bydau","SDVSecVtx_TkMaxdphi","SDVSecVtx_TkMindphi","SDVSecVtx_TkMaxdeta","SDVSecVtx_TkMindeta","SDVSecVtx_TkMaxdR","SDVSecVtx_TkMindR"]
#for v in variables:
#  for pf in ['sel',"mat"]:
#    pset = list(plots[v])
#    pset[0] = v+pf
#    pset = tuple(pset)
#    plots[v+pf] = pset

ds = {}
ws = {}

lumi = 100000. # units in pb-1

#label = "CustomNanoAODv1_MFV_1_noZrefit"
#input_json = "CustomNanoAODv1_MFV_1_noZrefit.json"
label = "CustomNanoAODv1_IVF_1"
input_json = "CustomNanoAODv1_IVF_1.json"
postfix = 'cut100'
ss = s.znunu_2018
makeHistFiles(ss,input_json,label,postfix)
ss = [s.stop_2018[1]]
makeHistFiles(ss,input_json,label,postfix)


#label = "CustomNanoAODv1_MFV_1"
#input_json = "CustomNanoAODv1_MFV_1.json"
#ss = s.znunu_2018
#makeHistFiles(ss,input_json,label)
#ss = [s.stop_2018[1]]
#makeHistFiles(ss,input_json,label)
