#!/usr/bin/env python3

import ROOT
import argparse
import os
import sys
import array
import cmsstyle as CMS
import numpy as np

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

var = "MET_pt_nomu"
#var = "Muon_pt_sel"
#var = "MET_pt_corr"

def main():
    args = parse_args()

    input_dir = args.inputs
    output_dir = args.outputs
    era = args.era
    lumi = args.lumi
    mc = args.mc
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

    # Collect ROOT files
    root_files = [
        os.path.join(input_dir, f)
        for f in os.listdir(input_dir)
        if f.endswith(".root")
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
        den_dir = f.Get("All_evt")
        if not den_dir:
            raise KeyError("Directory 'All_evt' not found in ROOT file")

        # Get histogram "X"
        hden = den_dir.Get(var)
        if not hden:
            raise KeyError("Histogram '"+var+"' not found in directory 'All_evt'")

        # Type check
        if not hden.InheritsFrom("TH1D"):
            raise TypeError(
                f"Object 'All_evt/'"+var+" exists but is not a TH1D (found {hden.ClassName()})"
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
        num_dir = f.Get("num_evt")
        if not num_dir:
            raise KeyError("Directory 'num_evt' not found in ROOT file")

        # Get histogram "X"
        hnum = num_dir.Get(var)
        if not hnum:
            raise KeyError("Histogram '"+var+"' not found in directory 'num_evt'")

        # Type check
        if not hnum.InheritsFrom("TH1D"):
            raise TypeError(
                f"Object 'num_evt/"+var+"' exists but is not a TH1D (found {hnum.ClassName()})"
            )

        # Detach from file so it survives file closing
        hnum.SetDirectory(0)

        if tot_num is None:
            tot_num = hnum.Clone("tot_num")
            tot_num.Reset()
            tot_num.SetDirectory(0)  # detach from file

        tot_num.Add(hnum)


        f.Close()


    bins = array.array(
        'd',
        [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200, 210, 220, 240, 250, 260, 280, 300, 500, 1000]
    )

    bins = array.array(
        'd',
        [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200, 210, 220, 240, 250, 260, 280, 300, 400, 500, 700, 1000]
    )

    #bins = np.linspace(0,1000,50)

    num_rb = tot_num.Rebin(len(bins)-1, "num_rb", bins)
    den_rb = tot_den.Rebin(len(bins)-1, "den_rb", bins)

    num_rb.SetDirectory(0)
    den_rb.SetDirectory(0)

    #clipping for numerical precision
    eps = 1e-9

    for i in range(1, num_rb.GetNbinsX()+1):
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



    x95 = find_x_at_efficiency(eff,0.95)
    x99 = find_x_at_efficiency(eff,0.99)
    

    print(x95, x99)
    
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
    eff.GetPaintedGraph().GetYaxis().SetRangeUser(0.0, 1.05)

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
    latex.DrawLatex(0.65, 0.94, "%.1f fb^{-1} (13.6 TeV)"%float(lumi))
    
    c.SaveAs(output_dir+"efficiency_"+tag+era+".png")
    c.SaveAs(output_dir+"efficiency_"+tag+era+".pdf")
    
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
    
if __name__ == "__main__":
    main()
