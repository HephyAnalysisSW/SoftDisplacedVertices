import ROOT
import cmsstyle as CMS
from array import array
import ctypes
import numpy as np
import math
ROOT.gStyle.SetOptStat(0)
ROOT.TH1.SetDefaultSumw2(True)
ROOT.TGaxis.SetExponentOffset(-0.10, 0.01, "Y")

def write(font, size, x, y, text):
    w = ROOT.TLatex()
    w.SetNDC()
    w.SetTextFont(font)
    w.SetTextSize(size)
    w.DrawLatex(x, y, text)
    return w

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
    return h
  for c in args.commands:
    l_dict = {'h': h}
    exec(c, globals(), l_dict)
    h = l_dict['h']
  return h

def comparehists_cms(name,hs,colors,legends,sig_scale=[], scale_to_data=False, ratio=True, norm=False, text=None):
  assert not (scale_to_data and norm), "Cannot set scale_to_data and norm in the same time!"
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
      #h=h.Rebin(11, '', array('d', [0,1,2,3,4,5,6,7,9,11,14,20]))
      move_overflows_into_visible_bins(h)
      h.GetYaxis().SetMaxDigits(2)
      if k=='bkg':
        d_bkg[legends[k][i]] = h
      elif k=='sig':
        h.SetLineColor(colors[k][i])
        h.SetLineWidth(3)
        if len(sig_scale)>0:
          h.Scale(sig_scale[i])
  data = None
  bkg_mc = None
  if len(hs['data'])>0:
    w =  [1]*len(hs['data'])
    data = AddHists(hs['data'],w)
  if len(hs['bkg'])>0:
    w = [1]*len(hs['bkg'])
    bkg_mc = AddHists(hs['bkg'],w)
  if scale_to_data and (data is not None and bkg_mc is not None) and bkg_mc.Integral()!=0:
    w = [data.Integral(0,1000000)/bkg_mc.Integral(0,1000000)]*len(hs['bkg'])
    w_value = data.Integral(0,1000000)/bkg_mc.Integral(0,1000000)
    bkg_mc.Scale(w_value)
    for h in d_bkg:
      d_bkg[h].Scale(w_value)

  if norm:
    if data is not None and data.Integral(0,1000000)!=0:
      data.Scale(1.0/data.Integral(0,1000000))
    if bkg_mc is not None and bkg_mc.Integral(0,1000000)!=0:
      w_value = 1.0/bkg_mc.Integral(0,1000000)
      bkg_mc.Scale(w_value)
      for h in d_bkg:
        d_bkg[h].Scale(w_value)
    for h in hs['sig']:
      if h.Integral(0,1000000)!=0:
        h.Scale(1.0/h.Integral(0,1000000))

  hlist = []
  if data is not None:
    hlist.append(data)
  if bkg_mc is not None:
    hlist.append(bkg_mc)
    hlist.append(d_bkg[legends['bkg'][0]])
  for h in hs['sig']:
    hlist.append(h)
  for h in hlist:
    x_label = h.GetXaxis().GetTitle()
    y_label = h.GetYaxis().GetTitle()
    y_label = "Number of vertices"
    y_label = "Fraction of vertices"
    #move_overflows_into_visible_bins(hs[i])
    y_max = max(y_max,h.GetMaximum())
    y_min_log = min(y_min_log,h.GetMinimum(1e-08))
    y_min = min(y_min,h.GetMinimum())
    x_max = max(x_max,h.GetXaxis().GetBinUpEdge(h.GetXaxis().GetLast()))
    x_min = min(x_min,h.GetXaxis().GetBinLowEdge(h.GetXaxis().GetFirst()))

  if data is not None:
    CMS.SetExtraText("")
  else:
    CMS.SetExtraText("Simulation")
  CMS.SetLumi("100") # 2017+2018
  square=CMS.kSquare
  iPos=0
  
  ratio = ratio and (data is not None and bkg_mc is not None)
  if ratio:
    # Create canvas
    canv = CMS.cmsDiCanvas(name, x_min, x_max, y_min, (y_max-y_min)/0.65+y_min, 0.5, 1.5, x_label, y_label, "Data/Sim.", square=square, extraSpace=0.1, iPos=iPos,)
  else:
    canv = CMS.cmsCanvas(name, x_min, x_max, y_min, (y_max-y_min)/0.65+y_min, x_label, y_label, square = CMS.kSquare, extraSpace=0.01, iPos=0)
    
  if ratio:
      hf = canv.GetListOfPrimitives().FindObject(name+"_1").GetListOfPrimitives().FindObject("hframe")
      hf.GetXaxis().SetLabelSize(0.05)
      hf.GetXaxis().SetTitleSize(0.075)
      hf.GetXaxis().SetTitleOffset(1.2)
      hf.GetYaxis().SetLabelSize(0.05)
      hf.GetYaxis().SetTitleSize(0.05)
      hf.GetYaxis().SetTitleOffset(1.25)

      hf2 = canv.GetListOfPrimitives().FindObject(name+"_2").GetListOfPrimitives().FindObject("hframe")
      hf2.GetXaxis().SetLabelSize(0.095)
      hf2.GetXaxis().SetTitleSize(0.095)
      hf2.GetXaxis().SetTitleOffset(1.5)
      hf2.GetYaxis().SetLabelSize(0.095)
      hf2.GetYaxis().SetTitleSize(0.095)
      hf2.GetYaxis().SetTitleOffset(0.65)
  else:
      hf = canv.GetListOfPrimitives().FindObject("hframe")
      hf.GetXaxis().SetLabelSize(0.035)
      hf.GetXaxis().SetTitleSize(0.04)
      hf.GetXaxis().SetTitleOffset(1.2)
      hf.GetYaxis().SetLabelSize(0.035)
      hf.GetYaxis().SetTitleSize(0.04)
      hf.GetYaxis().SetTitleOffset(1.5)
  canv.Update()

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
    #for i in range(1,ratio.GetNbinsX()+1):
    #    if(ratio.GetBinContent(i)):
    #        ratio.SetBinError(i, math.sqrt(data.GetBinContent(i))/bkg_mc.GetBinContent(i))
    #    else:
    #        ratio.SetBinError(i, 10^(-99))
    #yerr_root = ROOT.TGraphAsymmErrors()
    #yerr_root.Divide(data, bkg_mc, 'pois')
    #for i in range(0,yerr_root.GetN()+1):
    #    yerr_root.SetPointY(i,1)
    #CMS.cmsDraw(yerr_root, "e2same0", lwidth = 100, msize = 0, fcolor = ROOT.kBlack, fstyle = 3004)  
    CMS.cmsDraw(ratio, "E1X0", mcolor=ROOT.kBlack)
    #CMS.cmsDraw(yerr_root, "E1X0", mcolor=ROOT.kBlack)
    ref_line = ROOT.TLine(x_min, 1, x_max, 1)
    CMS.cmsDrawLine(ref_line, lcolor=ROOT.kBlack, lstyle=ROOT.kDotted)
  
  if ratio:
    canv.cd(1)
  if text is not None:
    #write(42, 0.04, 0.6, 0.6, text)
    write(42, 0.035, 0.3, 0.68, text)
  CMS.cmsCanvasResetAxes(ROOT.gPad, x_min, x_max, y_min, (y_max-y_min)/0.65+y_min)
  canv.Update()
  CMS.SaveCanvas(canv,"{}.pdf".format(name),False)
  CMS.SaveCanvas(canv,"{}.png".format(name),False)
  #canv.SaveAs("{}.pdf".format(args.output+'/'+name))
  #canv.SaveAs("{}.png".format(args.output+'/'+name))

  if ratio:
    canv.cd(1)
  CMS.cmsCanvasResetAxes(ROOT.gPad, x_min, x_max, y_min_log, y_min_log*((y_max/y_min_log)**(1/0.65)))
  ROOT.gPad.SetLogy()
  canv.Update()
  CMS.SaveCanvas(canv,"{}_log.pdf".format(name),False)
  CMS.SaveCanvas(canv,"{}_log.png".format(name),True)

def bkgsub(h,xmin,xmax):
    fb = h.GetXaxis().FindBin(xmin)
    lb = max(fb,h.GetXaxis().FindBin(xmax)-1)
    print(fb,lb)
    hdy = h.ProjectionY(firstxbin=fb,lastxbin=lb)
    print("22")
    hdy = hdy.Rebin(2)
    print("33")
    fBkg = ROOT.TF1("fBkg", "((x<=0.47)+(x>=0.53))*([0]+[1]*x)", 0.44, 0.56)
    hdy.Fit(fBkg)
    print("fit")
    fBkg_full = ROOT.TF1("fBkg_full", "([0]+[1]*x)", 0.44, 0.56)
    fBkg_full.SetParameter(0,fBkg.GetParameter(0))
    fBkg_full.SetParameter(1,fBkg.GetParameter(1))
    hSignal = hdy.Clone()
    hSignal.Add(fBkg_full, -1)
    nvtx_err = ctypes.c_double()
    nvtx = hSignal.IntegralAndError(hSignal.FindBin(0.47)+1,hSignal.FindBin(0.53)-1,nvtx_err)
    return nvtx, nvtx_err.value

def hist_bkgsub(h):
    hnew = ROOT.TH1D(h.GetName()+'_bkgsub',";vertex L_{xy} (cm);Number of vertices",40,0,20)
    for i in range(0,hnew.GetNbinsX()+1):
        ixmin = hnew.GetBinLowEdge(i+1)
        ixmax = hnew.GetBinLowEdge(i+1)+hnew.GetBinWidth(i+1)
        print(i,ixmin,ixmax)
        inv, inverr = bkgsub(h,ixmin,ixmax)
        hnew.SetBinContent(i+1,inv)
        hnew.SetBinError(i+1,inverr)
    return hnew


plt = 'METgreater400_SDVSecVtx_K0tightpA02/SDVSecVtx_Lxy'
plt2d = "All_SDVSecVtx_K0fitpA02/SDVSecVtx_Lxy_vs_SDVSecVtx_mass_K0"
hdir = "/scratch-cbe/users/ang.li/SoftDV/Histos/Histos_k0_tight_fit/"
fns = {
    'data' : 'met{}_hist.root',
    'sim' : 'background_{}_hist.root',
}
hs = {
    2017: {},
    2018: {},
}
sfs = {
    2017: 1.119195982378275,
    2018: 1.02119269910735,
}
hadd = {}
for k in fns:
    h_toadd = []
    w_toadd = []
    for year in [2017,2018]:
        f = ROOT.TFile.Open(hdir+fns[k].format(year))
        h2d = f.Get(plt2d)
        print("1", h2d.GetEntries())
        print("2", h2d.ProjectionY(firstxbin=1,lastxbin=5))
        h = hist_bkgsub(h2d)
        print("2")
        h.SetTitle(";Vertex L_{xy} (cm);Number of {\rm K_{S}^{0}} candidate vertices")
        h.SetDirectory(0)
        hs[year][k] = h
        h_toadd.append(h)
        if k=='data':
            w_toadd.append(1)
        else:
            w_toadd.append(sfs[year])
    
    newh = AddHists(h_toadd,w_toadd)
    newh.SetDirectory(0)
    #newh=newh.Rebin(11, '', array('d', [0,1,2,3,4,5,6,7,9,11,14,20]))
    #newh = h_command(newh)
    hadd[k] = newh
    
h_plt = {
    'data': [],
    'bkg': [],
    'sig': []
}

h_plt['data'].append(hadd['data'])
for k in ['sim']:
    h_plt['bkg'].append(hadd[k])
    
legends = {
      'bkg':["Background simulation"],
      'sig':[],
      }

sigcolors = [ROOT.kGreen,ROOT.kRed,ROOT.kYellow+1,ROOT.kMagenta+1,ROOT.kCyan+1,ROOT.kOrange+1]
bkgcolors = [ROOT.kBlue-9, ROOT.kBlue-5, ROOT.kCyan-9]
colors = {
      'bkg':bkgcolors,
      'sig':sigcolors,
      }

comparehists_cms('SDVSecVtx_Lxy_finebin',h_plt,colors,legends)
