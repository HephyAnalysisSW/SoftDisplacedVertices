import os
import argparse
import ctypes
import math
import ROOT
from uncertainties import ufloat


def getEvts(fn, hist_map, metcut):
    """
    Read ROOT file `fn` and extract integrals with uncertainties for each named histogram in `hist_map`.
    Returns a dict mapping region_key -> dict of subregions 'A','B','C','D' -> ufloat(count, error).
    """
    print('DEBUG: ', fn)
    f = ROOT.TFile.Open(fn)
    out_d = {}

    # assume 2D histograms with x-axis=MET, y-axis=LxySig
    for key, hist_name in hist_map.items():
        hist = f.Get(hist_name)
        if not hist:
            raise ValueError(f"Histogram '{hist_name}' not found in file {fn}")

        nbins_x = hist.GetXaxis().GetNbins()
        # determine bin corresponding to metcut
        xcut = hist.GetXaxis().FindBin(metcut)
        # choose a fixed y-axis cut (e.g., bin for 20)
        # you may parameterize this if needed
        ycut = hist.GetYaxis().FindBin(20)

        # define subregions in terms of axis ranges
        subregions = {
            'A': (xcut, nbins_x+1, ycut, nbins_x),   # high MET, high Sig
            'B': (1, xcut-1, ycut, nbins_x+1),       # low MET, high Sig
            'C': (xcut, nbins_x+1, 1, ycut-1),       # high MET, low Sig
            'D': (1, xcut-1, 1, ycut-1),           # low MET, low Sig
        }
        nevt = {}
        for sub, (xmin, xmax, ymin, ymax) in subregions.items():
            err = ctypes.c_double(0)
            cnt = hist.IntegralAndError(xmin, xmax, ymin, ymax, err)
            nevt[sub] = ufloat(cnt, err.value)

        out_d[key] = nevt
    return out_d


def predict(devt, plane, region):
    """
    Compute predicted yield for `plane` in subregion `region`.
    Uses LP_evt -> CP_evt transfer factors, with special formula for TP_evt.
    """
    # choose transfer factor f from loose vs control
    if region in ['C', 'D']:
        f = devt['LP_evt']['D'] / devt['CP_evt']['D']
    else:
        f = devt['LP_evt']['B'] / devt['CP_evt']['B']

    
    if plane == 'TP_evt':
        f = f * f * f / (1 - f)
    elif plane == 'MP_evt':
        f = f * f

    return devt['CP_evt'][region] * f


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process ROOT histograms in a directory")
    parser.add_argument('--input_dir', required=True,
                        help='Directory containing .root files')
    parser.add_argument('--metcut', type=float, default=700,
                        help='MET cut value (default: 700)')
    args = parser.parse_args()

    # Map our region keys to the actual histogram names in the ROOT files
    hist_map = {
        'TP_evt': 'TP_evt/MET_pt_corr_vs_TP_MaxLxySig',
        'MP_evt': 'MP_evt/MET_pt_corr_vs_MP_MaxLxySig',
        'LP_evt': 'LP_evt/MET_pt_corr_vs_LP_MaxLxySig',
        'CP_evt': 'CP_evt/MET_pt_corr_vs_CP_MaxLxySig',
    }

    filenames = [
        'met_2023_hist.root'
    ]
    files = [os.path.join(args.input_dir, file) for file in filenames]
    # Loop over all root files in the input directory
    for filepath in files:
        assert filepath.endswith('.root'), "File is not a .root file"
        devts = getEvts(filepath, hist_map, args.metcut)

        # for the eye
        # ------------------------------------------------------------------------
        print("="*40)
        print(f"File: {filepath}")
        print("Raw counts:")
        for plane, counts in devts.items():
            print(f" {plane}: " + ", ".join(f"{sub}={counts[sub]:.02fL}" for sub in ['A','B','C','D']))

        print("\nPredictions:")
        for plane in ['TP_evt', 'MP_evt', 'LP_evt']:
            preds = {sub: predict(devts, plane, sub) for sub in ['A','B','C','D']}
            print(f" {plane}: " + ", ".join(f"{sub}={preds[sub]:.02fL}" for sub in ['A','B','C','D']))
        print('\n\n')
        print('='*80)

        # LaTeX print
        # ------------------------------------------------------------------------
        print(r"\begin{table}[htbp!]")
        print(r"    \centering")
        print(r"    \begin{tabular}{l c c c c}")
        print(r"    \hline")
        print(r"Search plane  & A & B & C & D   \\")
        print(r"    \hline")

        rows = [
            ('TP_evt', r"Tight plane ($\ngoodtrack \geq 3$)", False),
            ('TP_evt', 'Prediction', True),
            ('MP_evt', r"Medium plane ($\ngoodtrack = 2$)", False),
            ('MP_evt', 'Prediction', True),
            ('LP_evt', r"Loose plane ($\ngoodtrack = 1$)", False),
            ('LP_evt', 'Prediction', True),
            ('CP_evt', r"Control plane ($\ngoodtrack = 0$)", False),
        ]

        for key, label, is_pred in rows:
            if is_pred:
                counts = {sub: predict(devts, key, sub) for sub in ['A','B','C','D']}
            else:
                counts = devts[key]
            row_vals = [f"${counts[sub]:.2fL}$" for sub in ['A','B','C','D']]
            print(f"{label} & {' & '.join(row_vals)} \\\\")

        print(r"    \hline")
        print(r"    \end{tabular}")
        print(r"    \caption{Event yield of data in the nominal search planes.}")
        print(r"    \label{tab:evt_yield}")
        print(r"\end{table}")

