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
            #assert p.valid
            assert p.expect_valid
            self.points.append(p)

    def __getitem__(self, key):
        if key == 'tau':
            #return [p.sample.tau/1000. for p in self.points]
            return [p.sample.tau for p in self.points]
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

def parse_theory_tau(which, mass, x_range, include_errors=True, cache={}):
    if which not in ('gluglu', 'stop', 'C1N2'):
        raise ValueError('bad which %r' % which)
    fn = which + '.csv'
    if not (fn in cache):
        xsecs = [eval(x.strip()) for x in open(fn) if x.strip()]
        xsec_mass = []
        for z in xsecs:
            if z[0]==mass:
                xsec_mass.append((x_range[0], z[1]*1000, z[2]/100*z[1]*1000))
                xsec_mass.append((x_range[1], z[1]*1000, z[2]/100*z[1]*1000))
        if not include_errors:
            xsec_mass = [(a,b,0.) for a,b,_ in xsec_mass]
        cache[fn] = xsecs
    return cache[fn]

def make_theory_tau(which, mass, x_range, include_errors=True, return_list=False):
    xsecs = parse_theory_tau(which, mass, x_range, include_errors)
    g = tge(xsecs)
    g.SetLineWidth(2)
    g.SetLineColor(9)
    if return_list:
        return g, xsecs
    else:
        return g

def make_1dplot_ctau_compare(path1, path2, label1="Set 1", label2="Set 2"):
    """
    Compare limits from two different folders
    
    Parameters:
    -----------
    path1 : str
        Path to first folder containing limit txt files
    path2 : str
        Path to second folder containing limit txt files
    label1 : str
        Label for first set of limits (for legend)
    label2 : str
        Label for second set of limits (for legend)
    """
    xkey='tau'
    if not os.path.exists(output):
        os.makedirs(output)
    
    for m in [200,500]:
        for dm in [5,15]:
            # Parse limits from first folder
            r1 = limits()
            for ct in ['2','20','200']:
                sample = getattr(sps,'{}ML_M{}_{}_ct{}_2018'.format(model,m,m-dm,ct))
                fn = 'limit_{}_datacard.txt'.format(sample.name.replace("2018",'2018').replace('ML',''))
                result_path = os.path.join(path1,fn)
                if os.path.exists(result_path):
                    r1.parse(sample,result_path)
                else:
                    print ("File {} not opened.".format(result_path))
            
            # Parse limits from second folder
            r2 = limits()
            for ct in ['2','20','200']:
                sample = getattr(sps,'{}ML_M{}_{}_ct{}_2018'.format(model,m,m-dm,ct))
                fn = 'limit_{}_datacard.txt'.format(sample.name.replace("2018",'2018').replace('ML',''))
                result_path = os.path.join(path2,fn)
                if os.path.exists(result_path):
                    r2.parse(sample,result_path)
                else:
                    print ("File {} not opened.".format(result_path))

            # Create graphs for first set
            expect50_1 = tgae(r1[xkey], r1['expect50'], None, None, None, None)
            expect95_1 = tgae(r1[xkey], r1['expect95'], None, None, r1['expect95lo'], r1['expect95hi'])
            expect68_1 = tgae(r1[xkey], r1['expect68'], None, None, r1['expect68lo'], r1['expect68hi'])
            
            # Create graphs for second set
            expect50_2 = tgae(r2[xkey], r2['expect50'], None, None, None, None)
            expect95_2 = tgae(r2[xkey], r2['expect95'], None, None, r2['expect95lo'], r2['expect95hi'])
            expect68_2 = tgae(r2[xkey], r2['expect68'], None, None, r2['expect68lo'], r2['expect68hi'])

            gt = make_theory_tau(model,m,[1,300])

            # Styling
            CMS.SetExtraText("Preliminary")
            iPos = 0
            canv_name = 'limitplot_compare'
            CMS.SetLumi("60")
            CMS.SetEnergy("13")
            CMS.ResetAdditionalInfo()
            canv = CMS.cmsCanvas(canv_name,1,300,1,1e+06,"c#tau (mm)","#sigma#bf{#it{#Beta}} (fb)",square=CMS.kSquare,extraSpace=0.01,iPos=iPos)
            canv.GetListOfPrimitives()[1].SetLabelSize(0.045, "XYZ")
            canv.GetListOfPrimitives()[1].SetTitleSize(0.045, "XYZ")
            canv.GetListOfPrimitives()[1].SetTitleOffset(1.4, "XYZ")
            expect95_1.GetXaxis().SetLabelSize(0.25)
            
            # Draw first set with original colors
            CMS.cmsDraw(expect95_1, "3", fcolor = ROOT.TColor.GetColor("#F5BB54"))
            CMS.cmsDraw(expect68_1, "Same3", fcolor = ROOT.TColor.GetColor("#607641"))
            CMS.cmsDraw(expect50_1, "L", lwidth=2, lcolor=ROOT.kBlack)
            
            # Draw second set with different colors/styles
            # Using dashed lines and different colors for the second set
            CMS.cmsDraw(expect95_2, "Same3", fcolor = ROOT.TColor.GetColor("#9AC2E5"), alpha=0.5)
            CMS.cmsDraw(expect68_2, "Same3", fcolor = ROOT.TColor.GetColor("#6B8FA3"), alpha=0.5)
            CMS.cmsDraw(expect50_2, "LSame", lwidth=2, lcolor=ROOT.kBlue, lstyle=2)
            
            # Legend
            leg = CMS.cmsLeg(0.2, 0.90 - 0.05 * 6, 0.9, 0.90, textSize=0.035, columns=2)
            leg.AddEntry(0, '#kern[-0.22]{95% CL upper limits:}', '')
            leg.AddEntry(0, '', '')
            
            # First set
            leg.AddEntry(expect50_1, "{} - Median expected".format(label1),"L")
            leg.AddEntry(expect68_1, "{} - 68% expected".format(label1),"F")
            leg.AddEntry(0, "", "")
            leg.AddEntry(expect95_1, "{} - 95% expected".format(label1),"F")
            
            # Second set
            leg.AddEntry(expect50_2, "{} - Median expected".format(label2),"L")
            leg.AddEntry(expect68_2, "{} - 68% expected".format(label2),"F")
            leg.AddEntry(0, "", "")
            leg.AddEntry(expect95_2, "{} - 95% expected".format(label2),"F")
            
            canv.SetLogy()
            canv.SetLogx()
            sig_text = write(42, 0.04, 0.20, 0.255, "#tilde{#chi_{2}^{0}} #rightarrow f#bar{f}#kern[0.1]{#tilde{#chi}^{0}_{1}}")
            mass_or_tau_text = write(42, 0.04, 0.20, 0.200, "M = {} GeV, #Delta m = {} GeV".format(m,dm))
            
            CMS.SaveCanvas(canv,os.path.join(output,'limit1d_compare_M{}_dm{}.pdf'.format(m,dm)),close=False)
            CMS.SaveCanvas(canv,os.path.join(output,'limit1d_compare_M{}_dm{}.png'.format(m,dm)))

def make_1dplot_mass_compare(path1, path2, label1="Set 1", label2="Set 2"):
    """
    Compare mass-based limits from two different folders
    
    Parameters:
    -----------
    path1 : str
        Path to first folder containing limit txt files
    path2 : str
        Path to second folder containing limit txt files
    label1 : str
        Label for first set of limits (for legend)
    label2 : str
        Label for second set of limits (for legend)
    """
    xkey='mass'
    if not os.path.exists(output):
        os.makedirs(output)
    
    for dm in [5,15]:
        for ct in ['2','20','200']:
            # Parse limits from first folder
            r1 = limits()
            for m in [200,500]:
                sample = getattr(sps,'{}ML_M{}_{}_ct{}_2018'.format(model,m,m-dm,ct))
                fn = 'limit_{}_datacard.txt'.format(sample.name.replace("2018",'2018').replace('ML',''))
                result_path = os.path.join(path1,fn)
                if os.path.exists(result_path):
                    r1.parse(sample,result_path)
                else:
                    print ("File {} not opened.".format(result_path))
            
            # Parse limits from second folder
            r2 = limits()
            for m in [200,500]:
                sample = getattr(sps,'{}ML_M{}_{}_ct{}_2018'.format(model,m,m-dm,ct))
                fn = 'limit_{}_datacard.txt'.format(sample.name.replace("2018",'2018').replace('ML',''))
                result_path = os.path.join(path2,fn)
                if os.path.exists(result_path):
                    r2.parse(sample,result_path)
                else:
                    print ("File {} not opened.".format(result_path))

            # Create graphs for first set
            expect50_1 = tgae(r1[xkey], r1['expect50'], None, None, None, None)
            expect95_1 = tgae(r1[xkey], r1['expect95'], None, None, r1['expect95lo'], r1['expect95hi'])
            expect68_1 = tgae(r1[xkey], r1['expect68'], None, None, r1['expect68lo'], r1['expect68hi'])
            
            # Create graphs for second set
            expect50_2 = tgae(r2[xkey], r2['expect50'], None, None, None, None)
            expect95_2 = tgae(r2[xkey], r2['expect95'], None, None, r2['expect95lo'], r2['expect95hi'])
            expect68_2 = tgae(r2[xkey], r2['expect68'], None, None, r2['expect68lo'], r2['expect68hi'])

            gt = make_theory(model)

            # Styling
            CMS.SetExtraText("Preliminary")
            iPos = 0
            canv_name = 'limitplot_compare'
            CMS.SetLumi("60")
            CMS.SetEnergy("13")
            CMS.ResetAdditionalInfo()
            canv = CMS.cmsCanvas(canv_name,200,500,1,1e+06,"M_{#tilde{#chi}^{#pm}_{1}/}#tilde{#chi}^{0}_{2} (GeV)","#sigma#bf{#it{#Beta}} (fb)",square=CMS.kSquare,extraSpace=0.01,iPos=iPos)
            canv.GetListOfPrimitives()[1].SetLabelSize(0.045, "XYZ")
            canv.GetListOfPrimitives()[1].SetTitleSize(0.045, "XYZ")
            canv.GetListOfPrimitives()[1].SetTitleOffset(1.4, "XYZ")
            expect95_1.GetXaxis().SetLabelSize(0.25)
            
            # Draw first set with original colors
            CMS.cmsDraw(expect95_1, "3", fcolor = ROOT.TColor.GetColor("#F5BB54"))
            CMS.cmsDraw(expect68_1, "Same3", fcolor = ROOT.TColor.GetColor("#607641"))
            CMS.cmsDraw(expect50_1, "L", lwidth=2, lcolor=ROOT.kBlack)
            
            # Draw second set with different colors/styles
            CMS.cmsDraw(expect95_2, "Same3", fcolor = ROOT.TColor.GetColor("#9AC2E5"), alpha=0.5)
            CMS.cmsDraw(expect68_2, "Same3", fcolor = ROOT.TColor.GetColor("#6B8FA3"), alpha=0.5)
            CMS.cmsDraw(expect50_2, "LSame", lwidth=2, lcolor=ROOT.kBlue, lstyle=2)
            
            # Draw theory
            CMS.cmsDraw(gt, "L3Same", lwidth=2, lcolor=46, fcolor = 45, alpha=0.5)
            
            # Legend
            leg = CMS.cmsLeg(0.2, 0.90 - 0.05 * 6, 0.9, 0.90, textSize=0.035, columns=2)
            leg.AddEntry(0, '#kern[-0.22]{95% CL upper limits:}', '')
            leg.AddEntry(0, '', '')
            
            # First set
            leg.AddEntry(expect50_1, "{} - Median expected".format(label1),"L")
            leg.AddEntry(expect68_1, "{} - 68% expected".format(label1),"F")
            leg.AddEntry(gt, "#kern[0.1]{#tilde{#chi_{1}^{#pm}}}#kern[0.1]{#tilde{#chi_{2}^{0}}} production","LF")
            leg.AddEntry(expect95_1, "{} - 95% expected".format(label1),"F")
            
            # Second set
            leg.AddEntry(expect50_2, "{} - Median expected".format(label2),"L")
            leg.AddEntry(expect68_2, "{} - 68% expected".format(label2),"F")
            leg.AddEntry(0, "", "")
            leg.AddEntry(expect95_2, "{} - 95% expected".format(label2),"F")
            
            canv.SetLogy()
            sig_text = write(42, 0.04, 0.20, 0.255, "#tilde{#chi_{2}^{0}} #rightarrow f#bar{f}#kern[0.1]{#tilde{#chi}^{0}_{1}}")
            mass_or_tau_text = write(42, 0.04, 0.20, 0.200, "#Delta m = {} GeV, c#tau = {} mm".format(dm,ct.replace('p','.')))
            
            CMS.SaveCanvas(canv,os.path.join(output,'limit1d_compare_mass_dm{}_ct{}.pdf'.format(dm,ct)),close=False)
            CMS.SaveCanvas(canv,os.path.join(output,'limit1d_compare_mass_dm{}_ct{}.png'.format(dm,ct)))


# =============================================================================
# Main execution
# =============================================================================
if __name__ == "__main__":
    # Configuration
    model = 'C1N2'
    
    # Define your two input folders here
    path1 = '/users/ang.li/public/SoftDV/Combine/CMSSW_14_1_0_pre4/src/HiggsAnalysis/CombinedLimit/combine_run3/limit_cards_without0'  # First folder
    path2 = '/users/ang.li/public/SoftDV/Combine/CMSSW_14_1_0_pre4/src/HiggsAnalysis/CombinedLimit/combine_run3/limit_cards_with0'     # Second folder (change this to your second folder name)
    
    # Define labels for the legend
    label1 = "Without 0"  # Label for first set
    label2 = "With 0"     # Label for second set
    
    # Output folder
    output = 'limit_comparison'
    
    # Run comparison plots
    print("Creating comparison plots for ctau scans...")
    make_1dplot_ctau_compare(path1, path2, label1, label2)
    
    #print("Creating comparison plots for mass scans...")
    #make_1dplot_mass_compare(path1, path2, label1, label2)
    
    print("Done! Plots saved in '{}'".format(output))
