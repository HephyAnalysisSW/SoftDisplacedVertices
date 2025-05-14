import sys
import ROOT

ROOT.gROOT.SetBatch(True)
f = ROOT.TFile.Open(sys.argv[1])
dir_path, hist_name = sys.argv[2].rsplit('/', 1)
f.cd(dir_path)
h = ROOT.gDirectory.Get(hist_name)
h.GetXaxis().SetRangeUser(-3, 3)
ROOT.gStyle.SetPalette(ROOT.kRainBow)
c = ROOT.TCanvas('c','',1300,1200)
c.SetRightMargin(0.15)
h.Draw('COLZ')
c.SaveAs(f'{hist_name}.png')
# palettes = [1,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,96,97,98,99,100,101,102,103,104,105,106,107,108,109,110,111,112,113]
# for pal in palettes:
#     ROOT.gStyle.SetPalette(pal)
#     h.Draw('COLZ')
#     c.SaveAs(f'{hist_name}_pal{pal}.png')
f.Close()
