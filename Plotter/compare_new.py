### Example usage:
### 
### Compare histograms for different directories in different files
### python3 compare.py --input /eos/vbc/group/cms/ang.li/MLhists/MLNanoAODv2/stop_M600_588_ct200_2018_hist.root /eos/vbc/group/cms/ang.li/MLhists/MLNanoAODv2/stop_M600_580_ct2_2018_hist.root --dirs histtag histuntag  --nice 588 580 --scale --output /groups/hephy/cms/ang.li/plots/plots_test
###
### Compare histograms for the same directory in different files
### python3 compare.py --input /eos/vbc/group/cms/ang.li/MLhists/MLNanoAODv2/stop_M600_588_ct200_2018_hist.root /eos/vbc/group/cms/ang.li/MLhists/MLNanoAODv2/stop_M600_580_ct2_2018_hist.root --dirs histtag  --nice 588 580 --scale --output /groups/hephy/cms/ang.li/plots/plots_test
###
### Compare histograms for different directories in the same file
### python3 compare.py --input /eos/vbc/group/cms/ang.li/MLhists/MLNanoAODv2/stop_M600_588_ct200_2018_hist.root --dirs histtag histuntag  --nice tag untag --scale --output /groups/hephy/cms/ang.li/plots/plots_test


import os
import ROOT
import cmsstyle as CMS
import SoftDisplacedVertices.Samples.Samples as s
ROOT.EnableImplicitMT(4)
ROOT.gROOT.SetBatch(ROOT.kTRUE)
ROOT.TH1.SetDefaultSumw2(True)
ROOT.gStyle.SetOptStat(0)

import argparse

## This part copied from https://github.com/Ang-Li-95/cmssw-usercode/blob/UL/Tools/python/ROOTTools.py#L27C1-L37C34
class TH1EntriesProtector(object):
    """SetBinContent increments fEntries, making a hist's stats hard
    to understand afterward, as in e.g. move_above/below_into_bin
    calls. This saves and resets fEntries when done."""
    def __init__(self, h):
        self.h = h
    def __enter__(self):
        self.n = self.h.GetEntries()
    def __exit__(self, *args):
        self.h.ResetStats() # JMTBAD probably not necessary?
        self.h.SetEntries(self.n)

def move_below_into_bin(h,a):
    """Given the TH1 h, add the contents of the bins below the one
    corresponding to a into that bin, and zero the bins below."""
    assert(h.Class().GetName().startswith('TH1')) # i bet there's a better way to do this...
    with TH1EntriesProtector(h) as _:
        b = h.FindBin(a)
        bc = h.GetBinContent(b)
        bcv = h.GetBinError(b)**2
        for nb in range(0, b):
            bc += h.GetBinContent(nb)
            bcv += h.GetBinError(nb)**2
            h.SetBinContent(nb, 0)
            h.SetBinError(nb, 0)
        h.SetBinContent(b, bc)
        h.SetBinError(b, bcv**0.5)

def move_above_into_bin(h,a,minus_one=False):
    """Given the TH1 h, add the contents of the bins above the one
    corresponding to a into that bin, and zero the bins above."""
    assert(h.Class().GetName().startswith('TH1')) # i bet there's a better way to do this...
    with TH1EntriesProtector(h) as _:
        b = h.FindBin(a)
        if minus_one:
            b -= 1
        bc = h.GetBinContent(b)
        bcv = h.GetBinError(b)**2
        for nb in range(b+1, h.GetNbinsX()+2):
            bc += h.GetBinContent(nb)
            bcv += h.GetBinError(nb)**2
            h.SetBinContent(nb, 0)
            h.SetBinError(nb, 0)
        h.SetBinContent(b, bc)
        h.SetBinError(b, bcv**0.5)

def move_overflow_into_last_bin(h):
    """Given the TH1 h, Add the contents of the overflow bin into the
    last bin, and zero the overflow bin."""
    assert(h.Class().GetName().startswith('TH1')) # i bet there's a better way to do this...
    with TH1EntriesProtector(h) as _:
        nb = h.GetNbinsX()
        h.SetBinContent(nb, h.GetBinContent(nb) + h.GetBinContent(nb+1))
        h.SetBinError(nb, (h.GetBinError(nb)**2 + h.GetBinError(nb+1)**2)**0.5)
        h.SetBinContent(nb+1, 0)
        h.SetBinError(nb+1, 0)

def move_overflows_into_visible_bins(h, opt='under over'):
    """Combination of move_above/below_into_bin and
    move_overflow_into_last_bin, except automatic in the range. Have
    to already have SetRangeUser."""
    if not h.Class().GetName().startswith('TH1'):
      return
    if type(opt) != str:
        opt = 'under over' if opt else ''
    opt = opt.strip().lower()
    if 'under' in opt:
        move_below_into_bin(h, h.GetBinLowEdge(h.GetXaxis().GetFirst()))
    if 'over' in opt:
        move_above_into_bin(h, h.GetBinLowEdge(h.GetXaxis().GetLast()))

parser = argparse.ArgumentParser()
parser.add_argument('--input', type=str, nargs='+',
                    help='files to compare')
parser.add_argument('--output', type=str,
                    help='output dir')
parser.add_argument('--dirs', type=str, nargs='+',
                    help='directories to compare')
parser.add_argument('--nice', type=str, nargs='+',
                    help='legend names')
parser.add_argument('--scale', action='store_true', default=False,
                    help='Whether to scale the plot')
parser.add_argument('--commands', type=str, nargs='+',
                    help="Additional commands, such as rebinning or set range etc.")
parser.add_argument('--ratio', action='store_true', default=False,
                    help="Whether to plot the ratio")
parser.add_argument('--datamc', action='store_true', default=False,
                    help="Whether it is a data/MC comparision")
parser.add_argument('--cms', action='store_true', default=False,
                    help="Whether to use CMS style")

args = parser.parse_args()

colors_global = [ROOT.kBlue,ROOT.kRed+1,ROOT.kGreen+1,ROOT.kYellow+1,ROOT.kMagenta+1,ROOT.kCyan+1,ROOT.kOrange+1]

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

def h_command(h):
  if args.commands is None:
    return
  for c in args.commands:
    exec(c)
    return

def datamccomparison(name,data,mc,scale=False, ratio=True):
  c = ROOT.TCanvas("c"+name,"c"+name,600,600)
  l = ROOT.TLegend(0.6,0.7,0.9,0.9)
  move_overflows_into_visible_bins(data)
  move_overflows_into_visible_bins(mc)
  if scale and data.Integral()!=0 and mc.Integral()!=0:
    data.Scale(1./data.Integral())
    mc.Scale(1./mc.Integral())
  mc.SetLineColor(ROOT.kBlue)
  mc.SetFillColor(ROOT.kBlue-9)
  mc.SetFillStyle(1001)
  data.SetLineColor(ROOT.kBlack)
  data.SetMarkerStyle(20)
  data.SetMarkerSize(1.0)
  l.SetBorderSize(0)
  l.AddEntry(data, "data", "lep")
  l.AddEntry(mc, "background MC")

  if ratio and (('TH1' in str(type(data))) and ('TH1' in str(type(mc)))):
    rp = ROOT.TRatioPlot(data,mc)
    rp.SetH1DrawOpt("e")
    rp.SetH2DrawOpt("histE2")
    rp.GetLowYaxis().SetNdivisions(505)
    rp.Draw()
    rp.GetLowerRefYaxis().SetTitle("Data/MC")
    rp.GetLowerRefGraph().SetMarkerStyle(20)
    rp.GetLowerRefGraph().SetLineColor(1)
    rp.GetLowerRefGraph().SetMarkerColor(1)
    rp.GetUpperPad().cd()
    data.Draw("PE SAME")
    rp.GetUpperPad().SetLogy()
  else:
    mc.Draw("histE1")
    data.Draw("PE SAME")
    c.SetLogy()

  l.Draw()
  c.Update()
  #c.GetUpperPad().BuildLegend(x1=0.58,y1=0.8,x2=0.88,y2=1.0)
  c.SaveAs("{}.pdf".format(args.output+'/'+name))
  c.SaveAs("{}.png".format(args.output+'/'+name))

def comparehists_cms(name,hs,legend,colors=None,scale=False, ratio=False):
  if colors is None:
    colors = colors_global[:len(hs)]
  y_max = float('-inf')
  y_min = float("inf")
  y_min_log = float("inf")
  x_max = float('-inf')
  x_min = float("inf")
  x_label = ''
  y_label = ''
  for i in range(len(hs)):
    x_label = hs[i].GetXaxis().GetTitle()
    y_label = hs[i].GetYaxis().GetTitle()
    hs[i].SetName(legend[i])
    hs[i].SetLineWidth(2)
    hs[i].SetLineColor(colors[i])
    move_overflows_into_visible_bins(hs[i])
    if scale and hs[i].Integral()!=0:
      hs[i].Scale(1./hs[i].Integral())
    y_max = max(y_max,hs[i].GetMaximum())
    y_min_log = min(y_min_log,hs[i].GetMinimum(1e-08))
    y_min = min(y_min,hs[i].GetMinimum())
    x_max = max(x_max,hs[i].GetXaxis().GetXmax())
    x_min = min(x_min,hs[i].GetXaxis().GetXmin())

  CMS.SetExtraText("Simulation Preliminary")
  CMS.SetLumi("")
  canv = CMS.cmsCanvas(name, x_min, x_max, y_min, (y_max-y_min)/0.65+y_min, x_label, y_label, square = CMS.kSquare, extraSpace=0.01, iPos=0)
  leg = CMS.cmsLeg(0.2, 0.69, 0.99, 0.89, textSize=0.04,columns=2)
  for i in range(len(hs)):
      if not ('TH1' in str(type(hs[i]))):
        continue
      hs[i].DrawClone("same hist")
      leg.AddEntry(hs[i],legend[i])
  canv.Update()
  canv.SaveAs("{}.pdf".format(args.output+'/'+name))
  canv.SaveAs("{}.png".format(args.output+'/'+name))

def comparehists(name,hs,legend,colors=None,scale=False, ratio=False):
  if colors is None:
    colors = colors_global[:len(hs)]
  c = ROOT.TCanvas("c"+name,"c"+name,600,600)
  l = ROOT.TLegend(0.6,0.7,0.9,0.9)
  y_max = 0
  y_min = 1
  for i in range(len(hs)):
    hs[i].SetName(legend[i])
    hs[i].SetLineWidth(2)
    hs[i].SetLineColor(colors[i])
    move_overflows_into_visible_bins(hs[i])
    if scale and hs[i].Integral()!=0:
      hs[i].Scale(1./hs[i].Integral())
    y_max = max(y_max,hs[i].GetMaximum())
    #y_min = min(y_min,hs[i].GetBinContent(hs[i].GetMinimumBin()))
    y_min = min(y_min,hs[i].GetMinimum(1e-08))
    #y_min = max(1e03,y_min)

  if ratio and len(hs)==2 and (('TH1' in str(type(hs[0]))) and ('TH1' in str(type(hs[1])))):
    rp = ROOT.TRatioPlot(hs[0],hs[1])
    rp.GetLowYaxis().SetNdivisions(505)
    rp.Draw()

  else:
    for i in range(len(hs)):
      if i==0:
        hs[i].SetMaximum(10*y_max)
        #hs[i].SetMinimum(0.5*y_min)
        hs[i].DrawClone()
      else:
        hs[i].DrawClone("same")
      l.AddEntry(hs[i],legend[i])

  #l.Draw()
  c.Update()
  if ratio:
    c.GetUpperPad().SetLogy()
    c.GetUpperPad().BuildLegend(x1=0.58,y1=0.8,x2=0.88,y2=1.0)
  else:
    c.SetLogy()
    c.BuildLegend(x1=0.58,y1=0.8,x2=0.88,y2=1.0)

  c.Update()
  c.SaveAs("{}.pdf".format(args.output+'/'+name))
  c.SaveAs("{}.png".format(args.output+'/'+name))

def compareDiffFiles(fns,legend,colors,scale,ratio,datamc):
  fs = [ROOT.TFile.Open(fn) for fn in fns]
  dirs = []
  if (args.dirs is None) or (len(args.dirs)==0):
    dirs = ['']*len(fs)
    plots = [p.GetName() for p in fs[0].GetListOfKeys()]
  else:
    dirs = args.dirs
    if len(dirs)==1:
      dirs = [args.dirs[0]]*len(fs)
    fdir = fs[0].Get(args.dirs[0])
    if not fdir:
      print("{} not available in {}!".format(args.dirs[0],fs[0].GetName()))
    plots = [p.GetName() for p in fdir.GetListOfKeys()]
  
  assert(len(dirs)==len(fs))
  for plt in plots:
    h_compare = []
    for f,d in zip(fs,dirs):
      try:
        if d=='':
          h = f.Get(plt)
        else:
          h = f.Get(d+'/'+plt)
      except:
        print('{} is not available in {}!'.format(d+'/'+plt,f.GetName()))
        continue
      if not h:
        print('{} is not available in {}!'.format(d+'/'+plt,f.GetName()))
        continue
      h.SetDirectory(0)
      h_command(h)
      h_compare.append(h)
  
    if datamc:
      datamccomparison(plt,h_compare[0],h_compare[1],scale, ratio)
    else:
      comparehists_cms(plt,h_compare,legend=legend,colors=colors,scale=scale,ratio=ratio)
  
  for f in fs:
    f.Close()

def compareSameFile(fn,legend,colors,scale,ratio):
  f = ROOT.TFile.Open(fn)

  fdir = f.Get(args.dirs[0])
  if not fdir:
    print("{} not available in {}!".format(args.dirs[0],f.GetName()))
  plots = [p.GetName() for p in fdir.GetListOfKeys()]
  
  for plt in plots:
    h_compare = []
    for d in args.dirs:
      try:
        h = f.Get(d+'/'+plt)
      except:
        print('{} is not available in {}!'.format(d+'/'+plt,f.GetName()))
        continue
      if not h:
        print('{} is not available in {}!'.format(d+'/'+plt,f.GetName()))
        continue
      h.SetDirectory(0)
      h_command(h)
      h_compare.append(h)
  
    comparehists_cms(plt,h_compare,legend=legend,colors=colors,scale=scale,ratio=ratio)
  
  f.Close()

if __name__ == "__main__":
  if not os.path.exists(args.output):
    os.makedirs(args.output)
  if len(args.input)==1:
    assert(len(args.dirs)>1)
    compareSameFile(args.input[0],args.nice,None,args.scale,ratio=args.ratio)
  else:
    compareDiffFiles(args.input,args.nice,None,args.scale,ratio=args.ratio,datamc=args.datamc)

