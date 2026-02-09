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

def main():
    args = parse_args()

    input_dir = args.inputs
    output_dir = args.outputs
    era = args.era
    lumi = args.lumi
    mc = args.mc
    tag = ""
    
    #if mc:
    #    tag = "WJetsToLNu"
    #else:
    #    tag = "SingleMuon"
    
    if not os.path.isdir(input_dir):
        print(f"ERROR: Input directory '{input_dir}' does not exist")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)

    output_file = os.path.join(output_dir, "efficiency"+tag+era+".root")

    # Collect ROOT files
    root_files = []
    data_files = []
    mc_files = []
    for root, dirs, files in os.walk(input_dir):
        # Check if current directory path contains "era"
        if era in root:
            for f in files:
                if f.endswith(".root"):
                    print(f)
                    if "SingleMuon" in f:
                        data_files.append(os.path.join(root, f))
                    else:
                        mc_files.append(os.path.join(root, f))

    if len(mc_files)+len(data_files) == 0:
        print("ERROR: No ROOT files found in input directory")
        sys.exit(1)

    print(f"Found {len(data_files)} data ROOT files")
    print(data_files)

    print(f"Found {len(mc_files)} mc ROOT files")
    print(mc_files)

    tot_den_mc = None
    tot_num_mc = None
    tot_den_data = None
    tot_num_data = None

    #mc
    for fn in mc_files:
        print(fn)
        f = ROOT.TFile.Open(fn, "READ")
        if not f or f.IsZombie():
            raise RuntimeError(f"Could not open ROOT file: {input_file}")

        ##### denominator
        
        # Get histogram "X"
        hden_mc = f.Get("tot_den")
        if not hden_mc:
            raise KeyError("Histogram 'tot_den' not found")

        # Type check
        if not hden_mc.InheritsFrom("TH1D"):
            raise TypeError(
                f"Object 'tot_den' exists but is not a TH1D (found {tot_den.ClassName()})"
            )

        # Detach from file so it survives file closing
        hden_mc.SetDirectory(0)

        if tot_den_mc is None:
            tot_den_mc = hden_mc.Clone("tot_den_mc")
            tot_den_mc.Reset()
            tot_den_mc.SetDirectory(0)  # detach from file

        tot_den_mc.Add(hden_mc)

        ##### numerator
        
        # Get histogram "X"
        hnum_mc = f.Get("tot_num")
        if not hnum_mc:
            raise KeyError("Histogram 'tot_num' not found")

        # Type check
        if not hnum_mc.InheritsFrom("TH1D"):
            raise TypeError(
                f"Object 'tot_num' exists but is not a TH1D (found {tot_num.ClassName()})"
            )

        # Detach from file so it survives file closing
        hnum_mc.SetDirectory(0)

        if tot_num_mc is None:
            tot_num_mc = hnum_mc.Clone("tot_num_mc")
            tot_num_mc.Reset()
            tot_num_mc.SetDirectory(0)  # detach from file

        tot_num_mc.Add(hnum_mc)


        f.Close()


    #data
    for fn in data_files:
        print(fn)
        f = ROOT.TFile.Open(fn, "READ")
        if not f or f.IsZombie():
            raise RuntimeError(f"Could not open ROOT file: {input_file}")

        ##### denominator
        
        # Get histogram "X"
        hden_data = f.Get("tot_den")
        if not hden_data:
            raise KeyError("Histogram 'tot_den' not found")

        # Type check
        if not hden_data.InheritsFrom("TH1D"):
            raise TypeError(
                f"Object 'tot_den' exists but is not a TH1D (found {tot_den.ClassName()})"
            )

        # Detach from file so it survives file closing
        hden_data.SetDirectory(0)

        if tot_den_data is None:
            tot_den_data = hden_data.Clone("tot_den_data")
            tot_den_data.Reset()
            tot_den_data.SetDirectory(0)  # detach from file

        tot_den_data.Add(hden_data)

        ##### numerator
        
        # Get histogram "X"
        hnum_data = f.Get("tot_num")
        if not hnum_data:
            raise KeyError("Histogram 'tot_num' not found")

        # Type check
        if not hnum_data.InheritsFrom("TH1D"):
            raise TypeError(
                f"Object 'tot_num' exists but is not a TH1D (found {tot_num.ClassName()})"
            )

        # Detach from file so it survives file closing
        hnum_data.SetDirectory(0)

        if tot_num_data is None:
            tot_num_data = hnum_data.Clone("tot_num_data")
            tot_num_data.Reset()
            tot_num_data.SetDirectory(0)  # detach from file

        tot_num_data.Add(hnum_data)


        f.Close()


    bins = array.array(
        'd',
        [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200, 210, 220, 240, 250, 260, 280, 300, 500, 1000]
    )

    bins = array.array(
        'd',
        [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200, 210, 220, 240, 250, 260, 280, 300, 400, 500, 700, 1000]
    )

    #Less bins?
    #bins = array.array(
    #    'd',
    #    [150, 160, 170, 180, 190, 200, 210, 220, 240, 250, 260, 280, 300, 400, 500, 700, 1000]
    #)

    
    #bins = np.linspace(0,1000,50)

    num_mc_rb = tot_num_mc.Rebin(len(bins)-1, "num_mc_rb", bins)
    den_mc_rb = tot_den_mc.Rebin(len(bins)-1, "den_mc_rb", bins)

    num_mc_rb.SetDirectory(0)
    den_mc_rb.SetDirectory(0)

    num_data_rb = tot_num_data.Rebin(len(bins)-1, "num_data_rb", bins)
    den_data_rb = tot_den_data.Rebin(len(bins)-1, "den_data_rb", bins)

    num_data_rb.SetDirectory(0)
    den_data_rb.SetDirectory(0)

        
    # Safety check
    if not ROOT.TEfficiency.CheckConsistency(num_mc_rb, den_mc_rb):
        raise RuntimeError("Numerator and denominator histograms are inconsistent")
    # Safety check
    if not ROOT.TEfficiency.CheckConsistency(num_data_rb, den_data_rb):
        raise RuntimeError("Numerator and denominator histograms are inconsistent")

    eff_mc = ROOT.TEfficiency(num_mc_rb, den_mc_rb)
    eff_data = ROOT.TEfficiency(num_data_rb, den_data_rb)

    # Optional: choose uncertainty type
    eff_mc.SetStatisticOption(ROOT.TEfficiency.kFCP)  # Clopper-Pearson (default)
    eff_mc.SetConfidenceLevel(0.683)
    # eff.SetStatisticOption(ROOT.TEfficiency.kFNormal)  # Gaussian
    # eff.SetStatisticOption(ROOT.TEfficiency.kFWilson)
    # eff.SetStatisticOption(ROOT.TEfficiency.kFAC)

    eff_mc.SetName("efficiency_mc")
    eff_mc.SetTitle(";E_{T}^{miss} (no #mu) [GeV];Efficiency L1+HLT")

    eff_mc.SetMarkerStyle(0)#(21)
    eff_mc.SetMarkerSize(0)#1.2)
    eff_mc.SetMarkerColor(634)#(ROOT.kBlack)

    eff_mc.SetLineColor(634)#(ROOT.kBlack)
    eff_mc.SetLineWidth(2)

    x95_mc = find_x_at_efficiency(eff_mc,0.95)
    x99_mc = find_x_at_efficiency(eff_mc,0.99)
    

    print(x95_mc, x99_mc)

    
    # Optional: choose uncertainty type
    eff_data.SetStatisticOption(ROOT.TEfficiency.kFCP)  # Clopper-Pearson (default)
    eff_data.SetConfidenceLevel(0.683)
    # eff.SetStatisticOption(ROOT.TEfficiency.kFNormal)  # Gaussian
    # eff.SetStatisticOption(ROOT.TEfficiency.kFWilson)
    # eff.SetStatisticOption(ROOT.TEfficiency.kFAC)

    eff_data.SetName("efficiency_data")
    eff_data.SetTitle(";E_{T}^{miss} (no #mu) [GeV];Efficiency L1+HLT")

    eff_data.SetMarkerStyle(20)
    eff_data.SetMarkerSize(1.2)
    eff_data.SetMarkerColor(1)#(ROOT.kBlack)

    eff_data.SetLineColor(1)#(ROOT.kBlack)
    eff_data.SetLineWidth(1)

    x95_data = find_x_at_efficiency(eff_data,0.95)
    x99_data = find_x_at_efficiency(eff_data,0.99)
    

    print(x95_data, x99_data)
    
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



    
    # Write merged output
    fout = ROOT.TFile(output_file, "RECREATE")
    fout.cd()
    tot_den_mc.Write()
    tot_num_mc.Write()
    eff_mc.Write()
    tot_den_data.Write()
    tot_num_data.Write()
    eff_data.Write()
    #gr.Write()
    fout.Close()


    c = ROOT.TCanvas("c", "Efficiency", 800, 700)

    pad1 = ROOT.TPad("pad1", "top pad", 0, 0.30, 1, 1.0)
    pad2 = ROOT.TPad("pad2", "bottom pad", 0, 0.0, 1, 0.30)

    pad1.SetBottomMargin(0.02)
    pad2.SetTopMargin(0.05)
    pad2.SetBottomMargin(0.30)

    pad1.Draw()
    pad2.Draw()

    pad1.cd()
    pad1.SetTicks(1, 1)
    pad1.SetGrid()

    eff_mc.Draw("AL")
    eff_data.Draw("P,sames")

    if x95_mc is not None:
        line95_mc = ROOT.TLine(x95_mc, 0, x95_mc, 1)
        line95_mc.SetLineColor(634)
        line95_mc.SetLineStyle(2)
        line95_mc.SetLineWidth(2)
        line95_mc.Draw("same")

        latex95_mc = ROOT.TLatex()
        latex95_mc.SetTextColor(634)
        latex95_mc.SetTextSize(0.035)
        latex95_mc.SetTextAlign(21)  # center horizontally, bottom vertically
        latex95_mc.SetTextAngle(90)   # rotate text 90 degrees
        latex95_mc.DrawLatex(x95_mc, 0.65, f"MC 95% @ {x95_mc:.0f} GeV")

    if x99_mc is not None:
        line99_mc = ROOT.TLine(x99_mc, 0, x99_mc, 1)
        line99_mc.SetLineColor(634)
        line99_mc.SetLineStyle(2)
        line99_mc.SetLineWidth(2)
        #line99_mc.Draw("same")

        latex99_mc = ROOT.TLatex()
        latex99_mc.SetTextColor(634)
        latex99_mc.SetTextSize(0.035)
        latex99_mc.SetTextAlign(21)  # center horizontally, bottom vertically
        latex99_mc.SetTextAngle(90)   # rotate text 90 degrees
        #latex99_mc.DrawLatex(x99_mc, 0.65, f"MC 99% @ {x99_mc:.0f} GeV")

    if x95_data is not None:
        line95_data = ROOT.TLine(x95_data, 0, x95_data, 1)
        line95_data.SetLineColor(1)
        line95_data.SetLineStyle(2)
        line95_data.SetLineWidth(2)
        line95_data.Draw("same")

        latex95_data = ROOT.TLatex()
        latex95_data.SetTextColor(1)
        latex95_data.SetTextSize(0.035)
        latex95_data.SetTextAlign(21)  # center horizontally, bottom vertically
        latex95_data.SetTextAngle(90)   # rotate text 90 degrees
        latex95_data.DrawLatex(x95_data, 0.65, f"DATA 95% @ {x95_data:.0f} GeV")

    if x99_data is not None:
        line99_data = ROOT.TLine(x99_data, 0, x99_data, 1)
        line99_data.SetLineColor(634)
        line99_data.SetLineStyle(2)
        line99_data.SetLineWidth(2)
        #line99_data.Draw("same")

        latex99_data = ROOT.TLatex()
        latex99_data.SetTextColor(634)
        latex99_data.SetTextSize(0.035)
        latex99_data.SetTextAlign(21)  # center horizontally, bottom vertically
        latex99_data.SetTextAngle(90)   # rotate text 90 degrees
        #latex99_data.DrawLatex(x99_data, 0.65, f"DATA 99% @ {x99_data:.0f} GeV")

        
    ROOT.gPad.Update()
    
    eff_mc.GetPaintedGraph().GetXaxis().SetTitleSize(0.045)
    eff_mc.GetPaintedGraph().GetYaxis().SetTitleSize(0.045)
    eff_mc.GetPaintedGraph().GetYaxis().SetRangeUser(0.0, 1.05)
    eff_data.GetPaintedGraph().GetXaxis().SetTitleSize(0.045)
    eff_data.GetPaintedGraph().GetYaxis().SetTitleSize(0.045)
    eff_data.GetPaintedGraph().GetYaxis().SetRangeUser(0.0, 1.05)

    
    leg = ROOT.TLegend(0.50, 0.20, 0.88, 0.35)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0)
    leg.SetTextSize(0.04)
    leg.AddEntry(eff_mc, "MC WJetsToLNu "+str(era), "PLE")
    leg.AddEntry(eff_data, "DATA SingleMuon "+str(era), "PE")
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

    pad1.Update()  # Important so graphs exist
    g_mc = eff_mc.GetPaintedGraph()
    g_data = eff_data.GetPaintedGraph()

    g_mc.GetXaxis().SetLabelSize(0)   # removes numbers
    g_mc.GetXaxis().SetTitleSize(0)   # removes axis title
    g_mc.GetXaxis().SetTickLength(0)  # optional: removes tick marks
    g_data.GetXaxis().SetLabelSize(0)   # removes numbers
    g_data.GetXaxis().SetTitleSize(0)   # removes axis title
    #g_data.GetXaxis().SetTickLength(0)  # optional: removes tick marks
    ratio = ROOT.TGraphAsymmErrors(g_mc.GetN())

    for i in range(g_mc.GetN()):

        x = g_mc.GetPointX(i)
        y_mc = g_mc.GetPointY(i)
        y_data = g_data.GetPointY(i)

        if y_mc > 0:
            r = y_data / y_mc
            ratio.SetPoint(i, x, r)

            # Propagate asymmetric errors approximately
            err_mc_up = g_mc.GetErrorYhigh(i)
            err_mc_dn = g_mc.GetErrorYlow(i)
            err_data_up = g_data.GetErrorYhigh(i)
            err_data_dn = g_data.GetErrorYlow(i)

            err_up = r * ((err_data_up/y_data)**2 + (err_mc_dn/y_mc)**2)**0.5
            err_dn = r * ((err_data_dn/y_data)**2 + (err_mc_up/y_mc)**2)**0.5

            ratio.SetPointError(i,
                                g_mc.GetErrorXlow(i),
                                g_mc.GetErrorXhigh(i),
                                err_dn,
                                err_up)

    
    #for i in range(g_mc.GetN()):
    #    x = ROOT.Double()
    pad2.cd()
    pad2.SetGrid()
    pad2.SetTicks(1, 1)

    ratio.SetTitle("")
    ratio.GetYaxis().SetTitle("Data / MC")
    ratio.GetXaxis().SetTitle(eff_mc.GetPaintedGraph().GetXaxis().GetTitle())

    ratio.GetYaxis().SetNdivisions(505)
    ratio.GetYaxis().SetTitleSize(0.10)
    ratio.GetYaxis().SetTitleOffset(0.45)
    ratio.GetYaxis().SetLabelSize(0.08)

    ratio.GetXaxis().SetTitleSize(0.12)
    ratio.GetXaxis().SetLabelSize(0.10)

    ratio.SetMarkerStyle(21)
    ratio.SetMarkerSize(1.)
    ratio.SetLineWidth(1)
    ratio.SetMarkerColor(4)
    ratio.SetLineColor(4)
    ratio.Draw("AP")

    xeff = find_first_unity_crossing(ratio)
    if xeff==None:
        xeff = 0
    line = ROOT.TLine(xeff, 0, xeff,1)
    line.SetLineColor(2)
    line.SetLineStyle(2)
    line.SetLineWidth(2)
    #line.Draw("same")

    latex = ROOT.TLatex()
    latex.SetTextColor(2)
    latex.SetTextSize(0.035)
    latex.SetTextAlign(21)  # center horizontally, bottom vertically
    latex.SetTextAngle(90)   # rotate text 90 degrees
    #latex.DrawLatex(xeff, 0.65, f"r=1 @ {xeff:.0f} GeV")


    #line = ROOT.TLine(
    #    ratio.GetXaxis().GetXmin(), 1.0,
    #    ratio.GetXaxis().GetXmax(), 1.0
    #)
    #line.SetLineStyle(2)
    #line.Draw()
    
    c.SaveAs(output_dir+"efficiency_"+era+".png")
    c.SaveAs(output_dir+"efficiency_"+era+".pdf")
    
    print(f"Output written to: {output_file}")

    fout = ROOT.TFile(output_dir+"ratio_"+era+".root", "RECREATE")
    fout.cd()
    ratio.Write("ratio")
    fout.Close()



    
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
