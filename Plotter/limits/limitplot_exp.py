#!/usr/bin/env python

import os, sys, re
import ROOT
import cmsstyle as CMS
from array import array
import SoftDisplacedVertices.Samples.Samples as sps
ROOT.gROOT.SetBatch(ROOT.kTRUE)

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
            #('observed'  , re.compile('Observed Limit: r < (.*)')),
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
            self.observed = self.expect50

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

def make_1dplot():
  xkey='mass'
  gt = make_theory(model)
  if not os.path.exists(output):
    os.makedirs(output)
  for dm,ct in zip([25,20,15,12],['0p2','2','20','200']):
    r = limits()
    for m in [600,1000,1400]:
      sample = getattr(sps,'{}_M{}_{}_ct{}_2018'.format(model,m,m-dm,ct))
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
    CMS.SetLumi("100.3")
    CMS.SetEnergy("13")
    CMS.ResetAdditionalInfo()
    canv = CMS.cmsCanvas(canv_name,550,1450,0.1,1e+05,"LLP mass (GeV)","#sigma#bf{#it{#Beta}}^{2} (fb)",square=CMS.kSquare,extraSpace=0.01,iPos=iPos)
    canv.GetListOfPrimitives()[1].SetLabelSize(0.045, "XYZ")
    canv.GetListOfPrimitives()[1].SetTitleSize(0.045, "XYZ")
    canv.GetListOfPrimitives()[1].SetTitleOffset(1.4, "XYZ")
    expect95.GetXaxis().SetLabelSize(0.25)
    CMS.cmsDraw(expect95, "3", fcolor = ROOT.TColor.GetColor("#F5BB54"))
    CMS.cmsDraw(expect68, "Same3", fcolor = ROOT.TColor.GetColor("#607641"))
    CMS.cmsDraw(expect50, "L", lwidth=2)
    CMS.cmsDraw(gt, "L3Same", lwidth=2, lcolor=46, fcolor = 45, alpha=0.5)
    leg = CMS.cmsLeg(0.2, 0.90 - 0.05 * 3, 0.9, 0.90, textSize=0.04, columns=2)
    leg.AddEntry(0, '#kern[-0.22]{95% CL upper limits:}', '')
    leg.AddEntry(0, '', '')

    leg.AddEntry(expect50, "Median expected","L")
    leg.AddEntry(expect68, "68% expected","F")
    leg.AddEntry(gt, "#kern[0.1]{#tilde{t}}#kern[0.1]{#tilde{t}} production","LF")
    leg.AddEntry(expect95, "95% expected","F")
    canv.SetLogy()
    sig_text         = write(42, 0.04, 0.20, 0.255, "#tilde{t} #rightarrow bf#bar{f}#kern[0.1]{#tilde{#chi}^{0}_{1}}")
    mass_or_tau_text = write(42, 0.04, 0.20, 0.200, "#Delta m = {} GeV, c#tau = {} mm".format(dm,ct.replace('p','.')))
    CMS.SaveCanvas(canv,os.path.join(output,'limit1d_mass_dm{}_ct{}.pdf'.format(dm,ct)),close=False)
    CMS.SaveCanvas(canv,os.path.join(output,'limit1d_mass_dm{}_ct{}.png'.format(dm,ct)))

def interpolate(h,x,y):
  hnew = ROOT.TH2D(h.GetName()+'inter','',len(x)-1,x,len(y)-1,y)
  for m in x:
    m = m+25
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
        y = yax.GetBinLowEdge(iy)
        for ix in range(h.GetNbinsX(), 0, -1):
            x = xax.GetBinLowEdge(ix)
            l = h.GetBinContent(ix, iy)
            if l:
                xs.append(x)
                ys.append(y)
                #print x, y, l
                break
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

def draw_2dlimit():
  if not os.path.exists(output):
    os.makedirs(output)
  limit,exc = make_2dplot()
  # Styling
  CMS.SetExtraText("Preliminary")
  iPos = 0
  canv_name = 'limitplot_root'
  CMS.SetLumi("100.3")
  CMS.SetEnergy("13")
  CMS.ResetAdditionalInfo()
  canv = CMS.cmsCanvas(canv_name,575,1425,11.5,25.5,"LLP mass (GeV)","#Delta m (GeV)",square=CMS.kSquare,extraSpace=0.01,iPos=iPos,with_z_axis=True)
  canv.SetTopMargin(0.160)
  canv.SetBottomMargin(0.12)
  canv.GetListOfPrimitives()[1].SetLabelSize(0.045, "XYZ")
  canv.GetListOfPrimitives()[1].SetTitleSize(0.045, "XYZ")
  canv.GetListOfPrimitives()[1].SetTitleOffset(1.4, "XYZ")
  limit['expect50'].GetZaxis().SetTitle("95% CL upper limit on #sigma#bf{#it{#Beta}}^{2} (fb)")
  limit['expect50'].GetZaxis().SetLabelSize(0.03)
  limit['expect50'].GetZaxis().SetLabelOffset(0.00005)
  limit['expect50'].GetZaxis().SetTitleSize(0.03)
  limit['expect50'].GetZaxis().SetTitleOffset(1.20)
  limit['expect50'].GetXaxis().SetLabelSize(0.2)
  limit['expect50'].Draw("colzsame")
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

  CMS.UpdatePalettePosition(limit['expect50'],canv=canv,Y2=0.9)

  leg = ROOT.TLegend(canv.GetLeftMargin(), 0.840, 1-canv.GetRightMargin(), 0.931)
  leg.SetTextFont(42)
  leg.SetTextSize(0.03)
  leg.SetTextAlign(22)
  leg.SetNColumns(2)
  leg.SetColumnSeparation(0.35)
  leg.SetFillColor(ROOT.kWhite)
  leg.SetBorderSize(1)
  leg.AddEntry(0, '', '')
  leg.AddEntry(exc['expect50']['nm'], '#kern[-0.16]{Median expected}', 'L')
  leg.AddEntry(0, '', '')
  leg.AddEntry(exc['expect84']['nm'], '#kern[-0.16]{Expected #pm 1 #sigma_{exp}}', 'L')
  leg.Draw()
  sig_text         = write(42, 0.04, 0.20, 0.88, "#tilde{t} #rightarrow bf#bar{f}#kern[0.1]{#tilde{#chi}^{0}_{1}}")

  #CMS.SaveCanvas(canv,"2dlimit.pdf",close=False)
  #CMS.SaveCanvas(canv,"2dlimit.png",close=False)
  CMS.SaveCanvas(canv,os.path.join(output,'limit2d_{}.pdf'.format(model)),close=False)
  CMS.SaveCanvas(canv,os.path.join(output,'limit2d_{}.png'.format(model)))

model = 'stop'
#path = '/users/ang.li/public/SoftDV/Combine/CMSSW_14_1_0_pre4/src/HiggsAnalysis/CombinedLimit/datacards/limit_STOP_Run2_20241218/'
path = '/users/ang.li/public/SoftDV/Combine/CMSSW_14_1_0_pre4/src/HiggsAnalysis/CombinedLimit/datacards/limit_STOP_Run2_20250206_3tk_Buncert_Asimov/'
#path = '/users/ang.li/public/SoftDV/Combine/CMSSW_14_1_0_pre4/src/HiggsAnalysis/CombinedLimit/datacards/limit_STOP_Run2_20250205_23tk_Asimov/'
#path='/users/ang.li/public/SoftDV/Combine/CMSSW_14_1_0_pre4/src/HiggsAnalysis/CombinedLimit/datacards/limit_C1N2_0909/'
output = '/groups/hephy/cms/ang.li/SDV/{}limit_run2_20250206_3tk_Buncert_Asimov/'.format(model)
make_1dplot()
draw_2dlimit()
