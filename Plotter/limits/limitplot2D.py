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
                    x = x*self.sample.xsec*1000 #convert to fb
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
    if which not in ('gluglu', 'stopstop', 'higgsino_N2N1'):
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
  gt = make_theory('stopstop')
  path = '/users/ang.li/public/SoftDV/Combine/CMSSW_14_1_0_pre4/src/HiggsAnalysis/CombinedLimit/datacards/limit_stop/'
  output = '/groups/hephy/cms/ang.li/SDV/stoplimit'
  if not os.path.exists(output):
    os.makedirs(output)
  for dm,ct in zip([25,20,15,12],['0p2','2','20','200']):
    r = limits()
    for m in [600,1000,1400]:
      sample = getattr(sps,'stop_M{}_{}_ct{}_2018'.format(m,m-dm,ct))
      fn = 'limit_{}_datacard.txt'.format(sample.name)
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
    CMS.SetLumi("")
    CMS.SetEnergy("13")
    CMS.ResetAdditionalInfo()
    canv = CMS.cmsCanvas(canv_name,550,1450,0.1,1e+05,"LLP mass (GeV)","#sigma #times BR^{2} (fb)",square=CMS.kSquare,extraSpace=0.01,iPos=iPos)
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

make_1dplot()
