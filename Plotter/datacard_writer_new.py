import ROOT

import click
import time
import math

import matplotlib.pyplot as plt

from HiggsAnalysis.CombinedLimit.DatacardParser import *
from HiggsAnalysis.CombinedLimit.ModelTools import *
from HiggsAnalysis.CombinedLimit.ShapeTools import *
from HiggsAnalysis.CombinedLimit.PhysicsModel import *

from sys import exit
from optparse import OptionParser

### data loading functions ###

def load_histogram_data(process_dict, xLow, yLow, xsplit, ysplit):
    count_dict = {}
    error_dict = {}
    for name in process_dict.keys():
        count_dict[name] = {}
        error_dict[name] = {}
        root_file = ROOT.TFile(process_dict[name], "READ")
        histogram = root_file.Get("hist_all_sv")

        '''
        #print(histogram.GetNbinsX())
        print(xsplit)
        print(histogram.GetXaxis().GetBinLowEdge(xsplit))
        print(ysplit)
        print(histogram.GetYaxis().GetBinLowEdge(ysplit))
        '''

        region_dict = { "A": [xsplit, histogram.GetNbinsX() + 1, ysplit, histogram.GetNbinsY() + 1],
                        "B": [xLow, xsplit - 1, ysplit, histogram.GetNbinsY() + 1],
                        "C": [xsplit, histogram.GetNbinsX() + 1, yLow, ysplit - 1],
                        "D": [xLow, xsplit - 1, yLow, ysplit - 1] }

        for region, splits in region_dict.items():
            count = histogram.Integral(int(splits[0]), int(splits[1]), int(splits[2]), int(splits[3]))
            count_dict[name][region] = count
            if count == 0:
                error_dict[name][region] = 0
                continue
            total_error = 0.0
            for i in range(splits[0], splits[1]):
                for j in range(splits[2], splits[3]):
                    total_error += histogram.GetBinError(i, j) * histogram.GetBinError(i, j)
            total_error = math.sqrt(total_error)
            error_dict[name][region] = 1 + total_error / count

    return count_dict, error_dict

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
        

### main ###
    
@click.command()
@click.argument('bkg')
@click.argument('sig')
@click.argument('met')
@click.argument('lxy')

def main_cli(bkg, sig, met, lxy):
    s_time = time.time()
    print("Running main...")
    print('')

    lumi = "59p8"
    version = "v5"

    bkg_path = "/users/felix.lang/private/master_thesis/plotter/SoftDisplacedVertices/{}_AllRegions_{}_{}.root".format(bkg, lumi, version)
    sig_path = "/users/felix.lang/private/master_thesis/plotter/SoftDisplacedVertices/{}_AllRegions_{}_{}.root".format(sig, lumi, version)

    out = "{}_{}_{}_{}".format(bkg, sig, lumi, version)

    process_dict = { "bkg": bkg_path,
                     "sig": sig_path }


    xStart = 200
    xEnd = 1200
    yStart = 0
    yEnd = 200
    nBinsX = 200
    nBinsY = 200

    x = int(met)
    y = int(lxy)

    xSplit = int(nBinsX * (x - xStart) / (xEnd - xStart) + 1)
    ySplit = int(nBinsY * (y - yStart) / (yEnd - yStart) + 1)

    print(xSplit)
    print(ySplit)
    print(process_dict)
    count_dict, error_dict = load_histogram_data(process_dict, 0, 0, xSplit, ySplit)
    outTag = out + "_{}_{}".format(x, y)

    print(count_dict)

    write_workspace_file(outTag, count_dict, error_dict)

    e_time = time.time()
    print('Ellapsed time: {}'.format(e_time - s_time))

if __name__ == "__main__":
    main_cli()