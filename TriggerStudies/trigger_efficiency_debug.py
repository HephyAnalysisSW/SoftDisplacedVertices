#!/usr/bin/env python3

import ROOT
import argparse
import os
import sys
import array
import cmsstyle as CMS
import numpy as np
import json

ROOT.gROOT.SetBatch(True)

def parse_args():
    parser = argparse.ArgumentParser(
        description="Calculate trigger efficiency from ROOT files in a folder"
    )
    parser.add_argument(
        "--inputs",
        required=True,
        help="Input folder containing ROOT files"
    )
    parser.add_argument(
        "--outputs",
        required=True,
        help="Output folder for efficiency ROOT file"
    )
    parser.add_argument(
        "--era",
        required=True,
        help="Data era"
    )
    parser.add_argument(
        "--lumi",
        required=True,
        help="Lumi"
    )
    parser.add_argument(
        "--mc",
        default = False,
        help="mc"
    )
    parser.add_argument(
        "--json_label",
        required=False,
        default = "",
        help="Json label"
    )
    return parser.parse_args()

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

#var = "Muon_pt_sel"
#var = "MET_pt_corr"

def drops_after_full_efficiency(eff, tol=1e-6):
    h = eff.GetTotalHistogram()
    nbins = h.GetNbinsX()

    reached_full = False
    dropped = False
    x_full = None
    x_drop = None

    last_data_bin = 0
    for i in range(nbins, 0, -1):
        if h.GetBinContent(i) > 0:
            last_data_bin = i
            break
    
    for i in range(1, nbins + 1):
        y = eff.GetEfficiency(i)
        x = h.GetXaxis().GetBinCenter(i)

        # detect first time efficiency reaches ~1
        if not reached_full and y >= 1.0 - tol:
            reached_full = True
            x_full = x
            continue

        # after reaching full efficiency, check for drop
        if reached_full and y < 1.0 - tol:
            if i >= last_data_bin:
                break
            dropped = True
            x_drop = x
            break

    return reached_full, dropped, x_full, x_drop

def drops_after_full_efficiency_new(eff,tol=1):
    h = eff.GetTotalHistogram()
    nbins = h.GetNbinsX()

    reached_full = False
    dropped = False
    x_full = None
    x_drop = None

    for i in range(1, nbins + 1):

        val = eff.GetEfficiency(i)

        # first time reaching 100%
        if not reached_full and val >= 0.999:
            reached_full = True
            x_full = h.GetXaxis().GetBinCenter(i)
            continue

        if reached_full:
            if val < 0.999:
                # ignore drop if in last bin (overflow edge)
                if i == nbins:
                    break

                dropped = True
                x_drop = h.GetXaxis().GetBinCenter(i)
                break

    return reached_full, dropped, x_full, x_drop


def two_d(den_folder,num_folder,varx,vary,binsx,binsy,log=False):
    args = parse_args()

    input_dir = args.inputs
    output_dir = args.outputs
    era = args.era
    lumi = args.lumi
    mc = args.mc
    tag = ""
    var = varx+"_vs_"+vary
    
    if mc:
        tag = "WJetsToLNu"
    else:
        tag = "SingleMuon"
    
    if not os.path.isdir(input_dir):
        print(f"ERROR: Input directory '{input_dir}' does not exist")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)

    output_file = os.path.join(output_dir, "efficiency_"+tag+era+".root")

    # Collect ROOT files
    root_files = [
        os.path.join(input_dir, f)
        for f in os.listdir(input_dir)
        if (f.endswith(".root"))# and "hist_40" in f)
    ]

    if len(root_files) == 0:
        print("ERROR: No ROOT files found in input directory")
        sys.exit(1)

    print(f"Found {len(root_files)} ROOT files")
    print(root_files)

    tot_den = None
    tot_num = None

    for fn in root_files:
        print(fn)
        f = ROOT.TFile.Open(fn, "READ")
        if not f or f.IsZombie():
            raise RuntimeError(f"Could not open ROOT file: {input_file}")

        ##### denominator
        
        # Check directory "All_evt"
        den_dir = f.Get(den_folder)
        if not den_dir:
            raise KeyError("Directory den not found in ROOT file")

        # Get histogram "X"
        hden = den_dir.Get(var)
        if not hden:
            raise KeyError("Histogram '"+var+"' not found in directory den")

        # Type check
        if not hden.InheritsFrom("TH2D"):
            raise TypeError(
                f"Object '{den_folder}'"+var+" exists but is not a TH2D (found {hden.ClassName()})"
            )

        # Detach from file so it survives file closing
        hden.SetDirectory(0)

        if tot_den is None:
            tot_den = hden.Clone("tot_den")
            tot_den.Reset()
            tot_den.SetDirectory(0)  # detach from file

        tot_den.Add(hden)



        ##### numerator
        
        # Check directory "num_evt"
        num_dir = f.Get(num_folder)
        if not num_dir:
            raise KeyError("Directory num not found in ROOT file")

        # Get histogram "X"
        hnum = num_dir.Get(var)
        if not hnum:
            raise KeyError("Histogram '"+var+"' not found in directory num ")

        # Type check
        if not hnum.InheritsFrom("TH2D"):
            raise TypeError(
                f"Object '{num_folder}"+var+"' exists but is not a TH2D (found {hnum.ClassName()})"
            )

        # Detach from file so it survives file closing
        hnum.SetDirectory(0)

        if tot_num is None:
            tot_num = hnum.Clone("tot_num")
            tot_num.Reset()
            tot_num.SetDirectory(0)  # detach from file

        tot_num.Add(hnum)


        f.Close()



    #bins = np.linspace(0,1000,50)

    rb = 20
    rbx=10#rb
    rby=20#rb
    rbx = 5
    rby = 5
    num_rb = tot_num.RebinX(rbx)#(len(bins)-1, "num_rb", bins)
    num_rb = tot_num.RebinY(rby)#(len(bins)-1, "num_rb", bins)
    den_rb = tot_den.RebinX(rbx)#(len(bins)-1, "den_rb", bins)
    den_rb = tot_den.RebinY(rby)#(len(bins)-1, "den_rb", bins)

    num_rb.SetDirectory(0)
    den_rb.SetDirectory(0)

    h_eff = num_rb.Clone("h_eff")
    h_eff.Divide(num_rb, den_rb, 1.0, 1.0, "B")

    #h_eff.SetMinimum(0.0001)
    #h_eff.SetMaximum(0.01)
    h_eff.SetMinimum(0.0023)
    h_eff.SetMaximum(0.0051)

    #vs nPV
    #h_eff.SetMinimum(0.4)
    #h_eff.SetMaximum(1.)

    

    #eff.SetMarkerStyle(ROOT.kFullCircle)
    #eff.SetMarkerSize(1.2)
    #eff.SetMarkerColor(922)#(ROOT.kBlack)

    #eff.SetLineColor(922)#(ROOT.kBlack)
    #eff.SetLineWidth(2)
    

    '''
    # Write merged output
    fout = ROOT.TFile(output_file, "RECREATE")
    fout.cd()
    tot_den.Write()
    tot_num.Write()
    eff.Write()
    #gr.Write()
    fout.Close()
    '''

    c = ROOT.TCanvas("c", "Efficiency", 800, 600)
    c.SetTicks(1, 1)
    c.SetGrid()
    h_eff.SetMarkerColor(1)
    ROOT.gStyle.SetPaintTextFormat("4.4f")
    #vs nPV
    #h_eff.SetMarkerSize(1.2)
    #ROOT.gStyle.SetPaintTextFormat("1.1f")
    #h_eff.Draw("COLTEXT")
    ###vs nPV
    ###h_eff.SetMarkerSize(0)
    ###h_eff.Draw("COLZ")
    ##h_eff.SetTitle(";E_{T}^{miss} (no #mu) [GeV];Efficiency L1+HLT")
    h_eff.GetXaxis().SetTitle(varx)
    h_eff.GetYaxis().SetTitle(vary)

    ROOT.gPad.Update()
    
    '''
    eff.GetPaintedGraph().GetXaxis().SetTitleSize(0.045)
    eff.GetPaintedGraph().GetYaxis().SetTitleSize(0.045)
    if log:
        eff.GetPaintedGraph().GetYaxis().SetRangeUser(0.000001, 2.)
    else:
        eff.GetPaintedGraph().GetYaxis().SetRangeUser(0., 1.05)

    leg = ROOT.TLegend(0.50, 0.20, 0.88, 0.35)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0)
    leg.SetTextSize(0.04)
    if mc:
        leg.AddEntry(eff, tag+str(era), "PE")
    else:
        leg.AddEntry(eff, tag+str(era), "PE")
    leg.Draw()
    '''
    latex = ROOT.TLatex()
    latex.SetNDC()
    latex.SetTextSize(0.045)
    latex.SetTextFont(62)
    latex.DrawLatex(0.1, 0.94, "CMS")
    latex.SetTextFont(52)
    latex.DrawLatex(0.26, 0.94, "Preliminary")
    latex.SetTextFont(42)
    latex.DrawLatex(0.65, 0.94, "%.1f fb^{-1} (13.6 TeV)"%float(lumi))
    c.SetLogz()
    c.SaveAs(output_dir+"efficiency_2D_"+tag+era+".png")
    c.SaveAs(output_dir+"efficiency_2D_"+tag+era+".pdf")
    
    print(f"Output written to: {output_file}")

    '''
    CMS.SetExtraText("Preliminary")
    CMS.SetLumi(0)
    canv = CMS.cmsCanvas('', 0.0075, 200, 0, 1.0, 'E_{T}^{miss} no #mu', 'Efficiency', extraSpace=0.01, iPos=0)
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
    CMS.cmsDraw(eff, "ap", lwidth = 2, marker=20, mcolor=ROOT.kBlue, msize = 1, lcolor = ROOT.kBlue) 

    leg.AddEntry(eff,"Data",'pe')

    canv.RedrawAxis()
    canv.Update()
    canv.Draw()
    #CMS.fixOverlay()
    CMS.SaveCanvas(canv,output_dir+"plot.png")
    CMS.SaveCanvas(canv,output_dir+"plot.pdf")
    '''

def one_d(den_folder,num_folder,var,bins,log=False):
    args = parse_args()

    input_dir = args.inputs
    output_dir = args.outputs
    era = args.era
    lumi = args.lumi
    mc = args.mc
    json_label = args.json_label
    tag = ""
    
    if mc:
        tag = "WJetsToLNu"
    else:
        tag = "SingleMuon"
    
    if not os.path.isdir(input_dir):
        print(f"ERROR: Input directory '{input_dir}' does not exist")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)

    output_file = os.path.join(output_dir, "efficiency_"+tag+era+".root")
    if "PV" in var:
        output_file = os.path.join(output_dir, "efficiency_"+tag+era+"_nPV.root")
    
    # Collect ROOT files
    root_files = [
        os.path.join(input_dir, f)
        for f in os.listdir(input_dir)
        if (f.endswith(".root"))# and "hist_40" in f)
    ]

    if len(root_files) == 0:
        print("ERROR: No ROOT files found in input directory")
        sys.exit(1)

    print(f"Found {len(root_files)} ROOT files")
    print(root_files)

    tot_den = None
    tot_num = None

    for fn in root_files:
        print(fn)
        f = ROOT.TFile.Open(fn, "READ")
        if not f or f.IsZombie():
            raise RuntimeError(f"Could not open ROOT file: {input_file}")

        ##### denominator
        
        # Check directory "All_evt"
        den_dir = f.Get(den_folder)
        if not den_dir:
            raise KeyError("Directory den not found in ROOT file")

        # Get histogram "X"
        hden = den_dir.Get(var)
        if not hden:
            raise KeyError("Histogram '"+var+"' not found in directory den")

        # Type check
        if not hden.InheritsFrom("TH1D"):
            raise TypeError(
                f"Object '{den_folder}'"+var+" exists but is not a TH1D (found {hden.ClassName()})"
            )

        # Detach from file so it survives file closing
        hden.SetDirectory(0)

        if tot_den is None:
            tot_den = hden.Clone("tot_den")
            tot_den.Reset()
            tot_den.SetDirectory(0)  # detach from file

        tot_den.Add(hden)



        ##### numerator
        
        # Check directory "num_evt"
        num_dir = f.Get(num_folder)
        if not num_dir:
            raise KeyError("Directory num not found in ROOT file")

        # Get histogram "X"
        hnum = num_dir.Get(var)
        if not hnum:
            raise KeyError("Histogram '"+var+"' not found in directory num ")

        # Type check
        if not hnum.InheritsFrom("TH1D"):
            raise TypeError(
                f"Object '{num_folder}"+var+"' exists but is not a TH1D (found {hnum.ClassName()})"
            )

        # Detach from file so it survives file closing
        hnum.SetDirectory(0)

        if tot_num is None:
            tot_num = hnum.Clone("tot_num")
            tot_num.Reset()
            tot_num.SetDirectory(0)  # detach from file

        tot_num.Add(hnum)


        f.Close()



    #bins = np.linspace(0,1000,100)

    num_rb = tot_num.Rebin(len(bins)-1, "num_rb", bins)
    den_rb = tot_den.Rebin(len(bins)-1, "den_rb", bins)

    num_rb.SetDirectory(0)
    den_rb.SetDirectory(0)

    
    #for i in range(1, num_rb.GetNbinsX()+1):
    for i in range(0, num_rb.GetNbinsX()+2):
        num_c = num_rb.GetBinContent(i)
        den_c = den_rb.GetBinContent(i)
        #print("Good (?) bin:", i)
        #print("num =", num_c, "den =", den_c)

        #print("UNDERFLOW")
        #print("num =", num_rb.GetBinContent(0))
        #print("den =", den_rb.GetBinContent(0))

        #print("OVERFLOW")
        #print("num =", num_rb.GetBinContent(num_rb.GetNbinsX()+1))
        #print("den =", den_rb.GetBinContent(den_rb.GetNbinsX()+1))

        if num_c > den_c:
            print("Problem bin:", i)
            print("num =", num_c, "den =", den_c)

            
    #clipping for numerical precision
    eps = 1e-9

    for i in range(0, num_rb.GetNbinsX()+2):
        num_c = num_rb.GetBinContent(i)
        den_c = den_rb.GetBinContent(i)

        if num_c > den_c and abs(num_c - den_c) < eps:
            num_rb.SetBinContent(i, den_c)

    # Safety check
    if not ROOT.TEfficiency.CheckConsistency(num_rb, den_rb):
        raise RuntimeError("Numerator and denominator histograms are inconsistent")

    eff = ROOT.TEfficiency(num_rb, den_rb)

    # Optional: choose uncertainty type
    eff.SetStatisticOption(ROOT.TEfficiency.kFCP)  # Clopper-Pearson (default)
    eff.SetConfidenceLevel(0.683)
    # eff.SetStatisticOption(ROOT.TEfficiency.kFNormal)  # Gaussian
    # eff.SetStatisticOption(ROOT.TEfficiency.kFWilson)
    # eff.SetStatisticOption(ROOT.TEfficiency.kFAC)

    eff.SetName("efficiency")
    eff.SetTitle(";E_{T}^{miss} (no #mu) [GeV];Efficiency L1+HLT")
    eff.SetTitle(";"+var+";Efficiency L1+HLT")

    eff.SetMarkerStyle(ROOT.kFullCircle)
    eff.SetMarkerSize(1.2)
    eff.SetMarkerColor(922)#(ROOT.kBlack)

    eff.SetLineColor(922)#(ROOT.kBlack)
    eff.SetLineWidth(2)
    
    '''
    gr = ROOT.TGraphAsymmErrors()
    gr.Divide(
        tot_num,
        tot_den,
        "cl=0.683 b(1,1) mode"
    )
    gr.SetName("gr_efficiency")
    gr.SetTitle("Efficiency;MET [GeV]; Efficiency")
    '''



    x20 = find_x_at_efficiency(eff,0.20)
    x40 = find_x_at_efficiency(eff,0.40)
    x60 = find_x_at_efficiency(eff,0.60)
    x80 = find_x_at_efficiency(eff,0.80)
    x95 = find_x_at_efficiency(eff,0.95)
    x99 = find_x_at_efficiency(eff,0.99)
    

    print(x95, x99)

    reached, dropped, x100, xdrop = drops_after_full_efficiency(eff,tol=0.05)

    if reached:
        print(f"Efficiency reaches 100% at x ~ {x100:.2f}")
        if dropped:
            print(f"It drops below 100% again at x ~ {xdrop:.2f}")
        else:
            print("Efficiency stays at 100% afterwards.")
    else:
        print("Efficiency never reaches 100%.")
    
    # Write merged output
    fout = ROOT.TFile(output_file, "RECREATE")
    fout.cd()
    tot_den.Write()
    tot_num.Write()
    eff.Write()
    #gr.Write()
    fout.Close()


    c = ROOT.TCanvas("c", "Efficiency", 800, 600)
    c.SetTicks(1, 1)
    c.SetGrid()
    eff.Draw("AP")

    if x95 is not None:
        line95 = ROOT.TLine(x95, 0, x95, 1)
        line95.SetLineColor(ROOT.kBlue)
        line95.SetLineStyle(2)
        line95.SetLineWidth(2)
        line95.Draw("same")

        latex95 = ROOT.TLatex()
        latex95.SetTextColor(4)
        latex95.SetTextSize(0.035)
        latex95.SetTextAlign(21)  # center horizontally, bottom vertically
        latex95.SetTextAngle(90)   # rotate text 90 degrees
        latex95.DrawLatex(x95, 0.65, f"95% @ {x95:.0f} GeV")

    if x99 is not None:
        line99 = ROOT.TLine(x99, 0, x99, 1)
        line99.SetLineColor(634)
        line99.SetLineStyle(2)
        line99.SetLineWidth(2)
        line99.Draw("same")

        latex99 = ROOT.TLatex()
        latex99.SetTextColor(634)
        latex99.SetTextSize(0.035)
        latex99.SetTextAlign(21)  # center horizontally, bottom vertically
        latex99.SetTextAngle(90)   # rotate text 90 degrees
        latex99.DrawLatex(x99, 0.65, f"99% @ {x99:.0f} GeV")
        
    ROOT.gPad.Update()
    
    eff.GetPaintedGraph().GetXaxis().SetTitleSize(0.045)
    eff.GetPaintedGraph().GetYaxis().SetTitleSize(0.045)
    if log:
        eff.GetPaintedGraph().GetYaxis().SetRangeUser(0.000001, 2.)
    else:
        eff.GetPaintedGraph().GetYaxis().SetRangeUser(0., 1.05)
        
    eff.GetPaintedGraph().GetXaxis().SetLimits(bins[0], bins[-1])
    ROOT.gPad.Modified()
    ROOT.gPad.Update()

    leg = ROOT.TLegend(0.50, 0.20, 0.88, 0.35)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0)
    leg.SetTextSize(0.04)
    if mc:
        leg.AddEntry(eff, tag+str(era), "PE")
    else:
        leg.AddEntry(eff, tag+str(era), "PE")
    leg.Draw()

    latex = ROOT.TLatex()
    latex.SetNDC()
    latex.SetTextSize(0.045)
    latex.SetTextFont(62)
    latex.DrawLatex(0.1, 0.94, "CMS")
    latex.SetTextFont(52)
    latex.DrawLatex(0.26, 0.94, "Preliminary")
    latex.SetTextFont(42)
    if "2022" in era or "2023" in era:
        s = "13.6"
    else:
        s = "13"
    latex.DrawLatex(0.65, 0.94, s+" TeV")
    #latex.DrawLatex(0.65, 0.94, "%.1f fb^{-1} (13.6 TeV)"%float(lumi))
    c.SetLogy(log)
    if "PV" in var:
        c.SaveAs(output_dir+"efficiency_"+tag+era+"_nPV.png")
        c.SaveAs(output_dir+"efficiency_"+tag+era+"_nPV.pdf")
    else:
        c.SaveAs(output_dir+"efficiency_"+tag+era+".png")
        c.SaveAs(output_dir+"efficiency_"+tag+era+".pdf")
        
    print(f"Output written to: {output_file}")

    data_dict = {
        "run": json_label,
        "x20": x20,
        "x40": x40,
        "x60": x60,
        "x80": x80,
        "x95": x95,
        "x99": x99,
        "reached" : reached,
        "dropped": dropped,
        "x100" : x100,
        "xdrop": xdrop,
    }

    output_json = output_dir+"efficiency_"+tag+era+".json"
    if "PV" in var:
        output_json = output_dir+"efficiency_"+tag+era+"_nPV.json"
        
    with open(output_json, "w") as f:
        json.dump(data_dict, f, indent=2)
    print(f"Output json written to: {output_json}")
    
bins = array.array(
    'd',
    [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200, 210, 220, 240, 250, 260, 280, 300, 500, 1000]
)

bins_met = array.array(
    'd',
    [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200, 210, 220, 230, 240, 250, 260, 270, 280, 290, 300, 400, 500, 700, 1000]
)

bins_met = array.array(
    'd',
    [0, 20, 40, 60, 80, 100, 120, 140, 160, 180, 200, 220, 240, 260, 280, 300, 400, 500, 700, 1000]
)

#Less
bins_met = array.array(
    'd',
    [0, 40, 80, 120, 160, 200, 240, 280, 350, 400, 500, 700, 1000]
)

bins_ht = array.array(
    'd',
    [0, 40, 80, 120, 160, 200, 240, 280, 350, 400, 500, 700, 1000, 1500, 2000,]
)

n_bins = 50
xmin = -3.2
xmax = 3.2
step = (xmax - xmin) / n_bins
bins_eta = array.array('d', [xmin + i*step for i in range(n_bins + 1)])
#bins_eta = array.array('d', [-3.2,-2.,-1.,0.,1.,2.,3.2])
bins_eta = array.array('d', [-3.2,-2.5,-2,-1.5,-1,-0.5,0.,0.5,1.,1.5,2.,2.5,3.2])

bins_pv = array.array('d', [ a for a in range(0,101,5)])

one=False
one=True

if one==False:
    #two_d(den_folder="All_Muon_tight_sel",num_folder="num_Muon_tight_sel",varx="Muon_phi",vary="Muon_eta",binsx=bins_eta,binsy=bins_eta,log=False)
    two_d(den_folder="All_evt",num_folder="num_evt",varx="PV_npvsGood",vary="MET_pt_nomu",binsx=bins_pv,binsy=bins_met,log=False)
    #two_d(den_folder="All_evt",num_folder="num_evt",varx="PV_npvs",vary="MET_pt_nomu",binsx=bins_pv,binsy=bins_met,log=False)

if one==True:
    #one_d(den_folder="All_evt",num_folder="num_evt",var = "MET_pt_nomu",bins=bins_met)
    #one_d(den_folder="All_evt",num_folder="num_evt",var = "HT_sel",bins=bins_ht)
    one_d(den_folder="All_evt",num_folder="num_evt",var = "PV_npvsGood",bins=bins_pv,log=True)

    #one_d(den_folder="All_evt",num_folder="num_evt",var = "MET_phi_corr",bins=bins_eta,log=True)
    #one_d(den_folder="den_run305282_evt",num_folder="num_run305282_evt",var = "MET_pt_nomu",bins=bins_met)
    #one_d(den_folder="den_run305516_evt",num_folder="num_run305516_evt",var = "MET_pt_nomu",bins=bins_met)
    #one_d(den_folder="den_run306121_evt",num_folder="num_run306121_evt",var = "MET_pt_nomu",bins=bins_met)
    #one_d(den_folder="den_run306462_evt",num_folder="num_run306462_evt",var = "MET_pt_nomu",bins=bins_met)

    ##one_d(den_folder="All_evt",num_folder="num140_evt",var = "MET_pt_nomu",bins=bins_met)
    #one_d(den_folder="All_evt",num_folder="num_evt",var = "MET_pt_corr",bins=bins_met)
    #one_d(den_folder="All_evt",num_folder="num_evt",var = "MET_phi_corr",bins=bins_eta,log=True)
    #one_d(den_folder="All_Muon_tight_sel",num_folder="num_Muon_tight_sel",var = "Muon_pt",bins=bins_met)
    #one_d(den_folder="All_Muon_tight_sel",num_folder="num_Muon_tight_sel",var = "Muon_eta",bins=bins_eta,log=True)
    #one_d(den_folder="All_Muon_tight_sel",num_folder="num_Muon_tight_sel",var = "Muon_phi",bins=bins_eta,log=True)

    ###################################
    #main(den_folder="All_evt",num_folder="num_evt",var = "MET_pt_nomu_L",bins=bins_met)

    #main(den_folder="1L_evt",num_folder="num1L_evt",var = "MET_pt_nomu_L",bins=bins_met)
    #main(den_folder="1L_evt",num_folder="num1L_evt",var = "MET_pt_corr",bins=bins_met)
    #main(den_folder="1L_evt",num_folder="num1L_evt",var = "MET_phi_corr",bins=bins_eta,log=True)

    #main(den_folder="1T_evt",num_folder="num1T_evt",var = "MET_pt_nomu",bins=bins_met)

    #main(den_folder="AtLeast1T_evt",num_folder="numAtLeast1T_evt",var = "MET_pt_nomu",bins=bins_met)

    #muons
    #main(den_folder="All_Muon_loose_sel",num_folder="num_Muon_loose_sel",var = "Muon_pt",bins=bins_met)
    #main(den_folder="All_Muon_loose_sel",num_folder="num_Muon_loose_sel",var = "Muon_eta",bins=bins_eta,log=True)
    #main(den_folder="All_Muon_loose_sel",num_folder="num_Muon_loose_sel",var = "Muon_phi",bins=bins_eta,log=True)

    #?
    #main(den_folder="All_Muon",num_folder="num_Muon",var = "Muon_pt",bins=bins_met)

    #main(den_folder="All_Muon_tight_sel",num_folder="num_Muon_tight_sel",var = "Muon_pt",bins=bins_met)
    #main(den_folder="All_Muon_tight_sel",num_folder="num_Muon_tight_sel",var = "Muon_eta",bins=bins_eta,log=True)
    #main(den_folder="All_Muon_tight_sel",num_folder="num_Muon_tight_sel",var = "Muon_phi",bins=bins_eta,log=True)

    #main(den_folder="1T_Muon_tight_sel",num_folder="num1T_Muon_tight_sel",var = "Muon_pt",bins=bins_met)
    #main(den_folder="1T_Muon_tight_sel",num_folder="num1T_Muon_tight_sel",var = "Muon_eta",bins=bins_eta,log=True)
    #main(den_folder="1T_Muon_tight_sel",num_folder="num1T_Muon_tight_sel",var = "Muon_phi",bins=bins_eta,log=True)

    #main(den_folder="1L_Muon_loose_sel",num_folder="num1L_Muon_loose_sel",var = "Muon_pt",bins=bins_met)
    #main(den_folder="1L_Muon_loose_sel",num_folder="num1L_Muon_loose_sel",var = "Muon_eta",bins=bins_eta,log=True)
    #main(den_folder="1L_Muon_loose_sel",num_folder="num1L_Muon_loose_sel",var = "Muon_phi",bins=bins_eta,log=True)
