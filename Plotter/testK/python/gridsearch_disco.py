import os
from warnings import simplefilter
simplefilter(action="ignore", category=FutureWarning)
simplefilter(action="ignore", category=UserWarning)


import time
import math

import pickle
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
simplefilter(action="ignore", category=pd.errors.PerformanceWarning)
import matplotlib.pyplot as plt
import seaborn as sns


from uncertainties import ufloat
from ctypes import c_double

import ROOT
ROOT.EnableImplicitMT()    # Tells ROOT to go parallel


def open_tfiles(workdir, tdir, histname, sigtag):

    

    bkg_dir = os.path.join(workdir, 'bkg')
    sig_dir = os.path.join(workdir, 'sig')



    sig_file = ROOT.TFile(os.path.join(sig_dir, f"{sigtag}_hist.root"), 'READ')
    sig_dir  = getattr(sig_file, tdir)
    sig_hist = getattr(sig_dir, histname).Clone()


    bkg_file = ROOT.TFile(os.path.join(bkg_dir, f"all_2018_hist.root"), 'READ')
    bkg_dir  = getattr(bkg_file, tdir)
    bkg_hist = getattr(bkg_dir, histname).Clone()

    tfiles = dict(sig = sig_file, bkg = bkg_file)
    th2s   = dict(sig = sig_hist, bkg = bkg_hist)

    return tfiles, th2s

def close_tfiles(tfiles):
    for tfile in tfiles:
        tfiles[tfile].Close()

def calc_unc(region, region_unc, x_boundary, y_boundary, tables, noncl=None):
    """
    Content:
    - 20% systematic uncertainty on the background prediction
    - non-closure uncertainty from data-driven closure test
    - statistical uncertainty on the background prediction

    All added in quadratures.
    """
    unc1 = tables[region].loc[x_boundary, y_boundary] * 0.20
    unc2 = tables[region].loc[x_boundary, y_boundary] * noncl if noncl else 0.
    unc3 = tables[region_unc].loc[x_boundary, y_boundary]
    total_unc = np.sqrt(unc1**2 + unc2**2 + unc3**2)
    return total_unc

def makeTables(
        xedges: np.ndarray,
        yedges: np.ndarray,
        bkg_hist: ROOT.TH2,
        sig_hist: ROOT.TH2,
        x_loCut: float = 0.0,
        y_loCut: float = 0.0,
        sigScale: float = 1.0,
        bkgScale: float = 1.0,
):
    x_step = xedges[1] - xedges[0]
    y_step = yedges[1] - yedges[0]
    empty_df = pd.DataFrame(index=np.arange(xedges[0], xedges[-1]+x_step, x_step),
                            columns=np.arange(yedges[0], yedges[-1]+y_step, y_step),
                            dtype= float)

    # Create empty tables
    tableNames = ['sig_NA', 'sig_NB', 'sig_NC', 'sig_ND',
                  'bkg_NA', 'bkg_NB', 'bkg_NC', 'bkg_ND',
                  'sig_NA_unc', 'sig_NB_unc', 'sig_NC_unc', 'sig_ND_unc',
                  'bkg_NA_unc', 'bkg_NB_unc', 'bkg_NC_unc', 'bkg_ND_unc',
                  'Z_A', 'Z_B', 'Z_C', 'Z_D',
                  'Z_noncl_A', 'Z_noncl_B', 'Z_noncl_C', 'Z_noncl_D',
                  'Z_noncl_plus1s_A', 'Z_noncl_plus1s_B', 'Z_noncl_plus1s_C', 'Z_noncl_plus1s_D',
                  'noncl', 'noncl_unc',
                ]
    tables = dict()
    for name in tableNames:
        tables[name] = empty_df.copy()
     
    for x_boundary in xedges:
        for y_boundary in yedges:
            x_lo    = bkg_hist.GetXaxis().FindBin(x_loCut)
            x_up    = bkg_hist.GetNbinsX()+1
            x_bound = bkg_hist.GetXaxis().FindBin(x_boundary)

            y_lo    = bkg_hist.GetYaxis().FindBin(y_loCut)
            y_up    = bkg_hist.GetNbinsY()+1
            y_bound = bkg_hist.GetYaxis().FindBin(y_boundary)


            # ------------ Backgrounds --------------
            c_err = c_double(0.0)
            NA = ufloat(bkg_hist.IntegralAndError(x_bound,    x_up,       y_bound,    y_up,          c_err), c_err.value) * bkgScale
            NB = ufloat(bkg_hist.IntegralAndError(x_lo,       x_bound-1,  y_bound,    y_up,          c_err), c_err.value) * bkgScale
            NC = ufloat(bkg_hist.IntegralAndError(x_bound,    x_up,       y_lo,      y_bound-1,      c_err), c_err.value) * bkgScale
            ND = ufloat(bkg_hist.IntegralAndError(x_lo,       x_bound-1,  y_lo,      y_bound-1,      c_err), c_err.value) * bkgScale

            num   = NB * NC
            denom = NA * ND
            noncl = np.abs(1- num/denom) if denom.n > 0 else ufloat(1e-5, 1e-5)

            eps = 5e-1

            tables['bkg_NA'].loc[x_boundary, y_boundary] = max(eps, NA.n) # max: in case there are negative bins
            tables['bkg_NB'].loc[x_boundary, y_boundary] = max(eps, NB.n)
            tables['bkg_NC'].loc[x_boundary, y_boundary] = max(eps, NC.n)
            tables['bkg_ND'].loc[x_boundary, y_boundary] = max(eps, ND.n)

            tables['bkg_NA_unc'].loc[x_boundary, y_boundary] = max(eps, NA.s)
            tables['bkg_NB_unc'].loc[x_boundary, y_boundary] = max(eps, NB.s)
            tables['bkg_NC_unc'].loc[x_boundary, y_boundary] = max(eps, NC.s)
            tables['bkg_ND_unc'].loc[x_boundary, y_boundary] = max(eps, ND.s)

            tables['noncl'].loc[x_boundary, y_boundary]     = noncl.n
            tables['noncl_unc'].loc[x_boundary, y_boundary] = noncl.s
            

            # ------------ Signals --------------
            c_err = c_double(0.0)
            NA = ufloat(sig_hist.IntegralAndError(x_bound,    x_up,       y_bound,    y_up,          c_err), c_err.value) * sigScale
            NB = ufloat(sig_hist.IntegralAndError(x_lo,       x_bound-1,  y_bound,    y_up,          c_err), c_err.value) * sigScale
            NC = ufloat(sig_hist.IntegralAndError(x_bound,    x_up,       y_lo,      y_bound-1,      c_err), c_err.value) * sigScale
            ND = ufloat(sig_hist.IntegralAndError(x_lo,       x_bound-1,  y_lo,      y_bound-1,      c_err), c_err.value) * sigScale

            eps = 5e-1

            tables['sig_NA'].loc[x_boundary, y_boundary] = max(eps, NA.n) # max: in case there are negative bins
            tables['sig_NB'].loc[x_boundary, y_boundary] = max(eps, NB.n)
            tables['sig_NC'].loc[x_boundary, y_boundary] = max(eps, NC.n)
            tables['sig_ND'].loc[x_boundary, y_boundary] = max(eps, ND.n)

            tables['sig_NA_unc'].loc[x_boundary, y_boundary] = max(eps, NA.s)
            tables['sig_NB_unc'].loc[x_boundary, y_boundary] = max(eps, NB.s)
            tables['sig_NC_unc'].loc[x_boundary, y_boundary] = max(eps, NC.s)
            tables['sig_ND_unc'].loc[x_boundary, y_boundary] = max(eps, ND.s)

            # ------------ Significance --------------

            Z_A      = ROOT.RooStats.AsimovSignificance(tables['sig_NA'].loc[x_boundary, y_boundary],
                                                         tables['bkg_NA'].loc[x_boundary, y_boundary],
                                                         calc_unc('bkg_NA', 'bkg_NA_unc', x_boundary, y_boundary, tables))
            Z_B      = ROOT.RooStats.AsimovSignificance(tables['sig_NB'].loc[x_boundary, y_boundary],
                                                         tables['bkg_NB'].loc[x_boundary, y_boundary],
                                                         calc_unc('bkg_NB', 'bkg_NB_unc', x_boundary, y_boundary, tables))
            Z_C      = ROOT.RooStats.AsimovSignificance(tables['sig_NC'].loc[x_boundary, y_boundary],
                                                         tables['bkg_NC'].loc[x_boundary, y_boundary],
                                                         calc_unc('bkg_NC', 'bkg_NC_unc', x_boundary, y_boundary, tables))
            Z_D      = ROOT.RooStats.AsimovSignificance(tables['sig_ND'].loc[x_boundary, y_boundary],
                                                         tables['bkg_ND'].loc[x_boundary, y_boundary],
                                                         calc_unc('bkg_ND', 'bkg_ND_unc', x_boundary, y_boundary, tables))

            
            tables['Z_A'].loc[x_boundary, y_boundary] = Z_A
            tables['Z_B'].loc[x_boundary, y_boundary] = Z_B
            tables['Z_C'].loc[x_boundary, y_boundary] = Z_C
            tables['Z_D'].loc[x_boundary, y_boundary] = Z_D

            # ------------ Significance with non-clsoure uncertainty --------------

            Z_A      = ROOT.RooStats.AsimovSignificance(tables['sig_NA'].loc[x_boundary, y_boundary],
                                                         tables['bkg_NA'].loc[x_boundary, y_boundary],
                                                         calc_unc('bkg_NA', 'bkg_NA_unc', x_boundary, y_boundary, tables, noncl.n))
            Z_B      = ROOT.RooStats.AsimovSignificance(tables['sig_NB'].loc[x_boundary, y_boundary],
                                                         tables['bkg_NB'].loc[x_boundary, y_boundary],
                                                         calc_unc('bkg_NB', 'bkg_NB_unc', x_boundary, y_boundary, tables, noncl.n))
            Z_C      = ROOT.RooStats.AsimovSignificance(tables['sig_NC'].loc[x_boundary, y_boundary],
                                                         tables['bkg_NC'].loc[x_boundary, y_boundary],
                                                         calc_unc('bkg_NC', 'bkg_NC_unc', x_boundary, y_boundary, tables, noncl.n))
            Z_D      = ROOT.RooStats.AsimovSignificance(tables['sig_ND'].loc[x_boundary, y_boundary],
                                                         tables['bkg_ND'].loc[x_boundary, y_boundary],
                                                         calc_unc('bkg_ND', 'bkg_ND_unc', x_boundary, y_boundary, tables, noncl.n))

            
            tables['Z_noncl_A'].loc[x_boundary, y_boundary] = Z_A
            tables['Z_noncl_B'].loc[x_boundary, y_boundary] = Z_B
            tables['Z_noncl_C'].loc[x_boundary, y_boundary] = Z_C
            tables['Z_noncl_D'].loc[x_boundary, y_boundary] = Z_D

            # ------------ Significance with non-clsoure uncertainty plus one sigma unc. -------

            Z_A      = ROOT.RooStats.AsimovSignificance(tables['sig_NA'].loc[x_boundary, y_boundary],
                                                         tables['bkg_NA'].loc[x_boundary, y_boundary],
                                                         calc_unc('bkg_NA', 'bkg_NA_unc', x_boundary, y_boundary, tables, noncl.n + noncl.s))
            Z_B      = ROOT.RooStats.AsimovSignificance(tables['sig_NB'].loc[x_boundary, y_boundary],
                                                         tables['bkg_NB'].loc[x_boundary, y_boundary],
                                                         calc_unc('bkg_NB', 'bkg_NB_unc', x_boundary, y_boundary, tables, noncl.n + noncl.s))
            Z_C      = ROOT.RooStats.AsimovSignificance(tables['sig_NC'].loc[x_boundary, y_boundary],
                                                         tables['bkg_NC'].loc[x_boundary, y_boundary],
                                                         calc_unc('bkg_NC', 'bkg_NC_unc', x_boundary, y_boundary, tables, noncl.n + noncl.s))
            Z_D      = ROOT.RooStats.AsimovSignificance(tables['sig_ND'].loc[x_boundary, y_boundary],
                                                         tables['bkg_ND'].loc[x_boundary, y_boundary],
                                                         calc_unc('bkg_ND', 'bkg_ND_unc', x_boundary, y_boundary, tables, noncl.n + noncl.s))

            
            tables['Z_noncl_plus1s_A'].loc[x_boundary, y_boundary] = Z_A
            tables['Z_noncl_plus1s_B'].loc[x_boundary, y_boundary] = Z_B
            tables['Z_noncl_plus1s_C'].loc[x_boundary, y_boundary] = Z_C
            tables['Z_noncl_plus1s_D'].loc[x_boundary, y_boundary] = Z_D
            
    return tables

def save_pickle(obj: Any, path: str) -> None:
    """
    Save any Python object (including nested dictionaries of DataFrames)
    using pickle.
    """
    path = Path(path)
    with path.open("wb") as f:
        pickle.dump(obj, f, protocol=pickle.HIGHEST_PROTOCOL)


def main(uniquedir: str,
         sigtag: str,
         scan_x_loCut: list[float],
         scan_y_loCut: list[float],
         sigScale: float,
         bkgScale: float,
         ) -> None:
    
    USER = os.getenv('USER')
    HISTDIR = f'/scratch-cbe/users/{USER}/AN_plots/ParT_hists'
    WORKDIR = os.path.join(HISTDIR, uniquedir)                      # e.g. 'vtx_PART_859_epoch_87_test1'

    tfiles, th2s = open_tfiles(
        workdir =    WORKDIR,
        tdir =      'SP1_evt',
        histname =  'leading_vtx_ML1_vs_leading_vtx_ML2',
        sigtag =   sigtag
        )
    
    sig_hist = th2s['sig']
    bkg_hist = th2s['bkg']
    

    x_binwidth = sig_hist.GetXaxis().GetBinWidth(1)
    y_binwidth = sig_hist.GetYaxis().GetBinWidth(1)

    xax = sig_hist.GetXaxis()
    yax = sig_hist.GetYaxis()

    x_min = xax.GetBinLowEdge(1)
    x_max = xax.GetBinUpEdge(xax.GetLast())

    y_min = yax.GetBinLowEdge(1)
    y_max = yax.GetBinUpEdge(yax.GetLast())

    ML1_boundaryList = np.arange(x_min + x_binwidth, x_max, x_binwidth)
    ML2_boundaryList = np.arange(y_min + y_binwidth, y_max, y_binwidth)


    myDict = dict()
    for x_cut in scan_x_loCut:
        for y_cut in scan_y_loCut:
            tables = makeTables(
                ML1_boundaryList,
                ML2_boundaryList,
                bkg_hist,
                sig_hist,
                x_loCut = x_cut,
                y_loCut = y_cut,
                sigScale = sigScale,
                bkgScale = bkgScale,
            )
            myDict[f"{x_cut:.2f},{y_cut:.2f}"] = tables
    
    OUTDIR = os.path.join(WORKDIR, sigtag)
    TABLEDIR = os.path.join(OUTDIR, 'tables')
    TABLEPATH = os.path.join(TABLEDIR, f"gridsearch_disco.pkl")
    os.makedirs(TABLEDIR, exist_ok=True)

    save_pickle(myDict, TABLEPATH)
    close_tfiles(tfiles)   


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Grid search for DISCO model")
    p.add_argument(
        "--uniquedir",
        type=str,
        default=None,
        help="Optional string argument."
    )

    p.add_argument(
        "--sigtag",
        type=str,
        default=None,
        help="Optional string argument."
    )

    p.add_argument(
        "--scan-x-loCut",
        nargs="+",
        type=float,
        default=[0.0],
        help="Scan non-closure x lower boundary. Default: [0.0]"
    )
    p.add_argument(
        "--scan-y-loCut",
        nargs="+",
        type=float,
        default=[0.0],
        help="Scan non-closure y lower boundary. Default: [0.0]"
    )
    p.add_argument(
    "--sigScale",
    type=float,
    default=1.0,
    help="Signal scale factor (float). Default: 1.0"
    )
    p.add_argument(
    "--bkgScale",
    type=float,
    default=1.0,
    help="Signal scale factor (float). Default: 1.0"
    )
    p.add_argument(
        "--test",
        action="store_true",
        help="Enables test mode. Runs over a predifened directory with default values."
    )
    p.add_argument(
        "--dryrun",
        action="store_true",
        help="Show what is about to be run without executing."
    )

    args = p.parse_args()


    # --- Test mode definition -----------------------------------------------

    if args.test:
        # Test mode → use defaults, reject user overrides.
        if args.uniquedir is not None:
            raise ValueError("Cannot use --test together with --uniquedir.")
        if args.sigtag is not None:
            raise ValueError("Cannot use --test together with --sigtag.")

        uniquedir = "vtx_PART_859_epoch_87_test1"
        sigtag    = "stop_M600_585_ct20_2018"

    else:
        # User must provide both
        if args.uniquedir is None:
            raise ValueError("Please provide --uniquedir when not using --test.")
        if args.sigtag is None:
            raise ValueError("Please provide --sigtag when not using --test.")

        uniquedir = args.uniquedir
        sigtag    = args.sigtag


    # --- Dry-run printing -------------------------------------------------

    if args.dryrun:
        print("main(")
        print(f"    uniquedir      = '{uniquedir}',")
        print(f"    sigtag         = '{sigtag}',")
        print(f"    scan_x_loCut   = {args.scan_x_loCut},")
        print(f"    scan_y_loCut   = {args.scan_y_loCut},")
        print(f"    sigScale       = {args.sigScale},")
        print(f"    bkgScale       = {args.bkgScale},")
        print(")")
    else:
        main(
            uniquedir    = uniquedir,
            sigtag       = sigtag,
            scan_x_loCut = args.scan_x_loCut,
            scan_y_loCut = args.scan_y_loCut,
            sigScale     = args.sigScale,
            bkgScale     = args.bkgScale,
        )