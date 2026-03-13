#!/usr/bin/env python3

import ROOT
import argparse
import os
import sys
import array
import cmsstyle as CMS
import numpy as np

ROOT.gROOT.SetBatch(True)
colors = [1,2,4,8]

def find_x_at_efficiency(eff, target):
    h = eff.GetTotalHistogram()
    nbins = h.GetNbinsX()

    for i in range(1, nbins):
        y1 = eff.GetEfficiency(i)
        y2 = eff.GetEfficiency(i + 1)

        if y1 < target <= y2:
            x1 = h.GetXaxis().GetBinCenter(i)
            x2 = h.GetXaxis().GetBinCenter(i + 1)

            x = x1 + (target - y1) * (x2 - x1) / (y2 - y1)
            return x
    return None

def find_first_unity_crossing(graph):
    n = graph.GetN()

    for i in range(n - 1):
        x1 = graph.GetPointX(i)
        y1 = graph.GetPointY(i)
        x2 = graph.GetPointX(i + 1)
        y2 = graph.GetPointY(i + 1)

        # Check if the segment crosses y = 1
        if (y1 - 1) * (y2 - 1) <= 0 and y1 != y2:
            # Linear interpolation
            x_cross = x1 + (1 - y1) * (x2 - x1) / (y2 - y1)
            return x_cross

    return None  # no crossing found

bins = array.array(
        'd',
        [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200, 210, 220, 240, 250, 260, 280, 300, 500, 1000]
    )

bins = array.array(
        'd',
        [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200, 210, 220, 230, 240, 250, 260, 270, 280, 290, 300, 400, 500, 700, 1000]
    )

bins = array.array(
        'd',
    [0, 20, 40, 60, 80, 100, 120, 140, 160, 180, 200, 220, 240, 260, 280, 300, 320, 340, 360, 380, 400, 420, 440, 460, 480, 500, 700, 1000]
)

def main_orig(file_list,direc,var,rb=2,ymin=0.0000005):
    #args = parse_args()

    #input_dir = "/groups/hephy/cms/lisa.benato/SDV/trigger_muon_histo_run2/muon2017f/"
    #output_dir = "/groups/hephy/cms/lisa.benato/SDV/trigger_efficiency_run2_distributions_muon2017f/"
    input_dir = "/groups/hephy/cms/lisa.benato/SDV/trigger_muon_histo_run2_IsoMu27_ISR_split_by_run/"
    output_dir = "/groups/hephy/cms/lisa.benato/SDV/trigger_efficiency_run2_IsoMu27_ISR_split_by_run/compare_good_bad/"
    
    tag = ""
        
    if not os.path.isdir(input_dir):
        print(f"ERROR: Input directory '{input_dir}' does not exist")
        sys.exit(1)

    # Collect ROOT files
    den = {}
    num = {}
    eff = {}
    for fi in file_list:
        # Check if current directory path contains "era"
        fn = input_dir+fi+".root"
        print(f"Opening {fn}")
        if os.path.isfile(fn): 
            f = ROOT.TFile.Open(fn, "READ")
            if not f or f.IsZombie():
                raise RuntimeError(f"Could not open ROOT file: {input_file}")
            h_den = f.Get(f"All{direc}/{var}")
            h_num = f.Get(f"num{direc}/{var}")
            
            if not h_den:
                raise RuntimeError(f"Histogram not found in {fn}")
            if not h_num:
                raise RuntimeError(f"Histogram not found in {fn}")

            if not h_den.InheritsFrom("TH1"):
                raise TypeError(f"Object in {fn} is not a TH1, got {h_den.ClassName()}")
            if not h_num.InheritsFrom("TH1"):
                raise TypeError(f"Object in {fn} is not a TH1, got {h_num.ClassName()}")

            h_den.SetDirectory(0)
            h_num.SetDirectory(0)

            num[fi] = h_num.Rebin(rb)#len(bins)-1, "num_rb", bins)
            den[fi] = h_den.Rebin(rb)#len(bins)-1, "den_rb", bins)

            num[fi].SetDirectory(0)
            den[fi].SetDirectory(0)

            eff[fi] = ROOT.TEfficiency(num[fi], den[fi])

            eff[fi].SetDirectory(0)

            den[fi].Scale(1./den[fi].Integral())
            num[fi].Scale(1./num[fi].Integral())
            #den[fi].SetDirectory(0)
            #num[fi].SetDirectory(0)
            f.Close()

    
    c = ROOT.TCanvas("c", "den", 800, 700)
    c.cd()
    c.SetTicks(1, 1)
    c.SetGrid()

    leg = ROOT.TLegend(0.50, 0.20, 0.88, 0.35)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0)
    leg.SetTextSize(0.04)

    for i,era in enumerate(file_list):
        print(i,era,den[era])
        den[era].SetTitle("")
        den[era].Draw("HISTO,sames")
        num[era].Draw("PE,sames")
        eff[era].Draw("PE,sames")
        den[era].GetXaxis().SetTitle(var)
        den[era].GetXaxis().SetTitleSize(0.045)
        den[era].GetYaxis().SetTitleSize(0.045)
        den[era].GetXaxis().SetLabelSize(0.045)
        den[era].GetYaxis().SetLabelSize(0.045)
        den[era].GetYaxis().SetRangeUser(ymin, 1.05)
        den[era].SetMarkerColor(colors[i])
        den[era].SetMarkerSize(0.0001)
        den[era].SetMarkerStyle(20)
        den[era].SetLineColor(colors[i])
        den[era].SetLineWidth(2)

        eff[era].SetMarkerColor(colors[i])
        eff[era].SetMarkerSize(0.0001)
        eff[era].SetMarkerStyle(20)
        eff[era].SetLineColor(colors[i])
        eff[era].SetLineWidth(2)

        num[era].SetMarkerColor(colors[i])
        #num[era].SetMarkerSize(0.0001)
        num[era].SetMarkerStyle(21)
        num[era].SetLineColor(colors[i])
        num[era].SetLineWidth(2)
        if i==0:
            leg.AddEntry(eff[era], "efficiency good", "PEL")
            leg.AddEntry(den[era], "den good", "L")
            leg.AddEntry(num[era], "num good", "PE")
        if i>0:
            leg.AddEntry(eff[era], "efficiency bad", "PEL")
            leg.AddEntry(den[era], "den bad", "L")
            leg.AddEntry(num[era], "num bad", "PE")

    leg.Draw()

    latex = ROOT.TLatex()
    latex.SetNDC()
    latex.SetTextSize(0.045)
    latex.SetTextFont(62)
    latex.DrawLatex(0.1, 0.94, "CMS")
    latex.SetTextFont(52)
    latex.DrawLatex(0.26, 0.94, "Preliminary")
    latex.SetTextFont(42)
    #latex.DrawLatex(0.65, 0.94, "%.1f fb^{-1} (13.6 TeV)"%float(lumi))
    latex.DrawLatex(0.65, 0.94, "13.6 TeV")

    c.SetLogy()
    c.SaveAs(output_dir+var+".png")
    c.SaveAs(output_dir+var+".pdf")

def main(file_list,direc,var,rb=2,ymin=0.0000005,rmin=0.5,rmax=2.5):
    #args = parse_args()

    #input_dir = "/groups/hephy/cms/lisa.benato/SDV/trigger_muon_histo_run2/muon2017f/"
    #output_dir = "/groups/hephy/cms/lisa.benato/SDV/trigger_efficiency_run2_distributions_muon2017f/"
    input_dir = "/groups/hephy/cms/lisa.benato/SDV/trigger_muon_histo_run2_IsoMu27_ISR_split_by_run/"
    output_dir = "/groups/hephy/cms/lisa.benato/SDV/trigger_efficiency_run2_IsoMu27_ISR_split_by_run/compare_good_bad/"
    
    tag = ""
        
    if not os.path.isdir(input_dir):
        print(f"ERROR: Input directory '{input_dir}' does not exist")
        sys.exit(1)

    # Collect ROOT files
    den = {}
    num = {}
    eff = {}
    for fi in file_list:
        # Check if current directory path contains "era"
        fn = input_dir+fi+".root"
        print(f"Opening {fn}")
        if os.path.isfile(fn): 
            f = ROOT.TFile.Open(fn, "READ")
            if not f or f.IsZombie():
                raise RuntimeError(f"Could not open ROOT file: {input_file}")
            h_den = f.Get(f"All{direc}/{var}")
            h_num = f.Get(f"num{direc}/{var}")
            
            if not h_den:
                raise RuntimeError(f"Histogram not found in {fn}")
            if not h_num:
                raise RuntimeError(f"Histogram not found in {fn}")

            if not h_den.InheritsFrom("TH1"):
                raise TypeError(f"Object in {fn} is not a TH1, got {h_den.ClassName()}")
            if not h_num.InheritsFrom("TH1"):
                raise TypeError(f"Object in {fn} is not a TH1, got {h_num.ClassName()}")

            h_den.SetDirectory(0)
            h_num.SetDirectory(0)

            num[fi] = h_num.Rebin(rb)#len(bins)-1, "num_rb", bins)
            den[fi] = h_den.Rebin(rb)#len(bins)-1, "den_rb", bins)

            num[fi].SetDirectory(0)
            den[fi].SetDirectory(0)

            eff[fi] = ROOT.TEfficiency(num[fi], den[fi])

            eff[fi].SetDirectory(0)

            den[fi].Scale(1./den[fi].Integral())
            num[fi].Scale(1./num[fi].Integral())
            #den[fi].SetDirectory(0)
            #num[fi].SetDirectory(0)
            f.Close()

    
    c = ROOT.TCanvas("c", "den", 800, 800)

    pad1 = ROOT.TPad("pad1", "top pad", 0, 0.30, 1, 1)
    pad2 = ROOT.TPad("pad2", "bottom pad", 0, 0.00, 1, 0.30)

    pad1.SetBottomMargin(0.1)#(0.02)
    pad1.SetRightMargin(0.2)#(0.02)

    pad2.SetTopMargin(0.05)
    pad2.SetBottomMargin(0.30)
    pad2.SetRightMargin(0.2)#(0.02)

    pad1.Draw()
    pad2.Draw()

    #w#c.cd()
    #w#c.SetTicks(1, 1)
    #w#c.SetGrid()

    # ==========================
    # TOP PAD
    # ==========================
    pad1.cd()
    pad1.SetLogy()
    pad1.SetGrid()
    
    #leg = ROOT.TLegend(0.50, 0.20, 0.88, 0.35)
    leg = ROOT.TLegend(0.80, 0.20, 1.0, 0.65)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0)
    leg.SetTextSize(0.04)

    for i,era in enumerate(file_list):
        print(i,era,den[era])
        den[era].SetTitle("")
        den[era].Draw("HISTO,sames")
        num[era].Draw("PE,sames")
        eff[era].Draw("PE,sames")
        den[era].GetXaxis().SetTitle(var)
        den[era].GetXaxis().SetTitleSize(0.045)
        den[era].GetYaxis().SetTitleSize(0.045)
        den[era].GetXaxis().SetLabelSize(0.045)
        den[era].GetYaxis().SetLabelSize(0.045)
        den[era].GetYaxis().SetRangeUser(ymin, 1.05)
        den[era].SetMarkerColor(colors[i])
        den[era].SetMarkerSize(0.0001)
        den[era].SetMarkerStyle(20)
        den[era].SetLineColor(colors[i])
        den[era].SetLineWidth(2)

        eff[era].SetMarkerColor(colors[i])
        eff[era].SetMarkerSize(0.0001)
        eff[era].SetMarkerStyle(20)
        eff[era].SetLineColor(colors[i])
        eff[era].SetLineWidth(2)

        num[era].SetMarkerColor(colors[i])
        #num[era].SetMarkerSize(0.0001)
        num[era].SetMarkerStyle(21)
        num[era].SetLineColor(colors[i])
        num[era].SetLineWidth(2)
        if i==0:
            leg.AddEntry(eff[era], "eff good", "PEL")
            leg.AddEntry(den[era], "den good", "L")
            leg.AddEntry(num[era], "num good", "PE")
        if i>0:
            leg.AddEntry(eff[era], "eff bad", "PEL")
            leg.AddEntry(den[era], "den bad", "L")
            leg.AddEntry(num[era], "num bad", "PE")

    leg.Draw()

    latex = ROOT.TLatex()
    latex.SetNDC()
    latex.SetTextSize(0.045)
    latex.SetTextFont(62)
    latex.DrawLatex(0.1, 0.94, "CMS")
    latex.SetTextFont(52)
    latex.DrawLatex(0.26, 0.94, "Preliminary")
    latex.SetTextFont(42)
    #latex.DrawLatex(0.65, 0.94, "%.1f fb^{-1} (13.6 TeV)"%float(lumi))
    latex.DrawLatex(0.65, 0.94, "13.6 TeV")
    pad1.SetLogy()

    
    # ==========================
    # RATIO PAD
    # ==========================
    pad2.cd()
    pad2.SetGrid()

    era_good = file_list[0]
    era_bad  = file_list[1]

    # ---- DEN RATIO ----
    ratio_den = den[era_good].Clone("ratio_den")
    ratio_den.Divide(den[era_bad])

    ratio_den.SetLineColor(ROOT.kBlue)
    ratio_den.SetMarkerColor(ROOT.kBlue)
    ratio_den.SetMarkerStyle(20)

    # ---- NUM RATIO ----
    ratio_num = num[era_good].Clone("ratio_num")
    ratio_num.Divide(num[era_bad])

    ratio_num.SetLineColor(ROOT.kGreen+2)#kBlack)
    ratio_num.SetMarkerColor(ROOT.kGreen+2)#kBlack)
    ratio_num.SetMarkerStyle(21)

    # ---- EFFICIENCY RATIO ----
    # Build TH1 efficiencies manually for ratio

    h_eff_good = den[era_good].Clone("h_eff_good")
    h_eff_bad  = den[era_bad].Clone("h_eff_bad")

    # Use original (non-normalized) histograms for efficiency
    h_eff_good.Divide(num[era_good], den[era_good], 1., 1., "B")
    h_eff_bad.Divide(num[era_bad],  den[era_bad],  1., 1., "B")

    ratio_eff = h_eff_good.Clone("ratio_eff")
    ratio_eff.Divide(h_eff_bad)

    ratio_eff.SetLineColor(ROOT.kViolet)#Red)
    ratio_eff.SetMarkerColor(ROOT.kViolet)#Red)
    ratio_eff.SetMarkerStyle(22)

    # Axis styling
    ratio_den.GetYaxis().SetTitle("Good / Bad")
    ratio_den.GetYaxis().SetTitleSize(0.10)
    ratio_den.GetYaxis().SetLabelSize(0.08)
    ratio_den.GetYaxis().SetTitleOffset(0.5)
    ratio_den.GetYaxis().SetRangeUser(0.5, 1.5)
    ratio_den.GetYaxis().SetRangeUser(rmin, rmax)

    ratio_den.GetXaxis().SetTitle(var)
    ratio_den.GetXaxis().SetTitleSize(0.12)
    ratio_den.GetXaxis().SetLabelSize(0.10)

    ratio_den.Draw("HISTO")
    ratio_num.Draw("PE SAME")
    ratio_eff.Draw("PEL SAME")

    legr = ROOT.TLegend(0.80, 0.30, 1.0, 0.7)
    legr.SetBorderSize(0)
    legr.SetFillStyle(0)
    legr.SetTextSize(0.1)
    legr.AddEntry(ratio_den,"ratio den","L")
    legr.AddEntry(ratio_num,"ratio num","PE")
    legr.AddEntry(ratio_eff,"ratio eff","PEL")
    legr.Draw("SAMES")
    
    # Unity line
    line = ROOT.TLine(
        ratio_den.GetXaxis().GetXmin(),
        1.0,
        ratio_den.GetXaxis().GetXmax(),
        1.0
    )
    line.SetLineStyle(2)
    line.Draw()
    c.SaveAs(output_dir+var+".png")
    c.SaveAs(output_dir+var+".pdf")

    
f1 = "muon2017f_hist_0"
f2 = "muon2017f_hist_54"

f1 = "merged_histo_good"
f2 = "merged_histo_bad"
'''
if __name__ == "__main__":
    main([f1,f2],direc="_evt",var="MET_pt_nomu")
    main([f1,f2],direc="_evt",var="MET_pt_corr")
    main([f1,f2],direc="_evt",var="MET_phi_corr")
    main([f1,f2],direc="_Muon_tight_sel",var="Muon_pt",rb=1)
    main([f1,f2],direc="_Muon_tight_sel",var="Muon_phi")
    main([f1,f2],direc="_Muon_tight_sel",var="Muon_eta")
'''

main([f1,f2],direc="_evt",var="PV_npvsGood",rb=2,ymin=0.0001,rmin=0.5,rmax=2.5)
main([f1,f2],direc="_evt",var="MET_pt_nomu",rb=2,ymin=0.0001,rmin=0.5,rmax=1.5)
main([f1,f2],direc="_evt",var="MET_pt_corr",rb=2,ymin=0.0001,rmin=0.5,rmax=1.5)
main([f1,f2],direc="_evt",var="MET_phi_corr",rb=8,ymin=0.0001,rmin=0.7,rmax=1.3)
main([f1,f2],direc="_Muon_tight_sel",var="Muon_pt",rb=2,ymin=0.0001,rmin=0.7,rmax=1.3)
main([f1,f2],direc="_Muon_tight_sel",var="Muon_phi",rb=8,ymin=0.0001,rmin=0.7,rmax=1.3)
main([f1,f2],direc="_Muon_tight_sel",var="Muon_eta",rb=2,ymin=0.0001,rmin=0.5,rmax=1.7)
main([f1,f2],direc="_evt",var="HT_sel",rb=4,ymin=0.0001,rmin=0.5,rmax=1.5)
