#!/usr/bin/env python

import os, sys, re, csv
import ROOT
import cmsstyle as CMS
from array import array
import SoftDisplacedVertices.Samples.Samples as sps
ROOT.gROOT.SetBatch(ROOT.kTRUE)

def drawText (text, posX, posY, font, align, size):
    """This method allows to draw a given text with all the provided characteristics.

    Args:
        text (str): text to be written in the Current TPad/TCanvas.
        posX (float): position in X (using NDC) where to place the text.
        posY (float): poisition in Y (using NDC) where to place the text.
        font (Font_t): Font to be used.
        align (int): Alignment code for the text.
        size (float): Size of the text.
    """
    latex = ROOT.TLatex()
    latex.SetNDC()
    latex.SetTextAngle(0)
    latex.SetTextColor(ROOT.kBlack)

    latex.SetTextFont(font)
    latex.SetTextAlign(align)
    latex.SetTextSize(size)
    latex.DrawLatex(posX, posY, text)


def draw_lumi(pad, iPosX=11, scaleLumi=1):
    """
    Draw the CMS text and luminosity information on the specified pad.

    Args:
        pad (ROOT.TPad): The pad to draw on.
        iPosX (int, optional): The position of the CMS logo. Defaults to 11 (top-left, left-aligned).
                               Set it to 0 to put it outside the box (top left)
        scaleLumi (float, optional): Scale factor for the luminosity text size (default is 1, no scaling).
    """
    CMS.SetLumi("100")
    CMS.SetEnergy("13")
    relPosX = 0.035
    relPosY = 0.035
    relExtraDY = 1.2
    outOfFrame = int(iPosX / 10) == 0
    alignX_ = max(int(iPosX / 10), 1)
    alignY_ = 1 if iPosX == 0 else 3
    align_ = 10 * alignX_ + alignY_
    H = pad.GetWh() * pad.GetHNDC()
    W = pad.GetWw() * pad.GetWNDC()
    l = pad.GetLeftMargin()
    t = pad.GetTopMargin()
    r = pad.GetRightMargin()
    b = pad.GetBottomMargin()
    outOfFrame_posY = 1 - t + CMS.lumiTextOffset * t
    pad.cd()

    lumiText = CMS.cms_lumi
    if CMS.cms_energy != "":
        lumiText += " (" + CMS.cms_energy + ")"
    lumiText = '100 fb^{#minus1} (13 TeV)'

    drawText(
        text=lumiText,
        posX=1 - r,
        posY=outOfFrame_posY,
        font=42,
        align=31,
        size=CMS.lumiTextSize * t * scaleLumi,
    )
    
    CMS.UpdatePad(pad)


def getwidth(m,dm):
    # this calculated the 4-body partial decay width 
    # m is the LLP mass and dm is the mass splitting
    return (9*28*(1.98*1e-14)*((dm)/30)**8*(400/m))

def getctau(m,dm):
    # this calculates the mean proper length of the LLP
    # m is the LLP mass and dm is the mass splitting
    return 1.973269788e-13/getwidth(m,dm)

def getctauBR(m,dm,br):
    # this calculates the mean proper length of the LLP
    # m is the LLP mass and dm is the mass splitting
    width_4body = getwidth(m,dm)
    width_total = width_4body/br
    return 1.973269788e-13/width_total

def write(font, size, x, y, text):
    w = ROOT.TLatex()
    w.SetNDC()
    w.SetTextFont(font)
    w.SetTextSize(size)
    w.DrawLatex(x, y, text)
    return w

def tge(xye):
    x = array('f', [z[0] for z in xye])
    y = array('f', [z[1] for z in xye])
    ey = array('f', [z[2] for z in xye])
    ex = array('f', [0.001]*len(x))
    return ROOT.TGraphErrors(len(x), x, y, ex, ey)

def tgae(x, y, exl, exh, eyl, eyh):
    #print 'tgae', len(x), len(y)
    x = array('d', x)
    y = array('d', y)
    l = len(x)
    if exl is None:
        exl = [0]*l
    exl = array('d', exl)
    if exh is None:
        exh = [0]*l
    exh = array('d', exh)
    if eyl is None:
        eyl = [0]*l
    eyl = array('d', eyl)
    if eyh is None:
        eyh = [0]*l
    eyh = array('d', eyh)
    #print l, x, y, exl, exh, eyl, eyh
    if l==0:
      print("array length 0!!!")
    t = ROOT.TGraphAsymmErrors(l, x, y, exl, exh, eyl, eyh)
    return t

class limits:
    class point:
        res = (
            ('observed'  , re.compile('Observed Limit: r < (.*)')),
            ('expect2p5' , re.compile('Expected  2.5%: r < (.*)')),
            ('expect16'  , re.compile('Expected 16.0%: r < (.*)')),
            ('expect50'  , re.compile('Expected 50.0%: r < (.*)')),
            ('expect84'  , re.compile('Expected 84.0%: r < (.*)')),
            ('expect97p5', re.compile('Expected 97.5%: r < (.*)')),
            )

        def __init__(self, sample):
            self.sample = sample
            self.observed = self.expect2p5 = self.expect16 = self.expect50 = self.expect84 = self.expect97p5 = None

        @property
        def valid(self):
            return all(x is not None for x in (self.observed,self.expect2p5,self.expect16,self.expect50,self.expect84,self.expect97p5))

        @property
        def expect_valid(self):
            return all(x is not None for x in (self.expect2p5,self.expect16,self.expect50,self.expect84,self.expect97p5))

        @property
        def expect68(self):
            return (self.expect16 + self.expect84) / 2
        @property
        def expect95(self):
            return (self.expect2p5 + self.expect97p5) / 2
        @property
        def expect68lo(self):
            return self.expect68 - self.expect16
        @property
        def expect68hi(self):
            return self.expect84 - self.expect68
        @property
        def expect95lo(self):
            return self.expect95 - self.expect2p5
        @property
        def expect95hi(self):
            return self.expect97p5 - self.expect95

        def tryset(self, line):
            for a,r in self.res:
                mo = r.search(line)
                if mo:
                    x = float(mo.group(1))
                    x = x*self.sample.xsec*1000 #convert to fb, and take care of the signal sample xsec (event yield calculated using sample.xsec)
                    setattr(self, a, x)

    def __init__(self):
        self.points = []

    def parse(self, sample, fn):
        p = limits.point(sample)
        if os.path.isfile(fn):
            for line in open(fn):
                p.tryset(line)
            assert p.valid
            self.points.append(p)

    def __getitem__(self, key):
        if key == 'tau':
            return [p.sample.tau/1000. for p in self.points]
        elif key == 'mass':
            return [p.sample.mass for p in self.points]
        elif key == 'massLSP':
            return [p.sample.massLSP for p in self.points]
        else:
            return [getattr(p,key) for p in self.points]

def parse_theory(which, include_errors=True, cache={}):
    if which not in ('gluglu', 'stop', 'C1N2'):
        raise ValueError('bad which %r' % which)
    fn = which + '.csv'
    if not (fn in cache):
        xsecs = [eval(x.strip()) for x in open(fn) if x.strip()]
        xsecs = [(z[0], z[1]*1000, z[2]/100*z[1]*1000) for z in xsecs] # convert pb to fb and percent to absolute
        if not include_errors:
            xsecs = [(a,b,0.) for a,b,_ in xsecs]
        cache[fn] = xsecs
    return cache[fn]

def make_theory(which, include_errors=True, return_list=False):
    xsecs = parse_theory(which, include_errors)
    g = tge(xsecs)
    g.SetLineWidth(2)
    g.SetLineColor(9)
    if return_list:
        return g, xsecs
    else:
        return g

def make_1dplot(model):

  if model == 'stop':
    masses = [400,500,600,700,800,900,1000,1100,1200,1300,1400]
    dms = [25,20,15,12]
    BRorct = [0.1,0.5,1] # BR
    xlow = 350
    xhigh = 1450
    production_nice = "#kern[0.1]{#tilde{t}}#kern[0.1]{#tilde{t}}"
  elif model == 'C1N2':
    masses = [200,300,400,500,600]
    dms = [25,20,15,12]
    BRorct = [0.2,2,20,200] # ctau in mm
    xlow = 150
    xhigh = 650
    production_nice = "#kern[0.1]{#tilde{#chi}^{#pm}_{1}}#kern[0.1]{#tilde{#chi}^{0}_{2}}"
  else:
    raise Exception("Model {} not defined!".format(model))

  xkey='mass'
  gt = make_theory(model)
  if not os.path.exists(output):
    os.makedirs(output)
  for dm in dms:
    for ibc in BRorct:
      r = limits()
      for m in masses:
        stopct = {
            25: 0.2,
            20: 2,
            15: 20,
            12: 200,
            }
        if model=='stop':
          ct = stopct[dm]
          BR = ibc
          realctau = getctauBR(m,dm,BR)
          decay_nice = "#tilde{{t}} #rightarrow bff'#kern[0.2]{{#tilde{{#chi}}^{{0}}_{{1}}}} / c#kern[0.1]{{#tilde{{#chi}}^{{0}}_{{1}}}}, B(#tilde{{t}} #rightarrow bff'#kern[0.2]{{#tilde{{#chi}}^{{0}}_{{1}}}}) = {}".format(BR)
          params_nice = "#Deltam = {} GeV, c#tau = {:.3} mm".format(dm,realctau)
        elif model=='C1N2':
          ct = ibc
          BR = 1
          decay_nice = "#tilde{#chi}^{#pm}_{1} #rightarrow ff'#kern[0.2]{#tilde{#chi}^{0}_{1}}, #tilde{#chi}^{0}_{2} #rightarrow f#bar{f}#kern[0.1]{#tilde{#chi}^{0}_{1}}"
          params_nice = "#Deltam = {} GeV, c#tau = {} mm".format(dm,ct)
        ctstr = str(ct).replace('.','p')
        sample = getattr(sps,'{}_M{}_{}_ct{}_2018'.format(model,m,m-dm,ctstr))
        if model=='stop':
          fn = 'limit_{}_datacard.txt'.format(sample.name.replace("2018",'Run2').replace("ct{}".format(ctstr),"BR{}".format(BR)).replace('.','p'))
        elif model=='C1N2':
          fn = 'limit_{}_datacard.txt'.format(sample.name.replace("2018",'Run2'))
        result_path = os.path.join(path,fn)
        if os.path.exists(result_path):
          r.parse(sample,result_path)
        else:
          print ("File {} not opened.".format(result_path))

      observed = tgae(r[xkey], r['observed'], None, None, None, None)
      expect50 = tgae(r[xkey], r['expect50'], None, None, None, None)
      expect95 = tgae(r[xkey], r['expect95'], None, None, r['expect95lo'], r['expect95hi'])
      expect68 = tgae(r[xkey], r['expect68'], None, None, r['expect68lo'], r['expect68hi'])

      # Styling
      CMS.SetExtraText("Preliminary")
      iPos = 0
      canv_name = 'limitplot_root'
      CMS.SetLumi("100")
      CMS.SetEnergy("13")
      CMS.ResetAdditionalInfo()
      canv = CMS.cmsCanvas(canv_name,xlow,xhigh,0.1,1e+05,"LLP mass (GeV)","Upper limits on #sigma (fb)",square=CMS.kSquare,extraSpace=0.01,iPos=iPos)
      canv.GetListOfPrimitives()[1].SetLabelSize(0.045, "XYZ")
      canv.GetListOfPrimitives()[1].SetTitleSize(0.045, "XYZ")
      canv.GetListOfPrimitives()[1].SetTitleOffset(1.4, "XYZ")
      expect95.GetXaxis().SetLabelSize(0.25)
      CMS.cmsDraw(expect95, "3", fcolor = ROOT.TColor.GetColor("#F5BB54"))
      CMS.cmsDraw(expect68, "Same3", fcolor = ROOT.TColor.GetColor("#607641"))
      CMS.cmsDraw(expect50, "L", lwidth=2, lstyle=7)
      CMS.cmsDraw(observed, "L", lwidth=2)
      CMS.cmsDraw(gt, "L3Same", lwidth=2, lcolor=46, fcolor = 45, alpha=0.5)
      leg = CMS.cmsLeg(0.2, 0.90 - 0.05 * 3, 0.9, 0.90, textSize=0.04, columns=2)
      leg.AddEntry(0, '#kern[-0.22]{95% CL upper limits:}', '')
      leg.AddEntry(0, '', '')

      leg.AddEntry(observed, "Observed","L")
      leg.AddEntry(expect68, "68% expected","F")
      leg.AddEntry(expect50, "Median expected","L")
      leg.AddEntry(expect95, "95% expected","F")
      leg.AddEntry(gt, "{} production".format(production_nice),"LF")
      canv.SetLogy()
      sig_text         = write(42, 0.04, 0.20, 0.255, decay_nice)
      mass_or_tau_text = write(42, 0.04, 0.20, 0.200, params_nice)
      savestr = "BR{}".format(BR).replace(".",'p') if model=='stop'  else "ct{}".format(ctstr) 
      CMS.SaveCanvas(canv,os.path.join(output,'limit1d_mass_{}_dm{}_{}.pdf'.format(model,dm,savestr)),close=False)
      CMS.SaveCanvas(canv,os.path.join(output,'limit1d_mass_{}_dm{}_{}.root'.format(model,dm,savestr)),close=False)
      CMS.SaveCanvas(canv,os.path.join(output,'limit1d_mass_{}_dm{}_{}.png'.format(model,dm,savestr)))

def interpolate(h,x,y):
  #return h
  hnew = ROOT.TH2D(h.GetName()+'inter','',len(x)-1,x,len(y)-1,y)
  for m in x:
    m = m+0.5
    for iy in y:
        iy = iy + 0.5
        xbin = hnew.GetXaxis().FindBin(m)
        ybin = hnew.GetYaxis().FindBin(iy)
        hnew.SetBinContent(xbin,ybin,h.Interpolate(m,iy))
  return hnew

def make_theory_hist(which):
    xsecs = parse_theory(which)
    h = ROOT.TH1F('h_xsecs_%s' % which, '', 561, 200, 3005)
    for m,s,se in xsecs:
        bin = h.FindBin(m)
        h.SetBinContent(bin, s)
        h.SetBinError  (bin, se)
    return xsecs, h

def theory_exclude(which, h, opt, use_error):
    theory, htheory = make_theory_hist(which)
    theory = dict((m, (s, es)) for m, s, es in theory)
    max_mass = max(theory.keys())
    min_mass = min(theory.keys())

    hexc = h.Clone(h.GetName() + '_%s' % which +'_exc_%s' % opt)
    hexc.SetStats(0)

    for ix in range(1, h.GetNbinsX()+1):
        mass = h.GetXaxis().GetBinCenter(ix)
        if mass >= max_mass:
            for iy in range(1, h.GetNbinsY()+1):
                hexc.SetBinContent(ix,iy, 0)
            continue
        elif mass <= min_mass:
            # JMTBAD gluglu theory stopped going down so far since old limits exclude those, assume this is the only place this is hit and assume we are doing so much better
            for iy in range(1, h.GetNbinsY()+1):
                hexc.SetBinContent(ix,iy, 1)
            continue

        for iy in range(1, h.GetNbinsY()+1):
            tau = h.GetYaxis().GetBinCenter(iy)

            lim = h.GetBinContent(ix, iy)

            bin = htheory.FindBin(mass)
            assert 1 <= bin < htheory.GetNbinsX()
            ma = htheory.GetBinLowEdge(bin)
            mb = htheory.GetBinLowEdge(bin+1)
            sa, esa = theory[ma]
            sb, esb = theory[mb]

            z = (mass - ma) / (mb - ma)
            s = sa + (sb - sa) * z

            bin = hexc.FindBin(mass, tau)
            s2 = s
            if use_error:
                es = (z**2 * esb**2 + (1 - z)**2 * esa**2)**0.5
                if opt.lower() == 'up':
                    s2 += es
                elif opt.lower() == 'dn':
                    s2 -= es
            if lim < s2:
                hexc.SetBinContent(bin, 1)
            else:
                hexc.SetBinContent(bin, 0)
    return hexc

def exc_graph(h, color, style):
    xax = h.GetXaxis()
    yax = h.GetYaxis()
    xs,ys = array('d'), array('d')
    for iy in range(1, h.GetNbinsY()+1):
        y = yax.GetBinCenter(iy)
        xprev = None
        #for ix in range(h.GetNbinsX(), 0, -1):
        for ix in range(1, h.GetNbinsX(), 1):
            x = xax.GetBinCenter(ix)
            l = h.GetBinContent(ix, iy)
            if l:
                xprev = x 
            elif xprev is not None:
                xs.append(xprev)
                ys.append(y)
                break
    if len(xs)==0:
      print("no exclusion points added!")
      xs.append(0)
      ys.append(0)
    g = ROOT.TGraph(len(xs), xs, ys)
    g.SetTitle(';mass (GeV);lifetime (mm)')
    g.SetLineWidth(2)
    g.SetLineColor(color)
    g.SetLineStyle(style)
    return g

def make_2dplot():
  x = [600,1000,1400]
  y = [12,15,20,25]
  x_coarse = array('d',[400.0, 800.0, 1200.0, 1600.0])
  y_coarse = array('d',[11.5,12.5,17.5,22.5,27.5])
  x_fine = [i-25 for i in range(int(min(x)),int(max(x))+100,50)]
  y_fine = [i-0.5 for i in range(int(min(y)),int(max(y))+2,1)]
  x_fine = array('d',x_fine)
  y_fine = array('d',y_fine)

  limits_2d = {}
  limits_2d_interp = {}
  for l in 'observed expect2p5 expect16 expect50 expect68 expect84 expect95 expect97p5'.split():
    limits_2d[l] = ROOT.TH2D(l,'',len(x_coarse)-1,x_coarse,len(y_coarse)-1,y_coarse)
  gt = make_theory(model)
  r = limits()
  for dm,ct in zip([25,20,15,12],['0p2','2','20','200']):
    for m in [600,1000,1400]:
      sample = getattr(sps,'{}_M{}_{}_ct{}_2018'.format(model,m,m-dm,ct))
      fn = 'limit_{}_datacard.txt'.format(sample.name.replace("2018","Run2"))
      result_path = os.path.join(path,fn)
      if os.path.exists(result_path):
        r.parse(sample,result_path)
      else:
        print ("File {} not opened.".format(result_path))
  for l in 'observed expect2p5 expect16 expect50 expect68 expect84 expect95 expect97p5'.split():
    for p in r.points:
      limits_2d[l].SetBinContent(limits_2d[l].FindBin(p.sample.mass,p.sample.mass-p.sample.massLSP),getattr(p, l))
    limits_2d_interp[l] = interpolate(limits_2d[l],x_fine,y_fine)
  exc_curve = {}
  for l in 'observed', 'expect50', 'expect16', 'expect84':
    if l not in exc_curve:
      exc_curve[l] = {}
    for opt in 'nm', 'up', 'dn':
      hexc = theory_exclude(model,limits_2d_interp[l],opt,'expect' not in l)
      g = exc_graph(hexc, 1, 1)
      exc_curve[l][opt] = g

  return limits_2d_interp,exc_curve

def compute_histogram_bins(data):
    data = sorted(data)
    n = len(data)

    if n < 2:
        raise ValueError("Need at least two data points to define bins")

    # Midpoints between data points define boundaries
    midpoints = [(data[i] + data[i+1]) / 2 for i in range(n - 1)]

    # First bin starts from left of first midpoint
    edges = [data[0] - (midpoints[0] - data[0])] + midpoints + [data[-1] + (data[-1] - midpoints[-1])]

    return edges

def make_2dplot_y_dm(model):
  if model == 'stop':
    masses = [400,500,600,700,800,900,1000,1100,1200,1300,1400]
    dms = [12,15,20,25]
    BRorct = [0.1,0.5,1] # BR
    xlow = 350
    xhigh = 1450
    production_nice = "#kern[0.1]{#tilde{t}}#kern[0.1]{#tilde{t}}"
  elif model == 'C1N2':
    masses = [200,300,400,500,600]
    dms = [12,15,20,25]
    BRorct = [0.2,2,20,200] # ctau in mm
    xlow = 150
    xhigh = 650
    production_nice = "#kern[0.1]{#tilde{#chi}^{#pm}_{1}}#kern[0.1]{#tilde{#chi}^{0}_{2}}"
  else:
    raise Exception("Model {} not defined!".format(model))

  x = masses
  y = dms

  x_coarse = array('d',[ix-50 for ix in x]+[x[-1]+50])
  y_coarse = array('d',[11.5,12.5,17.5,22.5,27.5])
  #x_fine = x
  #y_fine = y
  x_fine = [i-0.5 for i in range(int(min(x)),int(max(x))+2,1)]
  y_fine = [i-0.5 for i in range(int(min(y)),int(max(y))+2,1)]
  x_fine = array('d',x_fine)
  y_fine = array('d',y_fine)

  gt = make_theory(model)
  limits_2d = {}
  limits_2d_interp = {}
  exc_curve = {}
  if not os.path.exists(output):
    os.makedirs(output)

  for ibc in BRorct:
    limits_2d[ibc] = {}
    limits_2d_interp[ibc] = {}
    exc_curve[ibc] = {}
    r = limits()
    for m in masses:
      for dm in dms:
        # define a fake ctau for stop
        stopct = {
            25: 0.2,
            20: 2,
            15: 20,
            12: 200,
            }
        if model=='stop':
          ct = stopct[dm]
          BR = ibc
          realctau = getctauBR(m,dm,BR)
          decay_nice = "#tilde{{t}} #rightarrow bff'#kern[0.1]{{#tilde{{#chi}}^{{0}}_{{1}}}} / c#kern[0.1]{{#tilde{{#chi}}^{{0}}_{{1}}}}"
          params_nice = "B(#tilde{{t}} #rightarrow bff'#kern[0.1]{{#tilde{{#chi}}^{{0}}_{{1}}}}) = {}; B(#tilde{{t}} #rightarrow c#kern[0.1]{{#tilde{{#chi}}^{{0}}_{{1}}}}) = {}".format(BR,1.0-BR)
        elif model=='C1N2':
          ct = ibc
          BR = 1
          decay_nice = "#tilde{#chi}^{#pm}_{1} #rightarrow ff'#kern[0.1]{#tilde{#chi}^{0}_{1}}, #tilde{#chi}^{0}_{2} #rightarrow f#bar{f}#kern[0.1]{#tilde{#chi}^{0}_{1}}"
          params_nice = "c#tau = {} mm".format(ct)
        ctstr = str(ct).replace('.','p')
        sample = getattr(sps,'{}_M{}_{}_ct{}_2018'.format(model,m,m-dm,ctstr))
        if model=='stop':
          fn = 'limit_{}_datacard.txt'.format(sample.name.replace("2018",'Run2').replace("ct{}".format(ctstr),"BR{}".format(BR)).replace('.','p'))
        elif model=='C1N2':
          fn = 'limit_{}_datacard.txt'.format(sample.name.replace("2018",'Run2'))
        result_path = os.path.join(path,fn)
        if os.path.exists(result_path):
          r.parse(sample,result_path)
        else:
          print ("File {} not opened.".format(result_path))
    for l in 'observed expect2p5 expect16 expect50 expect68 expect84 expect95 expect97p5'.split():
      limits_2d[ibc][l] = ROOT.TH2D(l+model+str(ibc),'',len(x_coarse)-1,x_coarse,len(y_coarse)-1,y_coarse)
      for p in r.points:
        limits_2d[ibc][l].SetBinContent(limits_2d[ibc][l].FindBin(p.sample.mass,p.sample.mass-p.sample.massLSP),getattr(p, l))
      limits_2d_interp[ibc][l] = interpolate(limits_2d[ibc][l],x_fine,y_fine)
    for l in 'observed', 'expect50', 'expect16', 'expect84':
      if l not in exc_curve[ibc]:
        exc_curve[ibc][l] = {}
      for opt in 'nm', 'up', 'dn':
        hexc = theory_exclude(model,limits_2d_interp[ibc][l],opt,'expect' not in l)
        g = exc_graph(hexc, 1, 1)
        exc_curve[ibc][l][opt] = g

  return limits_2d_interp,exc_curve

def one_from_r(ex, name, rdir, ydm=True):
    print(ex)
    def read_csv(fn):
        lines = [x.strip() for x in open(os.path.join(rdir,fn)).read().replace('"', '').split('\n') if x.strip()]
        lines.pop(0)
        vs = []
        for line in lines:
            ws = [float(x) for x in line.split(',')]
            ws.pop(0)
            if len(ws) == 1:
                ws = ws[0]
            vs.append(ws)
        return vs

    x = read_csv('%s_x.csv' % ex)
    y = read_csv('%s_y.csv' % ex)
    z = read_csv('%s_z.csv' % ex)

    assert sorted(x) == x
    assert sorted(y) == y
    x_bins = compute_histogram_bins(x)
    #y_bins = compute_histogram_bins(y)
    y_bins = y
    nx = len(x)
    ny = len(y)
    #x.append(x[-1] + (x[-1] - x[-2]))
    y_bins.append(y_bins[-1] + (y_bins[-1] - y_bins[-2]))
    #print ex, nx, ny
    if ydm:
      y_bins = [11.5,12.5,17.5,22.5,27.5]
    else:
      y_bins = [0.05,0.35,0.65,1.35,2.65,7.35,12.65,27.35,72.65,127.35,272.65]
    x_bins = array('d', x_bins)
    y_bins = array('d', y_bins)
    h = ROOT.TH2F(name, '', len(x_bins)-1, x_bins, len(y_bins)-1, y_bins)
    h.SetStats(0)
    for ix in range(1, nx+1):
        for iy in range(1, ny+1):
            h.SetBinContent(ix, iy, z[ix-1][iy-1])
    return h

def one_from_ori(ex, name, rdir, ydm=True):
    print(ex)
    def read_csv(fn):
        lines = [x.strip() for x in open(os.path.join(rdir,fn)).read().replace('"', '').split('\n') if x.strip()]
        lines.pop(0)
        vs = []
        for line in lines:
            ws = [float(x) for x in line.split(',')]
            ws.pop(0)
            if len(ws) == 1:
                ws = ws[0]
            vs.append(ws)
        return vs

    x = read_csv('%s_x.csv' % ex)
    y = read_csv('%s_y.csv' % ex)
    z = read_csv('%s_z.csv' % ex)

    assert len(x) == len(y) == len(z)
    x_bins = compute_histogram_bins(sorted(list(set(x))))
    #y_bins = compute_histogram_bins(sorted(list(set(y))))
    y_bins = sorted(list(set(y)))
    y_bins.append(y_bins[-1] + (y_bins[-1] - y_bins[-2]))
    npoints = len(x)
    if ydm:
      y_bins = [11.5,12.5,17.5,22.5,27.5]
    else:
      y_bins = [0.05,0.35,0.65,1.35,2.65,7.35,12.65,27.35,72.65,127.35,272.65]
    x_bins = array('d', x_bins)
    y_bins = array('d', y_bins)
    h = ROOT.TH2F(name, '', len(x_bins)-1, x_bins, len(y_bins)-1, y_bins)
    h.SetStats(0)
    for i in range(npoints):
        h.SetBinContent(h.GetXaxis().FindBin(x[i]), h.GetYaxis().FindBin(y[i]), z[i])
    return h

def make_2dplot_y_dm_R(model,rdir):
  if model == 'stop':
    masses = [400,500,600,700,800,900,1000,1100,1200,1300,1400]
    dms = [12,15,20,25]
    BRorct = [0.1,0.5,1] # BR
    xlow = 350
    xhigh = 1450
    production_nice = "#kern[0.1]{#tilde{t}}#kern[0.1]{#tilde{t}}"
  elif model == 'C1N2':
    masses = [200,300,400,500,600]
    dms = [12,15,20,25]
    BRorct = [0.2,2,20,200] # ctau in mm
    xlow = 150
    xhigh = 650
    production_nice = "#kern[0.1]{#tilde{#chi}^{#pm}_{1}}#kern[0.1]{#tilde{#chi}^{0}_{2}}"
  else:
    raise Exception("Model {} not defined!".format(model))

  gt = make_theory(model)
  limits_2d_original = {}
  limits_2d_interp = {}
  exc_curve = {}
  if not os.path.exists(output):
    os.makedirs(output)

  for ibc in BRorct:
    limits_2d_original[ibc] = {}
    limits_2d_interp[ibc] = {}
    exc_curve[ibc] = {}
    for l in 'observed expect2p5 expect16 expect50 expect68 expect84 expect95 expect97p5'.split():
      limits_2d_interp[ibc][l] = one_from_r(f"{model}_{ibc}_{l}_interp",f"{model}_{ibc}_{l}_interp",rdir)
      limits_2d_original[ibc][l] = one_from_ori(f"{model}_{ibc}_{l}_original",f"{model}_{ibc}_{l}_original",rdir)
    for l in 'observed', 'expect50', 'expect16', 'expect84':
      if l not in exc_curve[ibc]:
        exc_curve[ibc][l] = {}
      for opt in 'nm', 'up', 'dn':
        hexc = theory_exclude(model,limits_2d_interp[ibc][l],opt,'expect' not in l)
        g = exc_graph(hexc, 1, 1)
        exc_curve[ibc][l][opt] = g

  #return limits_2d_interp,exc_curve
  return limits_2d_original,exc_curve

def draw_2dlimit_y_dm(model,rdir):
  if not os.path.exists(output):
    os.makedirs(output)
  #limit,exc = make_2dplot_y_dm(model)
  # use R interp
  limit,exc = make_2dplot_y_dm_R(model,rdir)
  for k in limit:
    if model=='stop':
      xlow = 350
      xhigh = 1450
      production_nice = "#kern[0.1]{#tilde{t}}#kern[0.1]{#tilde{t}}"
      decay_nice = "#tilde{{t}} #rightarrow bf#bar{{f}}'#kern[0.2]{{#tilde{{#chi}}^{{0}}_{{1}}}} / c#kern[0.1]{{#tilde{{#chi}}^{{0}}_{{1}}}}"
      params_nice = "#splitline{{B(#tilde{{t}} #rightarrow bf#bar{{f}}'#kern[0.2]{{#tilde{{#chi}}^{{0}}_{{1}}}}) = {}%}}{{B(#tilde{{t}} #rightarrow c#kern[0.1]{{#tilde{{#chi}}^{{0}}_{{1}}}}) = {}%}}".format(100*k,100*(1.0-k))
    elif model=='C1N2':
      xlow = 150
      xhigh = 650
      production_nice = "#kern[0.1]{#tilde{#chi}^{#pm}_{1}}#kern[0.1]{#tilde{#chi}^{0}_{2}}"
      decay_nice = "#tilde{#chi}^{#pm}_{1} #rightarrow ff'#kern[0.2]{#tilde{#chi}^{0}_{1}}, #tilde{#chi}^{0}_{2} #rightarrow f#bar{f}#kern[0.1]{#tilde{#chi}^{0}_{1}}"
      params_nice = "c#tau = {} mm".format(k)

    # Styling
    CMS.SetExtraText("")
    iPos = 0
    canv_name = 'limitplot_root_{}_bc{}'.format(model,k)
    CMS.SetLumi("100")
    CMS.SetEnergy("13")
    CMS.SetLumi("")
    CMS.SetEnergy("")
    CMS.ResetAdditionalInfo()
    canv = CMS.cmsCanvas(canv_name,xlow,xhigh,11.5,27.5,"LLP mass (GeV)","#Deltam (GeV)",square=CMS.kSquare,extraSpace=0.01,iPos=iPos,with_z_axis=True)
    canv.SetRightMargin(0.2)
    CMS.SetLumi("100")
    CMS.SetEnergy("13")
    draw_lumi(canv, iPos)
    canv.SetTopMargin(0.190)
    canv.SetBottomMargin(0.12)

    hf = canv.GetListOfPrimitives().FindObject("hframe")
    hf.GetXaxis().SetLabelSize(0.035)
    hf.GetXaxis().SetTitleSize(0.040)
    hf.GetXaxis().SetTitleOffset(1.2)
    hf.GetYaxis().SetLabelSize(0.035)
    hf.GetYaxis().SetTitleSize(0.040)
    hf.GetYaxis().SetTitleOffset(1.25)
    canv.Update()
    #canv.GetListOfPrimitives()[1].SetLabelSize(0.045, "XYZ")
    #canv.GetListOfPrimitives()[1].SetTitleSize(0.045, "XYZ")
    #canv.GetListOfPrimitives()[1].SetTitleOffset(1.4, "XYZ")
    limit[k]['observed'].GetZaxis().SetTitle("95% CL upper limit on #sigma (fb)")
    limit[k]['observed'].GetZaxis().SetLabelSize(0.035)
    limit[k]['observed'].GetZaxis().SetLabelOffset(0.01)
    limit[k]['observed'].GetZaxis().SetTitleSize(0.040)
    #limit[k]['observed'].GetZaxis().SetTitleOffset(1.7)
    limit[k]['observed'].GetZaxis().SetTitleOffset(1.4)
    limit[k]['observed'].SetMinimum(limit[k]['observed'].GetMinimum()/10.)
    #limit[k]['observed'].GetXaxis().SetLabelSize(0.1)
    limit[k]['observed'].SetName("observed_limit")
    limit[k]['observed'].Draw("colzsame")
    exc[k]['expect50']['nm'].SetLineColor(ROOT.kRed)
    exc[k]['expect50']['nm'].SetLineWidth(3)
    exc[k]['expect50']['nm'].SetLineStyle(7)
    exc[k]['expect16']['nm'].SetLineColor(ROOT.kRed)
    exc[k]['expect16']['nm'].SetLineWidth(1)
    exc[k]['expect16']['nm'].SetLineStyle(7)
    exc[k]['expect84']['nm'].SetLineColor(ROOT.kRed)
    exc[k]['expect84']['nm'].SetLineWidth(1)
    exc[k]['expect84']['nm'].SetLineStyle(7)
    exc[k]['expect50']['nm'].SetName('exp50_curve')
    exc[k]['expect16']['nm'].SetName('exp16_curve')
    exc[k]['expect84']['nm'].SetName('exp84_curve')
    exc[k]['expect50']['nm'].Draw('Lsame')
    exc[k]['expect16']['nm'].Draw('Lsame')
    exc[k]['expect84']['nm'].Draw('Lsame')
    exc[k]['observed']['nm'].SetLineColor(ROOT.kBlack)
    exc[k]['observed']['nm'].SetLineWidth(3)
    exc[k]['observed']['nm'].SetName('obs_curve')
    exc[k]['observed']['nm'].Draw('Lsame')

    CMS.UpdatePalettePosition(limit[k]['observed'],canv=canv,Y2=0.9)

    leg = ROOT.TLegend(canv.GetLeftMargin(), 0.810, 1-canv.GetRightMargin(), 0.931)
    leg.SetTextFont(42)
    leg.SetTextSize(0.038)
    leg.SetTextAlign(12)
    leg.SetNColumns(2)
    leg.SetColumnSeparation(0.40)
    leg.SetFillColor(ROOT.kWhite)
    leg.SetBorderSize(1)
    leg.AddEntry(0, '', '')
    leg.AddEntry(exc[k]['observed']['nm'], 'Obs.', 'L')
    leg.AddEntry(0, '', '')
    leg.AddEntry(exc[k]['expect50']['nm'], 'Med. exp.', 'L')
    leg.AddEntry(0, '', '')
    leg.AddEntry(exc[k]['expect84']['nm'], 'Exp. #pm 1 #sigma_{exp}', 'L')
    leg.Draw()
    sig_text         = write(42, 0.036, 0.165, 0.86, params_nice)
    canv.SetLogz()

    CMS.SaveCanvas(canv,os.path.join(output,'limit2d_{}_bc{}.pdf'.format(model,k)),close=False)
    CMS.SaveCanvas(canv,os.path.join(output,'limit2d_{}_bc{}.root'.format(model,k)),close=False)
    CMS.SaveCanvas(canv,os.path.join(output,'limit2d_{}_bc{}.png'.format(model,k)))

def csv_2d_y_dm(model,outdir):
  prepare = '''
Please do the following in a new terminal.
Setup:
ml build-env/f2022
ml foss/2022a
. /cvmfs/sft.cern.ch/lcg/views/LCG_100/x86_64-centos7-clang11-opt/setup.sh 
Run:
cd __PATH__
R_LIBS=~/.R Rscript Rscript.R
  '''.replace('__PATH__',os.path.abspath(outdir))
  print(prepare)
  if model == 'stop':
    masses = [400,500,600,700,800,900,1000,1100,1200,1300,1400]
    dms = [12,15,20,25]
    BRorct = [0.1,0.5,1] # BR
    xlow = 350
    xhigh = 1450
    production_nice = "#kern[0.1]{#tilde{t}}#kern[0.1]{#tilde{t}}"
  elif model == 'C1N2':
    masses = [200,300,400,500,600]
    dms = [12,15,20,25]
    BRorct = [0.2,2,20,200] # ctau in mm
    xlow = 150
    xhigh = 650
    production_nice = "#kern[0.1]{#tilde{#chi}^{#pm}_{1}}#kern[0.1]{#tilde{#chi}^{0}_{2}}"
  else:
    raise Exception("Model {} not defined!".format(model))

  x = masses
  y = dms

  if not os.path.exists(outdir):
    os.makedirs(outdir)

  f = open(f"{outdir}/Rscript.R",'w')
  f.write("library(akima)")
  for ibc in BRorct:
    r = limits()
    for m in masses:
      for dm in dms:
        # define a fake ctau for stop
        stopct = {
            25: 0.2,
            20: 2,
            15: 20,
            12: 200,
            }
        if model=='stop':
          ct = stopct[dm]
          BR = ibc
          realctau = getctauBR(m,dm,BR)
          decay_nice = "#tilde{{t}} #rightarrow bff'#kern[0.2]{{#tilde{{#chi}}^{{0}}_{{1}}}} / c#kern[0.1]{{#tilde{{#chi}}^{{0}}_{{1}}}}"
          params_nice = "B(#tilde{{t}} #rightarrow bff'#kern[0.2]{{#tilde{{#chi}}^{{0}}_{{1}}}}) = {}; B(#tilde{{t}} #rightarrow c#kern[0.1]{{#tilde{{#chi}}^{{0}}_{{1}}}}) = {}".format(BR,1.0-BR)
        elif model=='C1N2':
          ct = ibc
          BR = 1
          decay_nice = "#tilde{#chi}^{#pm}_{1} #rightarrow ff'#kern[0.2]{#tilde{#chi}^{0}_{1}}, #tilde{#chi}^{0}_{2} #rightarrow f#bar{f}#kern[0.1]{#tilde{#chi}^{0}_{1}}"
          params_nice = "c#tau = {} mm".format(ct)
        ctstr = str(ct).replace('.','p')
        sample = getattr(sps,'{}_M{}_{}_ct{}_2018'.format(model,m,m-dm,ctstr))
        if model=='stop':
          #fn = 'limit_{}_datacard.txt'.format(sample.name.replace("2018",'Run2').replace("ct{}".format(ctstr),"BR{}".format(BR)).replace('.','p'))
          fn = '{}_datacard_limitsum.txt'.format(sample.name.replace("2018",'Run2').replace("ct{}".format(ctstr),"BR{}".format(BR)).replace('.','p'))
        elif model=='C1N2':
          #fn = 'limit_{}_datacard.txt'.format(sample.name.replace("2018",'Run2'))
          fn = '{}_datacard_limitsum.txt'.format(sample.name.replace("2018",'Run2'))
        result_path = os.path.join(path,fn)
        if os.path.exists(result_path):
          r.parse(sample,result_path)
        else:
          print ("File {} not opened.".format(result_path))
    for l in 'observed expect2p5 expect16 expect50 expect68 expect84 expect95 expect97p5'.split():
      with open(f"{outdir}/{model}_{ibc}_{l}.csv","w") as fcsv:
        writer = csv.writer(fcsv)
        writer.writerow(["x", "y", "z"])
        for p in r.points:
          writer.writerow([p.sample.mass,p.sample.mass-p.sample.massLSP,getattr(p,l)])
      #print(f"csv file {outdir}/{model}_{ibc}_{l}.csv saved.")
      Rscript_template_STOP = '''
h<-read.table("__NAME__.csv", header=TRUE, sep=",")
write.csv(h$x,"__NAME___original_x.csv")
write.csv(h$y,"__NAME___original_y.csv")
write.csv(h$z,"__NAME___original_z.csv")
#i<-interp(x=h$x, y=h$y, z=h$z, xo=seq(400, 1400, by=10), yo=c(seq(12.001,13,by=100),seq(13,25,by=1)), linear=TRUE, extrap=FALSE)
i<-interp(x=h$x, y=h$y, z=h$z, xo=seq(400, 1400, by=10), yo=c(12.001,15,20,25), linear=TRUE, extrap=FALSE)
write.csv(i$x,"__NAME___interp_x.csv")
write.csv(i$y,"__NAME___interp_y.csv")
write.csv(i$z,"__NAME___interp_z.csv")
      '''
      Rscript_template_C1N2 = '''
h<-read.table("__NAME__.csv", header=TRUE, sep=",")
write.csv(h$x,"__NAME___original_x.csv")
write.csv(h$y,"__NAME___original_y.csv")
write.csv(h$z,"__NAME___original_z.csv")
#i<-interp(x=h$x, y=h$y, z=h$z, xo=seq(200, 600, by=10), yo=c(seq(12.001,13,by=100),seq(13,25,by=1)), linear=TRUE, extrap=FALSE)
i<-interp(x=h$x, y=h$y, z=h$z, xo=seq(200, 600, by=10), yo=c(12.001,15,20,25), linear=TRUE, extrap=FALSE)
write.csv(i$x,"__NAME___interp_x.csv")
write.csv(i$y,"__NAME___interp_y.csv")
write.csv(i$z,"__NAME___interp_z.csv")
      '''
      Rscript_template = Rscript_template_STOP if model=='stop' else Rscript_template_C1N2
      f.write(Rscript_template.replace('__NAME__',f"{model}_{ibc}_{l}"))

  f.close()
  return 

def make_2dplot_y_ctau_R(model,rdir):
  if model == 'stop':
    masses = [400,500,600,700,800,900,1000,1100,1200,1300,1400]
    dms = [12,15,20,25]
    BRorct = [0.1,0.5,1] # BR
    xlow = 350
    xhigh = 1450
    production_nice = "#kern[0.1]{#tilde{t}}#kern[0.1]{#tilde{t}}"
  elif model == 'C1N2':
    masses = [200,300,400,500,600]
    dms = [12,15,20,25]
    BRorct = [0.2,0.5,1,2,5,10,20,50,100,200] # ctau in mm
    xlow = 150
    xhigh = 650
    production_nice = "#kern[0.1]{#tilde{#chi}^{#pm}_{1}}#kern[0.1]{#tilde{#chi}^{0}_{2}}"
  else:
    raise Exception("Model {} not defined!".format(model))

  gt = make_theory(model)
  limits_2d_original = {}
  limits_2d_interp = {}
  exc_curve = {}
  if not os.path.exists(output):
    os.makedirs(output)

  for dm in dms:
    limits_2d_original[dm] = {}
    limits_2d_interp[dm] = {}
    exc_curve[dm] = {}
    for l in 'observed expect2p5 expect16 expect50 expect68 expect84 expect95 expect97p5'.split():
      limits_2d_interp[dm][l] = one_from_r(f"{model}_{dm}_{l}_interp",f"{model}_{dm}_{l}_interp",rdir,ydm=False)
      limits_2d_original[dm][l] = one_from_ori(f"{model}_{dm}_{l}_original",f"{model}_{dm}_{l}_original",rdir,ydm=False)
    for l in 'observed', 'expect50', 'expect16', 'expect84':
      if l not in exc_curve[dm]:
        exc_curve[dm][l] = {}
      for opt in 'nm', 'up', 'dn':
        hexc = theory_exclude(model,limits_2d_interp[dm][l],opt,'expect' not in l)
        g = exc_graph(hexc, 1, 1)
        exc_curve[dm][l][opt] = g

  #return limits_2d_interp,exc_curve
  return limits_2d_original,exc_curve

def draw_2dlimit_y_ctau(model,rdir):
  if not os.path.exists(output):
    os.makedirs(output)
  #limit,exc = make_2dplot_y_dm(model)
  # use R interp
  limit,exc = make_2dplot_y_ctau_R(model,rdir)
  for k in limit:
    if model=='stop':
      xlow = 350
      xhigh = 1450
      production_nice = "#kern[0.1]{#tilde{t}}#kern[0.1]{#tilde{t}}"
      decay_nice = "#tilde{{t}} #rightarrow bf#bar{{f}}'#kern[0.2]{{#tilde{{#chi}}^{{0}}_{{1}}}} / c#kern[0.1]{{#tilde{{#chi}}^{{0}}_{{1}}}}"
      params_nice = "#splitline{{B(#tilde{{t}} #rightarrow bf#bar{{f}}'#kern[0.2]{{#tilde{{#chi}}^{{0}}_{{1}}}}) = {}%}}{{B(#tilde{{t}} #rightarrow c#kern[0.1]{{#tilde{{#chi}}^{{0}}_{{1}}}}) = {}%}}".format(100*k,100*(1.0-k))
    elif model=='C1N2':
      xlow = 150
      xhigh = 650
      production_nice = "#kern[0.1]{#tilde{#chi}^{#pm}_{1}}#kern[0.1]{#tilde{#chi}^{0}_{2}}"
      decay_nice = "#tilde{#chi}^{#pm}_{1} #rightarrow f#bar{f}'#kern[0.2]{#tilde{#chi}^{0}_{1}}, #tilde{#chi}^{0}_{2} #rightarrow f#bar{f}#kern[0.1]{#tilde{#chi}^{0}_{1}}"
      params_nice = "#splitline{{{}}}{{#Deltam = {} GeV}}".format(decay_nice,k)

    # Styling
    CMS.SetExtraText("")
    iPos = 0
    canv_name = 'limitplot_root_{}_dm{}'.format(model,k)
    CMS.SetLumi("")
    CMS.SetEnergy("")
    CMS.ResetAdditionalInfo()
    canv = CMS.cmsCanvas(canv_name,xlow,xhigh,0.1,271.35,"LLP mass (GeV)","c#tau (mm)",square=CMS.kSquare,extraSpace=0.01,iPos=iPos,with_z_axis=True)
    canv.SetRightMargin(0.2)
    CMS.SetLumi("100")
    CMS.SetEnergy("13")
    draw_lumi(canv, iPos)
    canv.SetTopMargin(0.190)
    canv.SetBottomMargin(0.12)

    hf = canv.GetListOfPrimitives().FindObject("hframe")
    hf.GetXaxis().SetLabelSize(0.035)
    hf.GetXaxis().SetTitleSize(0.040)
    hf.GetXaxis().SetTitleOffset(1.2)
    hf.GetYaxis().SetLabelSize(0.035)
    hf.GetYaxis().SetTitleSize(0.040)
    hf.GetYaxis().SetTitleOffset(1.25)
    canv.Update()
    #canv.GetListOfPrimitives()[1].SetLabelSize(0.045, "XYZ")
    #canv.GetListOfPrimitives()[1].SetTitleSize(0.045, "XYZ")
    #canv.GetListOfPrimitives()[1].SetTitleOffset(1.4, "XYZ")
    limit[k]['observed'].GetZaxis().SetTitle("95% CL upper limit on #sigma (fb)")
    limit[k]['observed'].GetZaxis().SetLabelSize(0.035)
    limit[k]['observed'].GetZaxis().SetLabelOffset(0.01)
    limit[k]['observed'].GetZaxis().SetTitleSize(0.040)
    #limit[k]['observed'].GetZaxis().SetTitleOffset(1.65)
    limit[k]['observed'].GetZaxis().SetTitleOffset(1.4)
    #limit[k]['observed'].GetXaxis().SetLabelSize(0.1)
    limit[k]['observed'].SetMinimum(limit[k]['observed'].GetMinimum()/10.)
    limit[k]['observed'].SetName("observed_limit")
    limit[k]['observed'].Draw("colzsame")
    exc[k]['expect50']['nm'].SetLineColor(ROOT.kRed)
    exc[k]['expect50']['nm'].SetLineWidth(3)
    exc[k]['expect50']['nm'].SetLineStyle(7)
    exc[k]['expect16']['nm'].SetLineColor(ROOT.kRed)
    exc[k]['expect16']['nm'].SetLineWidth(1)
    exc[k]['expect16']['nm'].SetLineStyle(7)
    exc[k]['expect84']['nm'].SetLineColor(ROOT.kRed)
    exc[k]['expect84']['nm'].SetLineWidth(1)
    exc[k]['expect84']['nm'].SetLineStyle(7)
    exc[k]['expect50']['nm'].SetName('exp50_curve')
    exc[k]['expect16']['nm'].SetName('exp16_curve')
    exc[k]['expect84']['nm'].SetName('exp84_curve')
    exc[k]['expect50']['nm'].Draw('Lsame')
    exc[k]['expect16']['nm'].Draw('Lsame')
    exc[k]['expect84']['nm'].Draw('Lsame')
    exc[k]['observed']['nm'].SetLineColor(ROOT.kBlack)
    exc[k]['observed']['nm'].SetLineWidth(3)
    exc[k]['observed']['nm'].SetName('obs_curve')
    exc[k]['observed']['nm'].Draw('Lsame')

    CMS.UpdatePalettePosition(limit[k]['observed'],canv=canv,Y2=0.9)

    leg = ROOT.TLegend(canv.GetLeftMargin(), 0.810, 1-canv.GetRightMargin(), 0.931)
    leg.SetTextFont(42)
    leg.SetTextSize(0.038)
    leg.SetTextAlign(12)
    leg.SetNColumns(2)
    leg.SetColumnSeparation(0.4)
    leg.SetFillColor(ROOT.kWhite)
    leg.SetBorderSize(1)
    leg.AddEntry(0, '', '')
    leg.AddEntry(exc[k]['observed']['nm'], 'Obs.', 'L')
    leg.AddEntry(0, '', '')
    leg.AddEntry(exc[k]['expect50']['nm'], 'Med. exp.', 'L')
    leg.AddEntry(0, '', '')
    leg.AddEntry(exc[k]['expect84']['nm'], 'Exp. #pm 1 #sigma_{exp}', 'L')
    leg.Draw()
    sig_text         = write(42, 0.038, 0.17, 0.85, params_nice)
    canv.SetLogy()
    canv.SetLogz()

    CMS.SaveCanvas(canv,os.path.join(output,'limit2d_{}_dm{}.pdf'.format(model,k)),close=False)
    CMS.SaveCanvas(canv,os.path.join(output,'limit2d_{}_dm{}.root'.format(model,k)),close=False)
    CMS.SaveCanvas(canv,os.path.join(output,'limit2d_{}_dm{}.png'.format(model,k)))

def csv_2d_y_ctau(model,outdir):
  prepare = '''
Please do the following in a new terminal.
Setup:
ml build-env/f2022
ml foss/2022a
. /cvmfs/sft.cern.ch/lcg/views/LCG_100/x86_64-centos7-clang11-opt/setup.sh 
Run:
cd __PATH__
R_LIBS=~/.R Rscript Rscriptctau.R
  '''.replace('__PATH__',os.path.abspath(outdir))
  print(prepare)
  if model == 'stop':
    masses = [400,500,600,700,800,900,1000,1100,1200,1300,1400]
    dms = [12,15,20,25]
    BRorct = [0.1,0.5,1] # BR
    xlow = 350
    xhigh = 1450
    production_nice = "#kern[0.1]{#tilde{t}}#kern[0.1]{#tilde{t}}"
  elif model == 'C1N2':
    masses = [200,300,400,500,600]
    dms = [12,15,20,25]
    #BRorct = [0.2,2,20,200] # ctau in mm
    BRorct = [0.2,0.5,1,2,5,10,20,50,100,200] # ctau in mm
    xlow = 150
    xhigh = 650
    production_nice = "#kern[0.1]{#tilde{#chi}^{#pm}_{1}}#kern[0.1]{#tilde{#chi}^{0}_{2}}"
  else:
    raise Exception("Model {} not defined!".format(model))

  if not os.path.exists(outdir):
    os.makedirs(outdir)

  f = open(f"{outdir}/Rscriptctau.R",'w')
  f.write("library(akima)")
  for dm in dms:
    r = limits()
    for m in masses:
      for ibc in BRorct:
        # define a fake ctau for stop
        stopct = {
            25: 0.2,
            20: 2,
            15: 20,
            12: 200,
            }
        if model=='stop':
          ct = stopct[dm]
          BR = ibc
          realctau = getctauBR(m,dm,BR)
          decay_nice = "#tilde{{t}} #rightarrow bff'#kern[0.1]{{#tilde{{#chi}}^{{0}}_{{1}}}} / c#kern[0.1]{{#tilde{{#chi}}^{{0}}_{{1}}}}"
          params_nice = "B(#tilde{{t}} #rightarrow bff'#kern[0.1]{{#tilde{{#chi}}^{{0}}_{{1}}}}) = {}; B(#tilde{{t}} #rightarrow c#kern[0.1]{{#tilde{{#chi}}^{{0}}_{{1}}}}) = {}".format(BR,1.0-BR)
        elif model=='C1N2':
          ct = ibc
          BR = 1
          decay_nice = "#tilde{#chi}^{#pm}_{1} #rightarrow ff'#kern[0.1]{#tilde{#chi}^{0}_{1}}, #tilde{#chi}^{0}_{2} #rightarrow f#bar{f}#kern[0.1]{#tilde{#chi}^{0}_{1}}"
          params_nice = "c#tau = {} mm".format(ct)
        ctstr = str(ct).replace('.','p')
        sample = getattr(sps,'{}_M{}_{}_ct{}_2018'.format(model,m,m-dm,ctstr))
        if model=='stop':
          #fn = 'limit_{}_datacard.txt'.format(sample.name.replace("2018",'Run2').replace("ct{}".format(ctstr),"BR{}".format(BR)).replace('.','p'))
          fn = '{}_datacard_limitsum.txt'.format(sample.name.replace("2018",'Run2').replace("ct{}".format(ctstr),"BR{}".format(BR)).replace('.','p'))
        elif model=='C1N2':
          fn = '{}_datacard_limitsum.txt'.format(sample.name.replace("2018",'Run2'))
        result_path = os.path.join(path,fn)
        if os.path.exists(result_path):
          r.parse(sample,result_path)
        else:
          print ("File {} not opened.".format(result_path))
    for l in 'observed expect2p5 expect16 expect50 expect68 expect84 expect95 expect97p5'.split():
      with open(f"{outdir}/{model}_{dm}_{l}.csv","w") as fcsv:
        writer = csv.writer(fcsv)
        writer.writerow(["x", "y", "z"])
        for p in r.points:
          writer.writerow([p.sample.mass,p.sample.tau,getattr(p,l)])
      #print(f"csv file {outdir}/{model}_{ibc}_{l}.csv saved.")
      Rscript_template_STOP = '''
h<-read.table("__NAME__.csv", header=TRUE, sep=",")
write.csv(h$x,"__NAME___original_x.csv")
write.csv(h$y,"__NAME___original_y.csv")
write.csv(h$z,"__NAME___original_z.csv")
#i<-interp(x=h$x, y=h$y, z=h$z, xo=seq(400, 1400, by=10), yo=c(seq(12.001,13,by=100),seq(13,25,by=1)), linear=TRUE, extrap=FALSE)
i<-interp(x=h$x, y=h$y, z=h$z, xo=seq(400, 1400, by=10), yo=c(12.001,15,20,25), linear=TRUE, extrap=FALSE)
write.csv(i$x,"__NAME___interp_x.csv")
write.csv(i$y,"__NAME___interp_y.csv")
write.csv(i$z,"__NAME___interp_z.csv")
      '''
      Rscript_template_C1N2 = '''
h<-read.table("__NAME__.csv", header=TRUE, sep=",")
write.csv(h$x,"__NAME___original_x.csv")
write.csv(h$y,"__NAME___original_y.csv")
write.csv(h$z,"__NAME___original_z.csv")
#i<-interp(x=h$x, y=h$y, z=h$z, xo=seq(200, 600, by=10), yo=c(seq(12.001,13,by=100),seq(13,25,by=1)), linear=TRUE, extrap=FALSE)
i<-interp(x=h$x, y=h$y, z=h$z, xo=seq(200, 600, by=10), yo=c(0.200001,0.5,1,2,5,10,20,50,100,200), linear=TRUE, extrap=FALSE)
#i<-interp(x=h$x, y=log10(h$y), z=h$z, xo=seq(200, 600, by=10), yo=log10(c(0.200001,seq(0.3,1.9,by=0.1),seq(2,19,by=1),seq(20,200,by=10))), linear=TRUE, extrap=FALSE)
write.csv(i$x,"__NAME___interp_x.csv")
write.csv(i$y,"__NAME___interp_y.csv")
write.csv(i$z,"__NAME___interp_z.csv")
      '''
      Rscript_template = Rscript_template_STOP if model=='stop' else Rscript_template_C1N2
      f.write(Rscript_template.replace('__NAME__',f"{model}_{dm}_{l}"))

  f.close()
  return 

def draw_2dlimit(model):
    if not os.path.exists(output):
      os.makedirs(output)
    if model=='stop':
      limit,exc = make_2dplot_y_dm(model)
    # Styling
    CMS.SetExtraText("Preliminary")
    iPos = 0
    canv_name = 'limitplot_root'
    CMS.SetLumi("100")
    CMS.SetEnergy("13")
    CMS.ResetAdditionalInfo()
    canv = CMS.cmsCanvas(canv_name,375,1425,11.5,25.5,"LLP mass (GeV)","#Deltam (GeV)",square=CMS.kSquare,extraSpace=0.01,iPos=iPos,with_z_axis=True)
    canv.SetTopMargin(0.180)
    canv.SetBottomMargin(0.12)
    canv.GetListOfPrimitives()[1].SetLabelSize(0.045, "XYZ")
    canv.GetListOfPrimitives()[1].SetTitleSize(0.045, "XYZ")
    canv.GetListOfPrimitives()[1].SetTitleOffset(1.4, "XYZ")
    limit['observed'].GetZaxis().SetTitle("95% CL upper limit on #sigma (fb)")
    limit['observed'].GetZaxis().SetLabelSize(0.03)
    limit['observed'].GetZaxis().SetLabelOffset(0.00005)
    limit['observed'].GetZaxis().SetTitleSize(0.03)
    limit['observed'].GetZaxis().SetTitleOffset(1.20)
    limit['observed'].GetXaxis().SetLabelSize(0.2)
    limit['observed'].Draw("colzsame")
    exc['expect50']['nm'].SetLineColor(ROOT.kRed)
    exc['expect50']['nm'].SetLineWidth(3)
    exc['expect50']['nm'].SetLineStyle(7)
    exc['expect16']['nm'].SetLineColor(ROOT.kRed)
    exc['expect16']['nm'].SetLineWidth(1)
    exc['expect16']['nm'].SetLineStyle(7)
    exc['expect84']['nm'].SetLineColor(ROOT.kRed)
    exc['expect84']['nm'].SetLineWidth(1)
    exc['expect84']['nm'].SetLineStyle(7)
    exc['expect50']['nm'].Draw('Lsame')
    exc['expect16']['nm'].Draw('Lsame')
    exc['expect84']['nm'].Draw('Lsame')
    exc['observed']['nm'].SetLineColor(ROOT.kBlack)
    exc['observed']['nm'].SetLineWidth(3)
    exc['observed']['nm'].Draw('Lsame')

    CMS.UpdatePalettePosition(limit['observed'],canv=canv,Y2=0.9)

    leg = ROOT.TLegend(canv.GetLeftMargin(), 0.820, 1-canv.GetRightMargin(), 0.931)
    leg.SetTextFont(42)
    leg.SetTextSize(0.03)
    leg.SetTextAlign(22)
    leg.SetNColumns(2)
    leg.SetColumnSeparation(0.35)
    leg.SetFillColor(ROOT.kWhite)
    leg.SetBorderSize(1)
    leg.AddEntry(0, '', '')
    leg.AddEntry(exc['observed']['nm'], '#kern[-0.16]{Observed}', 'L')
    leg.AddEntry(0, '', '')
    leg.AddEntry(exc['expect50']['nm'], '#kern[-0.16]{Median expected}', 'L')
    leg.AddEntry(0, '', '')
    leg.AddEntry(exc['expect84']['nm'], '#kern[-0.16]{Expected #pm 1 #sigma_{exp}}', 'L')
    leg.Draw()
    sig_text         = write(42, 0.04, 0.20, 0.88, "#tilde{t} #rightarrow bf#bar{f}#kern[0.1]{#tilde{#chi}^{0}_{1}}")

    #CMS.SaveCanvas(canv,"2dlimit.pdf",close=False)
    #CMS.SaveCanvas(canv,"2dlimit.png",close=False)
    CMS.SaveCanvas(canv,os.path.join(output,'limit2d_{}.pdf'.format(model)),close=False)
    CMS.SaveCanvas(canv,os.path.join(output,'limit2d_{}.root'.format(model)),close=False)
    CMS.SaveCanvas(canv,os.path.join(output,'limit2d_{}.png'.format(model)))

model = 'C1N2'
path = '/users/ang.li/public/SoftDV/Combine/CMSSW_14_1_0_pre4/src/HiggsAnalysis/CombinedLimit/datacards/limit_HybridNew2C1N2_Run2_20250516_2/'
rdir = '/users/ang.li/public/SoftDV/CMSSW_13_3_0/src/SoftDisplacedVertices/Plotter/limits/limit_csv_C1N2_Run2_20250516_2_HybridNew2/'
output = '/groups/hephy/cms/ang.li/SDV/{}limitHybridNew2_C1N2_Run2_20250516_2_root/'.format(model)
#make_1dplot(model)
draw_2dlimit_y_ctau(model,rdir)
#csv_2d_y_ctau(model,"limit_csv_C1N2_Run2_20250516_2_HybridNew2")

model = 'stop'
path = '/users/ang.li/public/SoftDV/Combine/CMSSW_14_1_0_pre4/src/HiggsAnalysis/CombinedLimit/datacards/limit_HybridNew2stop_Run2_20250516_2/'
rdir = '/users/ang.li/public/SoftDV/CMSSW_13_3_0/src/SoftDisplacedVertices/Plotter/limits/limit_csv_stop_Run2_20250516_2_HybridNew2/'
output = '/groups/hephy/cms/ang.li/SDV/{}limitHybridNew2_stop_Run2_20250516_2_2D_root/'.format(model)
#make_1dplot(model)
draw_2dlimit_y_dm(model,rdir)
#csv_2d_y_dm(model,"limit_csv_stop_Run2_20250516_2_HybridNew2")
