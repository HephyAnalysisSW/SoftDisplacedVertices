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

def main(eras_list):
    #args = parse_args()

    input_dir = "/groups/hephy/cms/lisa.benato/SDV/trigger_efficiency_v2/merged/"
    output_dir = "/groups/hephy/cms/lisa.benato/SDV/trigger_efficiency_v2/merged/"
    tag = ""
        
    if not os.path.isdir(input_dir):
        print(f"ERROR: Input directory '{input_dir}' does not exist")
        sys.exit(1)

    # Collect ROOT files
    ratio_dict = {}
    for era in eras_list:
        # Check if current directory path contains "era"
        fn = input_dir+"ratio_"+era+".root"
        if os.path.isfile(fn): 
            f = ROOT.TFile.Open(fn, "READ")
            if not f or f.IsZombie():
                raise RuntimeError(f"Could not open ROOT file: {input_file}")
            ratio_dict[era] = f.Get("ratio")
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

    
    c = ROOT.TCanvas("c", "Efficiency", 800, 700)
    c.cd()
    c.SetTicks(1, 1)
    c.SetGrid()

    leg = ROOT.TLegend(0.50, 0.20, 0.88, 0.35)
    leg.SetBorderSize(0)
    leg.SetFillStyle(0)
    leg.SetTextSize(0.04)

    
    for i,era in enumerate(eras_list):
        print(i,era,ratio_dict[era])
        if i==0:
            ratio_dict[era].Draw("AL")
        else:
            ratio_dict[era].Draw("L,sames")
        ratio_dict[era].GetXaxis().SetTitleSize(0.045)
        ratio_dict[era].GetYaxis().SetTitleSize(0.045)
        ratio_dict[era].GetXaxis().SetLabelSize(0.045)
        ratio_dict[era].GetYaxis().SetLabelSize(0.045)
        ratio_dict[era].GetYaxis().SetRangeUser(0.5, 1.05)
        ratio_dict[era].SetMarkerColor(colors[i])
        ratio_dict[era].SetMarkerSize(0.0001)
        ratio_dict[era].SetMarkerStyle(21)
        ratio_dict[era].SetLineColor(colors[i])
        ratio_dict[era].SetLineWidth(2)
        leg.AddEntry(ratio_dict[era], era, "PLE")

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

    
    c.SaveAs(output_dir+"ratio_combined.png")
    c.SaveAs(output_dir+"ratio_combined.pdf")
    
    
if __name__ == "__main__":
    main(["2022pre","2022post","2023pre","2023post"])
