import warnings
warnings.filterwarnings('ignore')  # must be before numpy

import os
import argparse
import ctypes
import math
import ROOT
import warnings
import scipy.stats as st
from uncertainties import ufloat

def getEvts(file, hist2d, xBounds, yBounds):
    """
    Read ROOT file `file` and extract integrals with uncertainties for each named histogram in `hist2d`.
    Returns a dict mapping region_key -> dict of subregions 'A','B','C','D' -> ufloat(count, error).
    """
    print('DEBUG: ', file)
    f = ROOT.TFile.Open(file)
    out_d = {}
    boundaries_d = {}
    

    for key, hist_name in hist2d.items():
        hist = f.Get(hist_name)
        if not hist:
            raise ValueError(f"Histogram '{hist_name}' not found in file {file}")

        nbins_x = hist.GetXaxis().GetNbins()
        nbins_y = hist.GetYaxis().GetNbins()

        subregions = {}
        for i in range(len(xBounds) + 1):
            x_lo = 0 if i == 0 else hist.GetXaxis().FindBin(xBounds[i-1])
            x_hi = nbins_x + 1 if i == len(xBounds) else hist.GetXaxis().FindBin(xBounds[i]) - 1

            for j in range(len(yBounds) + 1):
                y_lo = 0 if j == 0 else hist.GetYaxis().FindBin(yBounds[j-1])
                y_hi = nbins_y + 1 if j == len(yBounds) else hist.GetYaxis().FindBin(yBounds[j]) - 1

                subregions[f"{i}_{j}"] = (x_lo, x_hi, y_lo, y_hi)

        # DEBUG
        #----------------------------------------
        for k, v in subregions.items():
            x_lo, x_hi = (hist.GetXaxis().GetBinLowEdge(v[0]),
                          hist.GetXaxis().GetBinUpEdge(v[1]))
            y_lo, y_hi = (hist.GetYaxis().GetBinLowEdge(v[2]),
                          hist.GetYaxis().GetBinUpEdge(v[3]))
        
            # widths: name 14, bins 20, each edge 9 (includes sign & dot)
            print(f"{'Subregion ' + k + ':':14} "
                f"({v[0]:3d}, {v[1]:3d}, {v[2]:3d}, {v[3]:3d})".ljust(20),
                f"x: {x_lo:9.3f} -- {x_hi:9.3f}, "
                f"y: {y_lo:9.3f} -- {y_hi:9.3f}")
        print()
        # ----------------------------------------

        boundaries_d[key] = {}
        nevt = {}
        for sub, (xmin, xmax, ymin, ymax) in subregions.items():
            x_lo = hist.GetXaxis().GetBinLowEdge(xmin)
            x_hi = hist.GetXaxis().GetBinUpEdge(xmax)
            y_lo = hist.GetYaxis().GetBinLowEdge(ymin)
            y_hi = hist.GetYaxis().GetBinUpEdge(ymax)

            boundaries_d[key][sub] = (x_lo, x_hi, y_lo, y_hi)

            err = ctypes.c_double(0)
            cnt = hist.IntegralAndError(xmin, xmax, ymin, ymax, err)
            nevt[sub] = ufloat(cnt, err.value)
            out_d[key] = nevt
    
    return out_d, boundaries_d

def predictA(devt, plane, region_map):
    """
    Compute predicted yield for `plane` in subregion `region`.
    Uses LP_evt -> CP_evt transfer factors, with special formula for TP_evt.
    """
    devt_copy = devt.copy()

    assert len(region_map) == 4, "regions must contain exactly 4 subregions"
    f = devt_copy[plane][region_map['C']] / devt_copy[plane][region_map['D']]
    A_pred = devt_copy[plane][region_map['B']] * f

    devt_copy[plane][region_map['A'] + '_pred'] = A_pred
    return devt_copy

def print_ABCD_table(devt, ABCD_map, form='LaTeX'):
    if form.lower() == 'latex'.lower():
        print("\nLaTeX table:")
        print("-"*80)
        print(r"\begin{table}[htbp!]")
        print(r"    \centering")
        print(r"    \begin{tabular}{l c c c c}")
        print(r"    \hline")
        print(r"Search plane  & A & B & C & D   \\")
        print(r"    \hline")

        for key, sub_dict in devt.items():
            key_formatted = key.replace('_', ' ')
            print(f"    {key_formatted} obs & "
                    f"{sub_dict[ABCD_map['A']].n:.2f} $\pm$ {sub_dict[ABCD_map['A']].s:.2f} & "
                    f"{sub_dict[ABCD_map['B']].n:.2f} $\pm$ {sub_dict[ABCD_map['B']].s:.2f} & "
                    f"{sub_dict[ABCD_map['C']].n:.2f} $\pm$ {sub_dict[ABCD_map['C']].s:.2f} & "
                    f"{sub_dict[ABCD_map['D']].n:.2f} $\pm$ {sub_dict[ABCD_map['D']].s:.2f} \\\\")
            print(r"    \hline")
            print(f"    {key_formatted} pred & "
                    f"{sub_dict[ABCD_map['A'] + '_pred'].n:.2f} $\pm$ {sub_dict[ABCD_map['A'] + '_pred'].s:.2f} & "
                    f"--- & "
                    f"--- & "
                    f"--- \\\\")
            print("\end{tabular}")
            print("\caption{Event yield}")
            print("\label{tab:evt_yield}")
            print("\end{table}")
            print("-"*80)

def print_prediction_results(devt, ABCD_map):
    print(f"Predicted A: {devt[plane][ABCD_map['A'] + '_pred'].n:.3f} ± {devt[plane][ABCD_map['A'] + '_pred'].s:.3f}")
    print(f"Observed  A: {devt[plane][ABCD_map['A']].n:.3f} ± {devt[plane][ABCD_map['A']].s:.3f}")

    pull_nom   = devt[plane][ABCD_map['A']].n - devt[plane][ABCD_map['A'] + '_pred'].n
    pull_denom = math.sqrt(devt[plane][ABCD_map['A']].s ** 2 + devt[plane][ABCD_map['A'] + '_pred'].s ** 2)
    pull = pull_nom / pull_denom if pull_denom != 0 else float('inf')
    print(f"Pull      A: {pull:.3f}") # Z-score of the difference.
    
    CL = abs(st.norm.cdf(pull) -  st.norm.cdf(-pull)) * 100
    print(f"Within CL:   {CL:.2f}%")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process ROOT histograms in a directory")
    parser.add_argument('--input_dir', required=True,
                        help='Directory containing .root files')
    parser.add_argument('-x', '--xBounds', nargs='+', type=float, default=700,
                        help='MET cut value (default: 700)')
    parser.add_argument('-y', '--yBounds', nargs='+', type=float, default=0.90,
                        help='ML cut value (default: 0.90)')
    parser.add_argument('-2x2', '--ABCD', action="store_true",
                        help='Enable 2x2 regions for ABCD prediction')
    args = parser.parse_args()

    print('args: ', args)

    file = os.path.join(args.input_dir, 'all_2018_hist.root')

    # Map our region keys to the actual histogram names in the ROOT files
    hist2d = {
        'all_evt': 'all_evt/MET_pt_corr_vs_Max_vtx_PART_338_epoch_6',
    }

    devt, boundaries = getEvts(file, hist2d, args.xBounds, args.yBounds)
    # print(devt)
    for plane, sub_dict in devt.items():
        print(f"{plane}:")
        for sub, count in sub_dict.items():
            print(f"  {sub}: {count.n:.2f} ± {count.s:.2f}")

    
        if args.ABCD:
            if len(args.xBounds) == 1 and len(args.yBounds) == 1:
                ABCD_map = {
                    'A':'1_1',
                    'B':'0_1',
                    'C':'1_0',
                    'D':'0_0'
                }
            elif (len(args.xBounds) == 2 and len(args.yBounds) == 3) or \
                 (len(args.xBounds) == 3 and len(args.yBounds) == 3):
                ABCD_map = {
                    'A':'2_2',
                    'B':'1_2',
                    'C':'2_1',
                    'D':'1_1'
                }
            print()
            print('A: ', boundaries[plane][ABCD_map['A']])
            print('B: ', boundaries[plane][ABCD_map['B']])
            print('C: ', boundaries[plane][ABCD_map['C']])
            print('D: ', boundaries[plane][ABCD_map['D']])
            print()

            devt = predictA(devt, plane, ABCD_map)
            
            print_prediction_results(devt, ABCD_map)
            print_ABCD_table(devt, ABCD_map, form='LaTeX')