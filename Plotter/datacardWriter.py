import ROOT

import numpy as np
import click
import time
import math
import os
import matplotlib.pyplot as plt

# from HiggsAnalysis.CombinedLimit.DatacardParser import *
# from HiggsAnalysis.CombinedLimit.ModelTools import *
# from HiggsAnalysis.CombinedLimit.ShapeTools import *
# from HiggsAnalysis.CombinedLimit.PhysicsModel import *

import SoftDisplacedVertices.Samples.Samples as s

from sys import exit
from optparse import OptionParser

### data loading functions ###

def load_histogram_data(process_dict, xLow, yLow, xsplit, ysplit):
    """
    xLow :  MET    lower bound as bin id
    yLow :  LxySig lower bound as bin id

    xsplit : MET    lower bound of signal region as bin id
    ysplit : LxySig lower bound of signal region as bin id
    """
    count_dict = {}
    error_dict = {}
    for name in process_dict.keys():
        root_file = ROOT.TFile(process_dict[name], "READ")
        histogram = root_file.Get("SP_evt").Get("MET_pt_vs_SPMaxLxySig")


        counts, errors = calculate_yields(histogram, xLow, yLow, xsplit, ysplit)
        count_dict[name] = counts
        error_dict[name] = errors

    return count_dict, error_dict

def calculate_yields(histogram, xLow, yLow, xsplit, ysplit):
    """
    Returns
    -------
    counts : dict (keys are regions)
    errors : dict (keys are regions)
    """
    counts = {}
    errors = {}
    region_dict = { "A": [xsplit, histogram.GetNbinsX() + 1, ysplit, histogram.GetNbinsY() + 1],
                    "B": [xLow, xsplit - 1, ysplit, histogram.GetNbinsY() + 1],
                    "C": [xsplit, histogram.GetNbinsX() + 1, yLow, ysplit - 1],
                    "D": [xLow, xsplit - 1, yLow, ysplit - 1] }

    for region, splits in region_dict.items():
        count = histogram.Integral(int(splits[0]), int(splits[1]), int(splits[2]), int(splits[3]))
        counts[region] = count
        if count == 0:
            errors[region] = 0
            continue
        squared_error = 0.0
        for i in range(splits[0], splits[1]):
            for j in range(splits[2], splits[3]):
                squared_error += histogram.GetBinError(i, j) * histogram.GetBinError(i, j)
        errors[region] = squared_error
    return counts, errors


def calc_yields(sampleDict, histdir, histname, debug):
    if debug:
        print('signal samples:')
        for sample in flatten_list(sampleDict['sig']):
            print(sample.name)
        print()
        print('background samples:')
        for sample in flatten_list(sampleDict['bkg']):
            print(sample.name)
        
    sampleDict['sig'] = flatten_list(sampleDict['sig'])
    sampleDict['bkg'] = flatten_list(sampleDict['bkg'])

    region_name, histname = histname.split('.')


    MET_boundary    = None
    LxySig_boundary = None

    for sig in sampleDict['sig']:
        sigFile = ROOT.TFile(os.path.join(histdir, f"{sig.name}_hist.root"))
        sigHist = getattr(getattr(sigFile, region_name),histname).Clone()

        if MET_boundary is None:
            # Set the boundaries only once.
            MET_lo  = sigHist.GetXaxis().GetBinLowEdge(1)
            MET_up  = sigHist.GetXaxis().GetBinLowEdge(sigHist.GetNbinsX() + 1)
            MET_inc = sigHist.GetXaxis().GetBinLowEdge(2) - sigHist.GetXaxis().GetBinLowEdge(1)
            MET_boundary = np.arange(MET_lo, MET_up + MET_inc, MET_inc)

            LxySig_lo  = sigHist.GetYaxis().GetBinLowEdge(1)
            LxySig_up  = sigHist.GetYaxis().GetBinLowEdge(sigHist.GetNbinsY() + 1)
            LxySig_inc = sigHist.GetYaxis().GetBinLowEdge(2) - sigHist.GetYaxis().GetBinLowEdge(1)
            LxySig_boundary = np.arange(LxySig_lo, LxySig_up + LxySig_inc, LxySig_inc)

        




    


### workspace writing functions ###

def write_workspace_file(fileOut, count_dict, error_dict):

    parser = OptionParser()
    addDatacardParserOptions(parser)
    options,args = parser.parse_args()
    options.bin = True # make a binary workspace

    DC = Datacard()
    MB = None

    ############## Setup the datacard (must be filled in) ###########################

    DC.bins =        ['A', 'B', 'C', 'D'] # <class 'list'>

    DC.obs =         {}

    DC.processes =   []

    DC.signals =     []

    DC.isSignal =    {}

    DC.keyline =     []
    for contribution in count_dict:
        DC.processes.append(contribution)
        if "sig" in contribution: DC.signals.append(contribution)
        DC.isSignal[contribution] = "sig" in contribution
        for region in DC.bins:
            DC.keyline.append((region, contribution, "sig" in contribution))

    DC.exp =         {}

    DC.systs =       []
    sigSys =         ('SigSys',  False, 'lnN', [], {})
    sigSysA =        ('SigSysA', False, 'lnN', [], {})
    sigSysB =        ('SigSysB', False, 'lnN', [], {})
    sigSysC =        ('SigSysC', False, 'lnN', [], {})
    sigSysD =        ('SigSysD', False, 'lnN', [], {})
    bkgSys =         ('BkgSys',  False, 'lnN', [], {})
    bkgSysA =        ('BkgSysA', False, 'lnN', [], {})
    bkgSysB =        ('BkgSysB', False, 'lnN', [], {})
    bkgSysC =        ('BkgSysC', False, 'lnN', [], {})
    bkgSysD =        ('BkgSysD', False, 'lnN', [], {})
    DC.rateParams =  {}
    for region in DC.bins:
        if region == "A":
            DC.obs[region] = count_dict["bkg"]["B"] * count_dict["bkg"]["C"] / count_dict["bkg"]["D"]
        else:
            DC.obs[region] = count_dict["bkg"][region]
        DC.exp[region] = {}
        sigSys[4][region] = {}
        sigSysA[4][region] = {}
        sigSysB[4][region] = {}
        sigSysC[4][region] = {}
        sigSysD[4][region] = {}
        bkgSys[4][region] = {}
        bkgSysA[4][region] = {}
        bkgSysB[4][region] = {}
        bkgSysC[4][region] = {}
        bkgSysD[4][region] = {}
        for contribution in count_dict:
            if "sig" in contribution: 
                DC.exp[region][contribution] = count_dict[contribution][region]
                sigSys[4][region][contribution] = 1.2
                bkgSys[4][region][contribution] = 0.0
                if region == "A":
                    sigSysA[4][region][contribution] = error_dict[contribution][region]
                    sigSysB[4][region][contribution] = 0.0
                    sigSysC[4][region][contribution] = 0.0
                    sigSysD[4][region][contribution] = 0.0
                if region == "B":
                    sigSysA[4][region][contribution] = 0.0
                    sigSysB[4][region][contribution] = error_dict[contribution][region]
                    sigSysC[4][region][contribution] = 0.0
                    sigSysD[4][region][contribution] = 0.0
                if region == "C":
                    sigSysA[4][region][contribution] = 0.0
                    sigSysB[4][region][contribution] = 0.0
                    sigSysC[4][region][contribution] = error_dict[contribution][region]
                    sigSysD[4][region][contribution] = 0.0
                if region == "D":
                    sigSysA[4][region][contribution] = 0.0
                    sigSysB[4][region][contribution] = 0.0
                    sigSysC[4][region][contribution] = 0.0
                    sigSysD[4][region][contribution] = error_dict[contribution][region]
                bkgSysA[4][region][contribution] = 0.0
                bkgSysB[4][region][contribution] = 0.0
                bkgSysC[4][region][contribution] = 0.0
                bkgSysD[4][region][contribution] = 0.0
            else: 
                DC.exp[region][contribution] = 1.0
                sigSys[4][region][contribution] = 0.0
                if region == "A": bkgSys[4][region][contribution] = 1.2
                else: bkgSys[4][region][contribution] = 0.0
                key = region + "AND" + contribution
                if region == "A":
                    DC.rateParams[key] = [[['alpha', '(@0*@1/@2)', 'beta,gamma,delta', 1], '']]
                    bkgSysA[4][region][contribution] = error_dict[contribution][region]
                    bkgSysB[4][region][contribution] = 0.0
                    bkgSysC[4][region][contribution] = 0.0
                    bkgSysD[4][region][contribution] = 0.0
                if region == "B":
                    DC.rateParams[key] = [[['beta', '{}'.format(count_dict[contribution][region]), 0], '']]
                    bkgSysA[4][region][contribution] = 0.0
                    bkgSysB[4][region][contribution] = error_dict[contribution][region]
                    bkgSysC[4][region][contribution] = 0.0
                    bkgSysD[4][region][contribution] = 0.0
                if region == "C":
                    DC.rateParams[key] = [[['gamma', '{}'.format(count_dict[contribution][region]), 0], '']]
                    bkgSysA[4][region][contribution] = 0.0
                    bkgSysB[4][region][contribution] = 0.0
                    bkgSysC[4][region][contribution] = error_dict[contribution][region]
                    bkgSysD[4][region][contribution] = 0.0
                if region == "D":
                    DC.rateParams[key] = [[['delta', '{}'.format(count_dict[contribution][region]), 0], '']]
                    bkgSysA[4][region][contribution] = 0.0
                    bkgSysB[4][region][contribution] = 0.0
                    bkgSysC[4][region][contribution] = 0.0
                    bkgSysD[4][region][contribution] = error_dict[contribution][region]
                sigSysA[4][region][contribution] = 0.0
                sigSysB[4][region][contribution] = 0.0
                sigSysC[4][region][contribution] = 0.0
                sigSysD[4][region][contribution] = 0.0

    DC.systs.append(sigSys)
    DC.systs.append(sigSysA)
    DC.systs.append(sigSysB)
    DC.systs.append(sigSysC)
    DC.systs.append(sigSysD)
    DC.systs.append(bkgSys)
    DC.systs.append(bkgSysA)
    DC.systs.append(bkgSysB)
    DC.systs.append(bkgSysC)
    DC.systs.append(bkgSysD)

    #print("------------------------------------------------------------------------------")
    #print(DC.obs)
    #print(DC.exp)
    #print(DC.rateParams)
    #print("------------------------------------------------------------------------------")

    DC.shapeMap =    {} # <class 'dict'>
    DC.hasShapes =   False # <class 'bool'>
    DC.flatParamNuisances =  {} # <class 'dict'>
    DC.extArgs =     {} # <class 'dict'>
    DC.rateParamsOrder      =  {'beta', 'delta', 'alpha', 'gamma'} # <class 'set'>
    DC.frozenNuisances      =  set() # <class 'set'>
    DC.systematicsShapeMap =  {} # <class 'dict'>
    DC.systematicsParamMap =  {} # <class 'dict'>
    DC.systIDMap =  {'SigSys': [0], 'BkgSys': [1]} # <class 'dict'>
    DC.nuisanceEditLines    =  [] # <class 'list'>
    DC.binParFlags  =  {} # <class 'dict'>
    DC.groups       =  {} # <class 'dict'>
    DC.discretes    =  [] # <class 'list'>
    DC.pdfnorms     =  {} # <class 'dict'>


    ###### User defined options #############################################

    options.out      = "{}".format(fileOut) + ".root"    # Output workspace name
    options.fileName = "./"                              # Path to input ROOT files
    options.verbose  = "1"                               # Verbosity

    ##########################################################################

    WriteDatacardTxt(DC, fileOut)

    '''
    # UNCOMMENT FOR ROOT FILES

    if DC.hasShapes:
        MB = ShapeBuilder(DC, options)
    else:
        MB = CountingModelBuilder(DC, options)

    # Set physics models
    MB.setPhysics(defaultModel)
    MB.doModel()
    '''

def WriteDatacardTxt(DC, fileOut):
    fileTxt = fileOut + ".txt"
    with open(fileTxt, 'w') as f:
        lines = ['imax {}  number of channels\n'.format(len(DC.bins)), 'jmax {} number of processes -1\n'.format(len(DC.processes) - 1), 'kmax *  number of nuisance parameters (sources of systematical uncertainties)\n']
        f.writelines(lines)
        f.write('-------\n')
        f.write('bin\t\t')
        for i in DC.bins:
            f.write('{}\t'.format(i))
        f.write('\n')
        f.write('observation\t\t')
        for i in DC.bins:
            f.write('{}\t'.format(DC.obs[i]))
        f.write('\n')
        f.write('-------\n')
        lines = ['bin\t\t', 'process\t\t', 'process\t\t', 'rate\t\t']
        for i in DC.keyline:
            #if i[0] != "A" and i[1] == "sig": continue
            lines[0] += ('{}\t'.format(i[0]))
            lines[1] += ('{}\t'.format(i[1]))
            if i[1] == "sig":
                lines[2] += ('0\t')
            else:
                lines[2] += ('1\t')
            lines[3] += '{}\t'.format(DC.exp[i[0]][i[1]])
        lines[0] += '\n'
        lines[1] += '\n'
        lines[2] += '\n'
        lines[3] += '\n'
        f.writelines(lines)
        f.write('-------\n')
        linesSys = []
        j = 0
        
        for i in DC.systs:
            linesSys.append('{} {}\t\t'.format(i[0], i[2]))
            for k in DC.keyline:
                #if k[0] != "A" and k[1] == "sig": continue
                if i[4][k[0]][k[1]] == 0:
                    linesSys[j] += '-\t'
                else:
                    linesSys[j] += '{}\t'.format(i[4][k[0]][k[1]])
            j += 1
        for line in linesSys:
            f.write(line)
            f.write('\n')
        f.write('\n')
        linesRate = []
        for i, j in DC.rateParams.items():
            line = '{} rateParam {} {} {} '.format(j[0][0][0], i.split("AND")[0], i.split("AND")[1], j[0][0][1])
            if '@' in j[0][0][1]:
                line += '{}'.format(j[0][0][2])
            linesRate.append(line)
                
        for line in linesRate:
            f.write(line)
            f.write('\n')

def flatten_list(lst):
    """
    Recursively flattens a nested list.
    If you increase the depth (layers of nested lists) it will fail at some point.
    (i.e. memory stack overflow)
    However reasonable number of nestedness is handled well.
    """
    out_lst = []
    for i in lst:
        if type(i) is list:
            # flatten_list(i)
            out_lst.extend(flatten_list(i))
        else:
            out_lst.append(i)
    return out_lst

def get_region_boundaries(sample, histdir, histname, MET_bound, LxySig_bound):
    """
    Gets the closest bin number and lower edge given an x,y value.
    """
    region_name, histname = histname.split('.')
    histFile = ROOT.TFile(os.path.join(histdir, f"{sample.name}_hist.root"))
    hist = histFile.Get(region_name).Get(histname).Clone()

    xSplit = int(hist.GetXaxis().FindBin(MET_bound))
    ySplit = int(hist.GetYaxis().FindBin(LxySig_bound))

    xSplit_val = hist.GetXaxis().GetBinLowEdge(xSplit)
    ySplit_val = hist.GetYaxis().GetBinLowEdge(ySplit)
    return (xSplit, ySplit, xSplit_val, ySplit_val)

def sum_background_hists(bkgSamples, histdir, histname, debug):
    """
    Sum the histograms in the bkgSamples dictionary.
    """
    region_name, histname = histname.split('.')

    histFile = ROOT.TFile(os.path.join(histdir, f"{bkgSamples[0].name}_hist.root"), "READ")
    hist = histFile.Get(region_name).Get(histname).Clone()
    nbinsx = hist.GetNbinsX()
    nbinsy = hist.GetNbinsY()
    xlo = hist.GetXaxis().GetBinLowEdge(1)
    ylo = hist.GetYaxis().GetBinLowEdge(1)
    xup = hist.GetXaxis().GetBinLowEdge(nbinsx + 1)
    yup = hist.GetYaxis().GetBinLowEdge(nbinsy + 1)
    histFile.Close()
    if debug: print(xlo, xup, nbinsy, ylo, yup)
    all_bkg = ROOT.TH2D('allbkg', 'sum of all bkgs', nbinsx, xlo, xup, nbinsy, ylo, yup)

    for sample in bkgSamples:
        histFile = ROOT.TFile(os.path.join(histdir, f"{sample.name}_hist.root"))
        hist = histFile.Get(region_name).Get(histname).Clone()
        all_bkg.Add(hist)
    return all_bkg

def get_histogram(sample, histdir, histname, debug):
    """
    Detaches the histogram from file.
    Thus you can return it safely via a function

    WARNING: Memory leaks!
    Deleting the histogram is your responsibility

    Ref: https://root-forum.cern.ch/t/get-histogram-and-close-file/18867
    """
    region_name, histname = histname.split('.')

    histFile = ROOT.TFile(os.path.join(histdir, f"{sample.name}_hist.root"), "READ")
    hist = histFile.Get(region_name).Get(histname).Clone()
    hist.SetDirectory(0)
    return hist
        

### main ###
    
@click.command()
@click.option('--sig',         default=None, help='Sample (or list of Sample) to be imported from Samples.py, e.g. stop_2018')
@click.option('--bkg',         default=None, help='Sample (or list of Sample) to be imported from Samples.py, e.g. qcd_2018')
@click.option('--histdir',     default=None, help='Directory of where to find the histogram files.')
@click.option('--histname',    default=None, help='Directory of where to find the histogram files.')
@click.option('--datacarddir', default=None, help='Directory of where to write the datacards.')
@click.option('--debug',       default=False)

def main_cli(sig, bkg, histdir, histname, datacarddir, debug):
    if any(True for arg in (sig, bkg, histdir, histname, datacarddir) if arg is None):
        print('Please fill all the options.')
        print('i.e. sig, bkg, histdir, histname, datacarddir')
        exit()

    if debug:
        s_time = time.time()
        print("Running main...")
        print()

    sampleDict = {
        "bkg" : [getattr(s, bkg)],
        "sig" : [getattr(s, sig)]
    }

    sampleDict['sig'] = flatten_list(sampleDict['sig'])
    sampleDict['bkg'] = flatten_list(sampleDict['bkg'])

    MET_bound = 449
    LxySig_bound = 33.7
    
    sample =  sampleDict['sig'][0]
    splits = get_region_boundaries(sample, histdir, histname, MET_bound, LxySig_bound)
    xSplit, ySplit, xSplit_val, ySplit_val = splits
    
    xlo = 0    # Control region lower boundaries as bin ids (MET)
    ylo = 0    # Control region lower boundaries as bin ids (LxySig)

    
    all_bkg = sum_background_hists(sampleDict['bkg'], histdir, histname, debug)
    bkg_count_dict, bkg_squared_error_dict = calculate_yields(all_bkg, xlo, ylo, xSplit, ySplit)


    # Prepare an error dict as one plus errors.
    # Background needs to be calculated only once.
    bkg_onepluserror_dict = {region : 1+ math.sqrt(squared_error) for region, squared_error in bkg_squared_error_dict.items()}


    count_dict = {}
    error_dict = {}
    for sig in sampleDict['sig']:
        processDict = {}
        count_dict['bkg'] = bkg_count_dict
        error_dict['bkg'] = bkg_onepluserror_dict

        sigHist = get_histogram(sig, histdir, histname, debug)
        sig_count_dict, sig_squared_error_dict = calculate_yields(sigHist, xlo, ylo, xSplit, ySplit)
        del sigHist    # Remember: deleting is your responsibility
        count_dict['sig'] = sig_count_dict
        error_dict['sig'] = sig_squared_error_dict
    
        outTag = f"MC_{sig.name}_{xSplit_val:.3g}_{ySplit_val:.3g}"

        write_workspace_file(outTag, count_dict, error_dict)

        e_time = time.time()
        print('Ellapsed time: {}'.format(e_time - s_time))

if __name__ == "__main__":
    main_cli()