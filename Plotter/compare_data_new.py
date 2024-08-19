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


import os,math
import ROOT
import cmsstyle as CMS
import SoftDisplacedVertices.Samples.Samples as s
ROOT.EnableImplicitMT(4)
ROOT.gROOT.SetBatch(ROOT.kTRUE)
ROOT.TH1.SetDefaultSumw2(True)
ROOT.gStyle.SetOptStat(0)
ROOT.TGaxis.SetExponentOffset(-0.10, 0.01, "Y")

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
parser.add_argument('--data', type=str, nargs='+',default=[],
                    help='data file to compare')
parser.add_argument('--bkg', type=str, nargs='+',default=[],
                    help='background files to compare')
parser.add_argument('--bkgnice', type=str, nargs='+',default=[],
                    help='background legend names')
parser.add_argument('--signal', type=str, nargs='+',default=[],
                    help='signal files to compare')
parser.add_argument('--signice', type=str, nargs='+',default=[],
                    help='signal legend names')
parser.add_argument('--output', type=str,
                    help='output dir')
parser.add_argument('--dirs', type=str, nargs='+',
                    help='directories to compare')
parser.add_argument('--scale', action='store_true', default=False,
                    help='Whether to scale the plot')
parser.add_argument('--commands', type=str, nargs='+',
                    help="Additional commands, such as rebinning or set range etc.")
parser.add_argument('--ratio', action='store_true', default=False,
                    help="Whether to plot the ratio")

args = parser.parse_args()

signal_colors = [ROOT.kGreen+1,ROOT.kRed+1,ROOT.kYellow+1,ROOT.kMagenta+1,ROOT.kCyan+1,ROOT.kOrange+1]
bkg_colors = [ROOT.kBlue-9, ROOT.kBlue-5, ROOT.kCyan-9]

def AddHists(hs,ws):
  assert len(hs)==len(ws)
  hnew = hs[0].Clone()
  for i in range(len(hs)):
    hs[i].Scale(ws[i])
    if i>0:
      hnew.Add(hs[i])
  return hnew

def StackHists(hs,ws):
  assert len(hs)==len(ws)
  h = ROOT.THStack("h","")
  for i in range(len(hs)):
    hs[i].Scale(ws[i])
    #hs[i].SetLineColor(i+1)
    #hs[i].SetFillColor(i+1)
    h.Add(hs[i])
  return h

def h_command(h):
  if args.commands is None:
    return
  for c in args.commands:
    exec(c)
    return

def comparehists_cms(name,hs,colors,legends,scale=False, ratio=True):
  if colors is None:
    colors = colors_global[:len(hs)]
  y_max = float('-inf')
  y_min = float("inf")
  y_min_log = float("inf")
  x_max = float('-inf')
  x_min = float("inf")
  x_label = ''
  y_label = ''
  d_bkg = {}
  for k in hs:
    for i in range(len(hs[k])):
      h = hs[k][i]
      move_overflows_into_visible_bins(h)
      h.GetYaxis().SetMaxDigits(2)
      if k=='bkg':
        d_bkg[legends[k][i]] = h
      elif k=='sig':
        h.SetLineColor(colors[k][i])
        h.SetLineWidth(2)
  data = None
  bkg_mc = None
  if len(hs['data'])>0:
    w =  [1]*len(hs['data'])
    data = AddHists(hs['data'],w)
  if len(hs['bkg'])>0:
    w = [1]*len(hs['bkg'])
    bkg_mc = AddHists(hs['bkg'],w)
  if scale and (data is not None and bkg_mc is not None) and bkg_mc.Integral()!=0:
    w = [data.Integral()/bkg_mc.Integral()]*len(hs['bkg'])
    w_value = data.Integral()/bkg_mc.Integral()
    bkg_mc.Scale(w_value)
    for h in d_bkg:
      d_bkg[h].Scale(w_value)

  hlist = []
  if data is not None:
    hlist.append(data)
  if bkg_mc is not None:
    hlist.append(bkg_mc)
  for h in hs['sig']:
    hlist.append(h)
  for h in hlist:
    x_label = h.GetXaxis().GetTitle()
    y_label = h.GetYaxis().GetTitle()
    #move_overflows_into_visible_bins(hs[i])
    y_max = max(y_max,h.GetMaximum())
    y_min_log = min(y_min_log,h.GetMinimum(1e-08))
    y_min = min(y_min,h.GetMinimum())
    x_max = max(x_max,h.GetXaxis().GetXmax())
    x_min = min(x_min,h.GetXaxis().GetXmin())

  if data is not None:
    CMS.SetExtraText("Preliminary")
  else:
    CMS.SetExtraText("Simulation Preliminary")
  CMS.SetLumi("")
  square=CMS.kSquare
  iPos=0
  
  ratio = ratio and (data is not None and bkg_mc is not None)
  if ratio:
    # Create canvas
    canv = CMS.cmsDiCanvas(name, x_min, x_max, y_min, (y_max-y_min)/0.65+y_min, 0, 2.5, x_label, y_label, "Data/MC", square=square, extraSpace=0.1, iPos=iPos,)
  else:
    canv = CMS.cmsCanvas(name, x_min, x_max, y_min, (y_max-y_min)/0.65+y_min, x_label, y_label, square = CMS.kSquare, extraSpace=0.01, iPos=0)

  leg = CMS.cmsLeg(0.2, 0.69, 0.99, 0.89, textSize=0.04,columns=2)
  if data is not None:
    leg.AddEntry(data, "Data", "pe")
  if bkg_mc is not None:
    stack = ROOT.THStack("stack", "Stacked")
    CMS.cmsDrawStack(stack, leg, d_bkg)
    h_err = bkg_mc.Clone("h_err")
    CMS.cmsDraw(h_err, "e2same0", lcolor = 335, lwidth = 1, msize = 0, fcolor = ROOT.kBlack, fstyle = 3004,) 
  if data is not None:
    CMS.cmsDraw(data, "E1X0", mcolor=ROOT.kBlack)

  for i in range(len(hs['sig'])):
    leg.AddEntry(hs['sig'][i], legends['sig'][i],"l")
    hs['sig'][i].Draw("hist same")

  if ratio:
    # Lower pad
    canv.cd(2)
    leg_ratio = CMS.cmsLeg(
        0.17, 0.97 - 0.05 * 5, 0.35, 0.97, textSize=0.05, columns=2
    )
    ratio = data.Clone("ratio")
    ratio.Divide(bkg_mc)
    for i in range(1,ratio.GetNbinsX()+1):
        if(ratio.GetBinContent(i)):
            ratio.SetBinError(i, math.sqrt(data.GetBinContent(i))/bkg_mc.GetBinContent(i))
        else:
            ratio.SetBinError(i, 10^(-99))
    yerr_root = ROOT.TGraphAsymmErrors()
    yerr_root.Divide(data, bkg_mc, 'pois') 
    for i in range(0,yerr_root.GetN()+1):
        yerr_root.SetPointY(i,1)
    CMS.cmsDraw(yerr_root, "e2same0", lwidth = 100, msize = 0, fcolor = ROOT.kBlack, fstyle = 3004)  
    CMS.cmsDraw(ratio, "E1X0", mcolor=ROOT.kBlack)
    ref_line = ROOT.TLine(x_min, 1, x_max, 1)
    CMS.cmsDrawLine(ref_line, lcolor=ROOT.kBlack, lstyle=ROOT.kDotted)

  canv.Update()
  CMS.SaveCanvas(canv,"{}.pdf".format(args.output+'/'+name),False)
  CMS.SaveCanvas(canv,"{}.png".format(args.output+'/'+name),False)
  #canv.SaveAs("{}.pdf".format(args.output+'/'+name))
  #canv.SaveAs("{}.png".format(args.output+'/'+name))

  if ratio:
    canv.cd(1)
  CMS.cmsCanvasResetAxes(ROOT.gPad, x_min, x_max, y_min_log, y_min_log*((y_max/y_min_log)**(1/0.65)))
  ROOT.gPad.SetLogy()
  canv.Update()
  CMS.SaveCanvas(canv,"{}_log.pdf".format(args.output+'/'+name),False)
  CMS.SaveCanvas(canv,"{}_log.png".format(args.output+'/'+name),True)

def datamccomparison(name,hs,colors,legends,scale=False, ratio=True):
  c = ROOT.TCanvas("c"+name,"c"+name,1000,800)
  l = ROOT.TLegend(0.72,0.7,1.0,0.9)
  for k in hs:
    for i in range(len(hs[k])):
      h = hs[k][i]
      move_overflows_into_visible_bins(h)
      if k=='data':
        h.SetLineColor(ROOT.kBlack)
        h.SetMarkerStyle(20)
        h.SetMarkerSize(0.8)
      elif k=='bkg':
        h.SetLineColor(ROOT.kBlue)
        h.SetFillColor(ROOT.kBlue-9)
        #h.SetFillStyle(1001)
        h.SetLineColor(colors[k][i])
        h.SetFillColor(colors[k][i])
      elif k=='sig':
        h.SetLineColor(colors[k][i])
        h.SetLineWidth(2)
  w =  [1]*len(hs['data'])
  data = AddHists(hs['data'],w)
  w = [1]*len(hs['bkg'])
  bkg_mc = AddHists(hs['bkg'],w)
  bkg_mc.SetLineColor(0)
  bkg_mc.SetFillColor(1)
  bkg_mc.SetFillStyle(3254)
  if scale and bkg_mc.Integral()!=0:
    w = [data.Integral()/bkg_mc.Integral()]*len(hs['bkg'])
    bkg_mc.Scale(data.Integral()/bkg_mc.Integral())
  bkg_stack = StackHists(hs['bkg'],w)
  l.SetBorderSize(0)
  l.AddEntry(data, "data", "lep")
  for k in ['bkg','sig']:
    for i in range(len(hs[k])):
      l.AddEntry(hs[k][i],legends[k][i])

  if ratio and (('TH1' in str(type(data))) and ('TH1' in str(type(bkg_mc)))):
    rp = ROOT.TRatioPlot(data,bkg_mc)
    rp.SetH1DrawOpt("e")
    rp.SetH2DrawOpt("E2")
    rp.GetLowYaxis().SetNdivisions(505)
    rp.SetRightMargin(0.3)
    rp.SetSeparationMargin(0.01)
    rp.Draw()
    #rmax = rp.GetLowerRefGraph().GetMaximum()
    #rp.GetLowerRefGraph().SetMinimum(0.85)
    rp.GetLowerRefGraph().SetMaximum(2.5)
    rp.GetLowerRefYaxis().SetTitle("Data/MC")
    rp.GetLowerRefGraph().SetMarkerStyle(20)
    rp.GetLowerRefGraph().SetLineColor(1)
    rp.GetLowerRefGraph().SetMarkerColor(1)
    rp.GetUpperPad().cd()
    bkg_stack.Draw("hist SAME")
    bkg_mc.Draw("E2 SAME")
    for i in range(len(hs['sig'])):
      hs['sig'][i].Draw("SAME histE1")
    data.Draw("PE SAME")
    rp.GetUpperPad().SetLogy()
  else:
    bkg_stack.Draw("hist")
    bkg_mc.Draw("SAME E2")
    for i in range(len(hs['sig'])):
      hs['sig'][i].Draw("SAME histE1")
    data.Draw("PE SAME")
    c.SetLogy()

  l.Draw()
  c.Update()
  #c.GetUpperPad().BuildLegend(x1=0.58,y1=0.8,x2=0.88,y2=1.0)
  c.SaveAs("{}.pdf".format(args.output+'/'+name))
  c.SaveAs("{}.png".format(args.output+'/'+name))

def comparehists(name,hs,legend,colors=None,scale=False, ratio=False):
  if colors is None:
    colors = colors_global[:len(hs)]
  c = ROOT.TCanvas("c"+name,"c"+name,600,600)
  l = ROOT.TLegend(0.7,0.7,1.0,1.0)
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
    rp.SetSeparationMargin(0.01)
    #rp.SetRightMargin(0.4)
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
  c.GetUpperPad().SetLogy()
  c.GetUpperPad().BuildLegend(x1=0.58,y1=0.8,x2=0.88,y2=1.0)
  c.Update()
  c.SaveAs("{}.pdf".format(args.output+'/'+name))
  c.SaveAs("{}.png".format(args.output+'/'+name))

def makeplots(datafn, bkgfns, sigfns,bkglegend,siglegend,bkgcolors,sigcolors,scale,ratio):
  assert(len(bkgfns)==len(bkglegend))
  assert(len(sigfns)==len(siglegend))
  legends = {
      'bkg':bkglegend,
      'sig':siglegend,
      }
  colors = {
      'bkg':bkgcolors,
      'sig':sigcolors,
      }
  fs = {
      'data': [ROOT.TFile.Open(fn) for fn in datafn],
      'bkg': [ROOT.TFile.Open(fn) for fn in bkgfns],
      'sig': [ROOT.TFile.Open(fn) for fn in sigfns]
      }
  dirs = ''
  if (args.dirs is None) or (len(args.dirs)==0):
    dirs = ''
    plots = [p.GetName() for p in fs['data'][0].GetListOfKeys()]
  else:
    dirs = args.dirs[0]
    if len(fs['data'])>0:
      fdir = fs['data'][0].Get(dirs)
    elif len(fs['bkg'])>0:
      fdir = fs['bkg'][0].Get(dirs)
    else:
      fdir = fs['sig'][0].Get(dirs)
    if not fdir:
      print("{} not available in {}!".format(args.dirs[0],fs['data'][0].GetName()))
    plots = [p.GetName() for p in fdir.GetListOfKeys()]
  
  if not dirs=='':
    dirs += '/'
  for plt in plots:
    hs = {}
    doit = False
    for k in fs:
      if not (k in hs):
        hs[k] = []
      for f in fs[k]:
        h = f.Get(dirs+plt)
        if not h:
          print('{} is not available in {}!'.format(dirs+plt,f.GetName()))
          continue
        if not ('TH1' in str(type(h))):
          break
        h.SetDirectory(0)
        h_command(h)
        hs[k].append(h)
        doit = True
    #datamccomparison(plt,hs,colors,legends,scale=False, ratio=True)
    comparehists_cms(plt,hs,colors,legends,scale=False, ratio=ratio)
  
  for k in fs:
    for f in fs[k]:
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
  
    comparehists(plt,h_compare,legend=legend,colors=colors,scale=scale,ratio=ratio)
  
  f.Close()

if __name__ == "__main__":
  if not os.path.exists(args.output):
    os.makedirs(args.output)
  makeplots(args.data,args.bkg,args.signal,args.bkgnice,args.signice,bkg_colors,signal_colors,args.scale,ratio=args.ratio)


