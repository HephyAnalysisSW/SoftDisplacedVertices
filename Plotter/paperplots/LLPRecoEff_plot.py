from array import array
import os, ROOT
import cmsstyle as CMS
ROOT.EnableImplicitMT(16)
ROOT.gStyle.SetOptStat(0)
ROOT.gROOT.SetBatch(1)

def write(font, size, x, y, text):
    w = ROOT.TLatex()
    w.SetNDC()
    w.SetTextFont(font)
    w.SetTextSize(size)
    w.DrawLatex(x, y, text)
    return w

def AddVars(d):
    d = d.Define("LLP_Lxy","sqrt((LLP_decay_x-PV_x)*(LLP_decay_x-PV_x)+(LLP_decay_y-PV_y)*(LLP_decay_y-PV_y))")
    d = d.Define("LLP_Lxy_genreconstructable", "LLP_Lxy[LLP_ngentk>=2]")
    d = d.Define("LLP_Lxy_reconstructable", "LLP_Lxy[LLP_ngentk>=2 & LLP_nrecotk>=2]")
    d = d.Define("LLP_Lxy_match_dau", "LLP_Lxy[LLP_ngentk>=2 & LLP_nrecotk>=2 & LLP_matchedSDVIdx_bydau>=0 & LLP_matchedSDVnDau_bydau>=2]")

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

    d = d.Define("SDVSecVtx_nTracks_match","SDVSecVtx_nTracks[SDVSecVtx_matchedLLPIdx_bydau>=0]")
    
    d = d.Define("SDVSecVtx_TkMaxdphi","SDV_TkMaxdphi(SDVIdxLUT_TrackIdx, SDVIdxLUT_SecVtxIdx, nSDVSecVtx, SDVTrack_phi)")
    d = d.Define("SDVSecVtx_TkMindphi","SDV_TkMindphi(SDVIdxLUT_TrackIdx, SDVIdxLUT_SecVtxIdx, nSDVSecVtx, SDVTrack_phi)")
    
    d = d.Define("MET_corr",'SDV::METXYCorr_Met_MetPhi(MET_pt,MET_phi,run,"{}",{},PV_npvs)'.format(self.year,"false" if self.isData else "true"))
    d = d.Define("MET_pt_corr",'MET_corr.first')
    d = d.Define("MET_phi_corr",'MET_corr.second')
    
    return d

def geteffptg(d):
    #bins = [0.05,0.0941825,0.177407,0.334172,0.629463,1.18569,2.23342,4.20698,7.92447,14.9269,28.1171,52.9627,187.91870]
    bins = [i for i in range(0,51)]
    h_LLP_Lxy_genreconstructable = d.Histo1D(("LLP_Lxy_genreconstructable","LLP_Lxy_genreconstructable",len(bins)-1,array('d',bins)),"LLP_gentk_sumpt_genreconstructable")
    h_LLP_Lxy_genreconstructable.Clone()
    h_LLP_Lxy_reconstructable = d.Histo1D(("LLP_Lxy_reconstructable","LLP_Lxy_reconstructable",len(bins)-1,array('d',bins)),"LLP_gentk_sumpt_reconstructable")
    h_LLP_Lxy_reconstructable.Clone()

    h_LLP_Lxy = d.Histo1D(("LLP_Lxy","LLP_Lxy",len(bins)-1,array('d',bins)),"LLP_gentk_sumpt")
    h_LLP_Lxy.Clone()

    h_LLP_Lxy_match_bydau = d.Histo1D(("LLP_Lxy_match_bydau","LLP_Lxy_match_bydau",len(bins)-1,array('d',bins)),"LLP_gentk_sumpt_match_dau")
    h_LLP_Lxy_match_bydau.Clone()


    h_neu = h_LLP_Lxy_match_bydau.GetValue()
    h_den = h_LLP_Lxy.GetValue()
    h_den_gen = h_LLP_Lxy_genreconstructable.GetValue()
    h_den_reco = h_LLP_Lxy_reconstructable.GetValue()
    r = ROOT.TEfficiency(h_neu, h_den_reco)
    r.SetLineWidth(2)
    r.SetTitle(";LLP #Sigmap_{T}^{gentk} (GeV);Efficiency")

    return r

def geteffptg_all(d):
    #bins = [0.0075,0.014,0.0265,0.05,0.0941825,0.177407,0.334172,0.629463,1.18569,2.23342,4.20698,7.92447,14.9269,28.1171,52.9627,187.91870]
    bins = [i for i in range(0,51)]
    h_LLP_Lxy_genreconstructable = d.Histo1D(("LLP_Lxy_genreconstructable","LLP_Lxy_genreconstructable",len(bins)-1,array('d',bins)),"LLP_gentk_sumpt_genreconstructable")
    h_LLP_Lxy_genreconstructable.Clone()
    h_LLP_Lxy_reconstructable = d.Histo1D(("LLP_Lxy_reconstructable","LLP_Lxy_reconstructable",len(bins)-1,array('d',bins)),"LLP_gentk_sumpt_reconstructable")
    h_LLP_Lxy_reconstructable.Clone()

    h_LLP_Lxy = d.Histo1D(("LLP_Lxy","LLP_Lxy",len(bins)-1,array('d',bins)),"LLP_gentk_sumpt")
    h_LLP_Lxy.Clone()

    h_LLP_Lxy_match_bydau = d.Histo1D(("LLP_Lxy_match_bydau","LLP_Lxy_match_bydau",len(bins)-1,array('d',bins)),"LLP_gentk_sumpt_match_dau")
    h_LLP_Lxy_match_bydau.Clone()

    hs = [h_LLP_Lxy,h_LLP_Lxy_genreconstructable,h_LLP_Lxy_reconstructable,h_LLP_Lxy_match_bydau]
    rs = []

    for i in range(len(hs)-1):
        h_neu = hs[i+1].GetValue()
        h_den = hs[i].GetValue()
        r = ROOT.TEfficiency(h_neu, h_den)
        r.SetLineWidth(2)
        r.SetTitle(";LLP #Sigmap_{T}^{gentk} (GeV);Efficiency")
        rs.append(r)

    return rs

def geteffg(d):
    bins = [0.0075,0.014,0.0265,0.05,0.0941825,0.177407,0.334172,0.629463,1.18569,2.23342,4.20698,7.92447,14.9269,28.1171,52.9627,187.91870]
    h_LLP_Lxy_genreconstructable = d.Histo1D(("LLP_Lxy_genreconstructable","LLP_Lxy_genreconstructable",len(bins)-1,array('d',bins)),"LLP_Lxy_genreconstructable")
    h_LLP_Lxy_genreconstructable.Clone()
    h_LLP_Lxy_reconstructable = d.Histo1D(("LLP_Lxy_reconstructable","LLP_Lxy_reconstructable",len(bins)-1,array('d',bins)),"LLP_Lxy_reconstructable")
    h_LLP_Lxy_reconstructable.Clone()

    h_LLP_Lxy = d.Histo1D(("LLP_Lxy","LLP_Lxy",len(bins)-1,array('d',bins)),"LLP_Lxy")
    h_LLP_Lxy.Clone()

    h_LLP_Lxy_match_bydau = d.Histo1D(("LLP_Lxy_match_bydau","LLP_Lxy_match_bydau",len(bins)-1,array('d',bins)),"LLP_Lxy_match_dau")
    h_LLP_Lxy_match_bydau.Clone()


    h_neu = h_LLP_Lxy_match_bydau.GetValue()
    h_den = h_LLP_Lxy.GetValue()
    h_den_gen = h_LLP_Lxy_genreconstructable.GetValue()
    h_den_reco = h_LLP_Lxy_reconstructable.GetValue()
    r = ROOT.TEfficiency(h_neu, h_den)
    r.SetLineWidth(2)
    r.SetTitle(";LLP L_{xy} (cm);Efficiency")

    return r

def geteffg_all(d):
    bins = [0.0075,0.014,0.0265,0.05,0.0941825,0.177407,0.334172,0.629463,1.18569,2.23342,4.20698,7.92447,14.9269,28.1171,52.9627,187.91870]
    h_LLP_Lxy_genreconstructable = d.Histo1D(("LLP_Lxy_genreconstructable","LLP_Lxy_genreconstructable",len(bins)-1,array('d',bins)),"LLP_Lxy_genreconstructable")
    h_LLP_Lxy_genreconstructable.Clone()
    h_LLP_Lxy_reconstructable = d.Histo1D(("LLP_Lxy_reconstructable","LLP_Lxy_reconstructable",len(bins)-1,array('d',bins)),"LLP_Lxy_reconstructable")
    h_LLP_Lxy_reconstructable.Clone()

    h_LLP_Lxy = d.Histo1D(("LLP_Lxy","LLP_Lxy",len(bins)-1,array('d',bins)),"LLP_Lxy")
    h_LLP_Lxy.Clone()

    h_LLP_Lxy_match_bydau = d.Histo1D(("LLP_Lxy_match_bydau","LLP_Lxy_match_bydau",len(bins)-1,array('d',bins)),"LLP_Lxy_match_dau")
    h_LLP_Lxy_match_bydau.Clone()

    hs = [h_LLP_Lxy,h_LLP_Lxy_genreconstructable,h_LLP_Lxy_reconstructable,h_LLP_Lxy_match_bydau]
    rs = []

    for i in range(len(hs)-1):
        h_neu = hs[i+1].GetValue()
        h_den = hs[i].GetValue()
        r = ROOT.TEfficiency(h_neu, h_den)
        r.SetLineWidth(2)
        r.SetTitle(";LLP L_{xy} (cm);Efficiency")
        rs.append(r)

    return rs

def ploteffg(fs,neu,den):
    bins = [0.0075,0.014,0.0265,0.05,0.0941825,0.177407,0.334172,0.629463,1.18569,2.23342,4.20698,7.92447,14.9269,28.1171,52.9627,187.91870]
    
    assert len(fs)>0
    
    for i in range(len(fs)):
        if i==0:
            h_neu = fs[0].Get(f"{neu}/LLP_Lxy")
            h_den = fs[0].Get(f"{den}/LLP_Lxy")
        else:
            h_neu.Add(fs[i].Get(f"{neu}/LLP_Lxy"))
            h_den.Add(fs[i].Get(f"{den}/LLP_Lxy"))

    r = ROOT.TEfficiency(h_neu, h_den)
    r.SetLineWidth(2)
    r.SetTitle(";LLP transverse dispalcement (cm);Efficiency")

    return r

def ploteffptg(fs,neu,den):
    bins = [0.0075,0.014,0.0265,0.05,0.0941825,0.177407,0.334172,0.629463,1.18569,2.23342,4.20698,7.92447,14.9269,28.1171,52.9627,187.91870]
    
    assert len(fs)>0
    
    for i in range(len(fs)):
        if i==0:
            h_neu = fs[0].Get(f"{neu}/LLP_gentk_sumpt")
            h_den = fs[0].Get(f"{den}/LLP_gentk_sumpt")
        else:
            h_neu.Add(fs[i].Get(f"{neu}/LLP_gentk_sumpt"))
            h_den.Add(fs[i].Get(f"{den}/LLP_gentk_sumpt"))

    r = ROOT.TEfficiency(h_neu, h_den)
    r.SetLineWidth(2)
    r.SetTitle(";LLP #Sigmap_{T}^{gen trk} (GeV);Efficiency")

    return r

def dummygraph(lwidth, marker, mcolor, msize, lcolor):
    # Create a dummy TGraphErrors for the legend
    x = ROOT.std.vector('double')()
    y = ROOT.std.vector('double')()
    ex = ROOT.std.vector('double')()
    ey = ROOT.std.vector('double')()
    x.push_back(0.5)
    y.push_back(1.0)
    ex.push_back(0.0)
    ey.push_back(0.3)
    
    x = array('d',[0.5])
    y = array('d',[1.0])
    ex = array('d',[0.0])
    ey = array('d',[0.3])

    dummy = ROOT.TGraphErrors(len(x), x, y, ex, ey)
    dummy.SetLineColor(mcolor)
    dummy.SetMarkerStyle(marker)
    dummy.SetMarkerColor(mcolor)
    dummy.SetLineWidth(lwidth)
    dummy.SetMarkerSize(msize)
    
    return dummy

fn17_25 = "/scratch-cbe/users/ang.li/SoftDV/Histos/Histos_geneff/C1N2_M400_375_ct20_2017_hist.root"
f17_25 = ROOT.TFile.Open(fn17_25)
fn18_25 = "/scratch-cbe/users/ang.li/SoftDV/Histos/Histos_geneff/C1N2_M400_375_ct20_2018_hist.root"
f18_25 = ROOT.TFile.Open(fn18_25)

fn17_12 = "/scratch-cbe/users/ang.li/SoftDV/Histos/Histos_geneff/C1N2_M400_388_ct20_2017_hist.root"
f17_12 = ROOT.TFile.Open(fn17_12)
fn18_12 = "/scratch-cbe/users/ang.li/SoftDV/Histos/Histos_geneff/C1N2_M400_388_ct20_2018_hist.root"
f18_12 = ROOT.TFile.Open(fn18_12)

fn17_25_old = "/scratch-cbe/users/ang.li/SoftDV/Histos/Histos_geneff_oldIVF2/C1N2_M400_375_ct20_2017_hist.root"
f17_25_old = ROOT.TFile.Open(fn17_25_old)
fn18_25_old = "/scratch-cbe/users/ang.li/SoftDV/Histos/Histos_geneff_oldIVF2/C1N2_M400_375_ct20_2018_hist.root"
f18_25_old = ROOT.TFile.Open(fn18_25_old)

fn17_12_old = "/scratch-cbe/users/ang.li/SoftDV/Histos/Histos_geneff_oldIVF2/C1N2_M400_388_ct20_2017_hist.root"
f17_12_old = ROOT.TFile.Open(fn17_12_old)
fn18_12_old = "/scratch-cbe/users/ang.li/SoftDV/Histos/Histos_geneff_oldIVF2/C1N2_M400_388_ct20_2018_hist.root"
f18_12_old = ROOT.TFile.Open(fn18_12_old)

r25 = ploteffg([f17_25,f18_25],"All_LLP_match","All_LLP_all")
r12 = ploteffg([f17_12,f18_12],"All_LLP_match","All_LLP_all")
r25_old = ploteffg([f17_25_old,f18_25_old],"All_LLP_match","All_LLP_all")
r12_old = ploteffg([f17_12_old,f18_12_old],"All_LLP_match","All_LLP_all")

#CMS.SetExtraText("Simulation Preliminary")
CMS.SetExtraText("Simulation")
CMS.SetLumi("")
canv = CMS.cmsCanvas('', 0.0075, 200, 0, 1.0, 'Transverse displacement of the LLP decay vertex (cm)', 'Efficiency', square = CMS.kSquare, extraSpace=0.01, iPos=0)
canv.Draw()
hf = canv.GetListOfPrimitives().FindObject("hframe")
hf.GetXaxis().SetLabelSize(0.035)
hf.GetXaxis().SetTitleSize(0.04)
hf.GetXaxis().SetTitleOffset(1.4)
hf.GetYaxis().SetLabelSize(0.035)
hf.GetYaxis().SetTitleSize(0.04)
hf.GetYaxis().SetTitleOffset(1.4)
canv.Update()
leg = CMS.cmsLeg(0.2, 0.6, 0.90, 0.75, textSize=0.035)
leg.Draw()

#bins = [0.05,0.0941825,0.177407,0.334172,0.629463,1.18569,2.23342,4.20698,7.92447,14.9269,28.1171,52.9627,187.91870]
CMS.cmsDraw(r25, "e1same", lwidth = 2, marker=20, mcolor=ROOT.kBlue, msize = 1, lcolor = ROOT.kBlue) 
CMS.cmsDraw(r12, "e1same", lwidth = 2, marker=21, mcolor=ROOT.kRed, msize = 1, lcolor = ROOT.kRed)  
CMS.cmsDraw(r25_old, "e1same", lwidth = 2, marker=24, mcolor=ROOT.kBlue, msize = 1, lcolor = ROOT.kBlue, lstyle=2) 
CMS.cmsDraw(r12_old, "e1same", lwidth = 2, marker=25, mcolor=ROOT.kRed, msize = 1, lcolor = ROOT.kRed, lstyle=2)  

#d1 = dummygraph(lwidth = 2, marker=20, mcolor=ROOT.kBlue, msize = 1, lcolor = ROOT.kBlue)
#d2 = dummygraph(lwidth = 2, marker=20, mcolor=ROOT.kRed, msize = 1, lcolor = ROOT.kRed)
#d3 = dummygraph(lwidth = 2, marker=21, mcolor=ROOT.kBlue, msize = 1, lcolor = ROOT.kBlue)
#d4 = dummygraph(lwidth = 2, marker=21, mcolor=ROOT.kRed, msize = 1, lcolor = ROOT.kRed)


leg.AddEntry(r25,"#Deltam = 25 GeV, tuned IVF",'lp')
leg.AddEntry(r12,"#Deltam = 12 GeV, tuned IVF",'lp')
leg.AddEntry(r25_old,"#Deltam = 25 GeV, default IVF",'lp')
leg.AddEntry(r12_old,"#Deltam = 12 GeV, default IVF",'lp')
desc = "#tilde{#chi}^{#pm}_{1} #rightarrow f#bar{f}'#kern[0.2]{#tilde{#chi}^{0}_{1}}, #tilde{#chi}^{0}_{2} #rightarrow f#bar{f}#kern[0.1]{#tilde{#chi}^{0}_{1}}"
param = "m_{#kern[0.1]{LLP}} = 400 GeV, c#tau = 20 mm"
#param2 = "#Delta m = 25 GeV, c#tau=20 mm"
write(42, 0.04, 0.2, 0.85, desc)
write(42, 0.04, 0.2, 0.79, param)
#write(42, 0.04, 0.35, 0.64, param2)

canv.SetLogx()
canv.RedrawAxis()
canv.Update()
canv.Draw()

CMS.SaveCanvas(canv,"LLPeff_lxy.pdf")
