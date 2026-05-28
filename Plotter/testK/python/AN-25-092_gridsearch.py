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

SCAN_X_MIN = 350.0
SCAN_X_MAX = 700.0
SCAN_X_STEP = 50.0
SCAN_Y_MIN = 0.990
SCAN_Y_MAX = 1.0
SCAN_Y_STEP = 0.0002


def open_tfiles(workdir, tdir, histname, sigtag, isData=False):


    sig_file = ROOT.TFile(os.path.join(workdir, f"{sigtag}_hist.root"), 'READ')
    sig_dir  = getattr(sig_file, tdir)
    sig_hist = getattr(sig_dir, histname).Clone()

    if isData:
        bkg_file = ROOT.TFile(os.path.join(workdir, f"data_run2plus3_hist.root"), 'READ')
    else:
        bkg_file = ROOT.TFile(os.path.join(workdir, f"bkg_run2plus3_hist.root"), 'READ')
    bkg_dir  = getattr(bkg_file, tdir)
    bkg_hist = getattr(bkg_dir, histname).Clone()

    tfiles = dict(sig = sig_file, bkg = bkg_file)
    th2s   = dict(sig = sig_hist, bkg = bkg_hist)

    return tfiles, th2s

def find_tdirs(workdir, histname, sigtag):
    sig_file = ROOT.TFile(os.path.join(workdir, f"{sigtag}_hist.root"), 'READ')
    tdirs = []
    for key in sig_file.GetListOfKeys():
        obj = key.ReadObj()
        if obj.InheritsFrom("TDirectory") and obj.Get(histname):
            tdirs.append(obj.GetName())
    sig_file.Close()
    return tdirs

def close_tfiles(tfiles):
    for tfile in tfiles:
        tfiles[tfile].Close()

def calc_unc(bkg_NA, bkg_NA_unc, noncl=None):
    unc1 = bkg_NA * 0.20
    unc2 = bkg_NA * noncl if noncl else 0.
    unc3 = bkg_NA_unc
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
    xedges = np.round(np.asarray(xedges, dtype=np.float64), 8)
    yedges = np.round(np.asarray(yedges, dtype=np.float64), 8)

    xidx = pd.Index(xedges)# , name="x_cut")
    yidx = pd.Index(yedges)# , name="y_cut")

    empty_df = pd.DataFrame(index=xidx, columns=yidx, dtype=float)

    # Create empty tables
    tableNames = ['sig_NA', 'sig_NB', 'sig_NC', 'sig_ND',
                  'bkg_NA', 'bkg_NB', 'bkg_NC', 'bkg_ND',
                  'sig_NA_unc', 'sig_NB_unc', 'sig_NC_unc', 'sig_ND_unc',
                  'bkg_NA_unc', 'bkg_NB_unc', 'bkg_NC_unc', 'bkg_ND_unc',
                  'Z_A', 'Z_B', 'Z_C', 'Z_D',
                  'Z_A_pred', 'Z_noncl_A_pred',
                  'Z_noncl_A', 'Z_noncl_B', 'Z_noncl_C', 'Z_noncl_D',
                  # 'Z_noncl_plus1s_A', 'Z_noncl_plus1s_B', 'Z_noncl_plus1s_C', 'Z_noncl_plus1s_D',
                  'noncl', 'noncl_unc',
                  'A_pred', 'A_pred_unc',
                  'delta_A', 'delta_A_unc',
                ]
    tables = dict()
    for name in tableNames:
        tables[name] = empty_df.copy()
     
    for x_boundary in xidx.to_numpy():
        for y_boundary in yidx.to_numpy():
            x_lo    = bkg_hist.GetXaxis().FindBin(x_loCut)
            x_up    = bkg_hist.GetNbinsX()+1
            x_bound = bkg_hist.GetXaxis().FindBin(x_boundary)

            y_lo    = bkg_hist.GetYaxis().FindBin(y_loCut)
            y_up    = bkg_hist.GetNbinsY()+1
            y_bound = bkg_hist.GetYaxis().FindBin(y_boundary)

            if x_boundary < x_loCut: continue
            if y_boundary < y_loCut: continue


            # ------------ Backgrounds --------------
            c_err = c_double(0.0)
            bkg_NA = ufloat(bkg_hist.IntegralAndError(x_bound,    x_up,       y_bound,    y_up,          c_err), c_err.value) * bkgScale
            bkg_NB = ufloat(bkg_hist.IntegralAndError(x_lo,       x_bound-1,  y_bound,    y_up,          c_err), c_err.value) * bkgScale
            bkg_NC = ufloat(bkg_hist.IntegralAndError(x_bound,    x_up,       y_lo,      y_bound-1,      c_err), c_err.value) * bkgScale
            bkg_ND = ufloat(bkg_hist.IntegralAndError(x_lo,       x_bound-1,  y_lo,      y_bound-1,      c_err), c_err.value) * bkgScale

            num   = bkg_NB * bkg_NC
            denom = bkg_NA * bkg_ND
            noncl = np.abs(1- num/denom) if denom.n > 0 else ufloat(1., 1.) # Check this line!

            A_pred = (bkg_NB * bkg_NC) / bkg_ND if bkg_ND.n > 0 else ufloat(float('nan'),float('nan'))
            delta_A = bkg_NA - A_pred if bkg_ND.n > 0 else ufloat(float('nan'),float('nan'))

            tables['bkg_NA'].loc[x_boundary, y_boundary] = bkg_NA.n
            tables['bkg_NB'].loc[x_boundary, y_boundary] = bkg_NB.n
            tables['bkg_NC'].loc[x_boundary, y_boundary] = bkg_NC.n
            tables['bkg_ND'].loc[x_boundary, y_boundary] = bkg_ND.n

            tables['bkg_NA_unc'].loc[x_boundary, y_boundary] = bkg_NA.s
            tables['bkg_NB_unc'].loc[x_boundary, y_boundary] = bkg_NB.s
            tables['bkg_NC_unc'].loc[x_boundary, y_boundary] = bkg_NC.s
            tables['bkg_ND_unc'].loc[x_boundary, y_boundary] = bkg_ND.s

            tables['noncl'].loc[x_boundary, y_boundary]     = noncl.n
            tables['noncl_unc'].loc[x_boundary, y_boundary] = noncl.s

            tables['A_pred'].loc[x_boundary, y_boundary]     = A_pred.n
            tables['A_pred_unc'].loc[x_boundary, y_boundary] = A_pred.s

            tables['delta_A'].loc[x_boundary, y_boundary]     = delta_A.n
            tables['delta_A_unc'].loc[x_boundary, y_boundary] = delta_A.s
            

            # ------------ Signals --------------
            c_err = c_double(0.0)
            sig_NA = ufloat(sig_hist.IntegralAndError(x_bound,    x_up,       y_bound,    y_up,          c_err), c_err.value) * sigScale
            sig_NB = ufloat(sig_hist.IntegralAndError(x_lo,       x_bound-1,  y_bound,    y_up,          c_err), c_err.value) * sigScale
            sig_NC = ufloat(sig_hist.IntegralAndError(x_bound,    x_up,       y_lo,      y_bound-1,      c_err), c_err.value) * sigScale
            sig_ND = ufloat(sig_hist.IntegralAndError(x_lo,       x_bound-1,  y_lo,      y_bound-1,      c_err), c_err.value) * sigScale

            tables['sig_NA'].loc[x_boundary, y_boundary] = sig_NA.n
            tables['sig_NB'].loc[x_boundary, y_boundary] = sig_NB.n
            tables['sig_NC'].loc[x_boundary, y_boundary] = sig_NC.n
            tables['sig_ND'].loc[x_boundary, y_boundary] = sig_ND.n

            tables['sig_NA_unc'].loc[x_boundary, y_boundary] = sig_NA.s
            tables['sig_NB_unc'].loc[x_boundary, y_boundary] = sig_NB.s
            tables['sig_NC_unc'].loc[x_boundary, y_boundary] = sig_NC.s
            tables['sig_ND_unc'].loc[x_boundary, y_boundary] = sig_ND.s

            # ------------ Significance --------------
            eps = 5e-1

            Z_A = ROOT.RooStats.AsimovSignificance(sig_NA.n, max(eps, bkg_NA.n), calc_unc(max(eps, bkg_NA.n), max(eps, bkg_NA.s), 0.))
            Z_B = ROOT.RooStats.AsimovSignificance(sig_NB.n, max(eps, bkg_NB.n), calc_unc(max(eps, bkg_NB.n), max(eps, bkg_NB.s), 0.))
            Z_C = ROOT.RooStats.AsimovSignificance(sig_NC.n, max(eps, bkg_NC.n), calc_unc(max(eps, bkg_NC.n), max(eps, bkg_NC.s), 0.))
            Z_D = ROOT.RooStats.AsimovSignificance(sig_ND.n, max(eps, bkg_ND.n), calc_unc(max(eps, bkg_ND.n), max(eps, bkg_ND.s), 0.))

            A_pred_n = max(eps, A_pred.n) if np.isfinite(A_pred.n) else eps
            A_pred_s = max(eps, A_pred.s) if np.isfinite(A_pred.s) else eps
            Z_A_pred = ROOT.RooStats.AsimovSignificance(sig_NA.n, A_pred_n, calc_unc(A_pred_n, A_pred_s, 0.))
            
            tables['Z_A'].loc[x_boundary, y_boundary] = Z_A
            tables['Z_B'].loc[x_boundary, y_boundary] = Z_B
            tables['Z_C'].loc[x_boundary, y_boundary] = Z_C
            tables['Z_D'].loc[x_boundary, y_boundary] = Z_D
            tables['Z_A_pred'].loc[x_boundary, y_boundary] = Z_A_pred

            # ------------ Significance with non-clsoure uncertainty --------------

            Z_noncl_A = ROOT.RooStats.AsimovSignificance(sig_NA.n, max(eps, bkg_NA.n), calc_unc(max(eps, bkg_NA.n), max(eps, bkg_NA.s), abs(noncl.n)))
            Z_noncl_B = ROOT.RooStats.AsimovSignificance(sig_NB.n, max(eps, bkg_NB.n), calc_unc(max(eps, bkg_NB.n), max(eps, bkg_NB.s), abs(noncl.n)))
            Z_noncl_C = ROOT.RooStats.AsimovSignificance(sig_NC.n, max(eps, bkg_NC.n), calc_unc(max(eps, bkg_NC.n), max(eps, bkg_NC.s), abs(noncl.n)))
            Z_noncl_D = ROOT.RooStats.AsimovSignificance(sig_ND.n, max(eps, bkg_ND.n), calc_unc(max(eps, bkg_ND.n), max(eps, bkg_ND.s), abs(noncl.n)))
            Z_noncl_A_pred = ROOT.RooStats.AsimovSignificance(sig_NA.n, A_pred_n, calc_unc(A_pred_n, A_pred_s, abs(noncl.n)))

            
            tables['Z_noncl_A'].loc[x_boundary, y_boundary] = Z_noncl_A
            tables['Z_noncl_B'].loc[x_boundary, y_boundary] = Z_noncl_B
            tables['Z_noncl_C'].loc[x_boundary, y_boundary] = Z_noncl_C
            tables['Z_noncl_D'].loc[x_boundary, y_boundary] = Z_noncl_D
            tables['Z_noncl_A_pred'].loc[x_boundary, y_boundary] = Z_noncl_A_pred

            
    return tables

def save_pickle(obj: Any, path: str) -> None:
    """
    Save any Python object (including nested dictionaries of DataFrames)
    using pickle.
    """
    path = Path(path)
    with path.open("wb") as f:
        pickle.dump(obj, f, protocol=pickle.HIGHEST_PROTOCOL)


def make_tdir_tables(workdir: str,
                     sigtag: str,
                     scan_x_loCut: list[float],
                     scan_y_loCut: list[float],
                     sigScale: float,
                     bkgScale: float,
                     tdir: str,
                     histname: str,
                     isData: bool = False,
                     ) -> dict:
    tfiles, th2s = open_tfiles(
        workdir =   workdir,
        tdir    =   tdir,        # e.g. SP1_evt
        histname =  histname,    # e.g. leading_vtx_ML1_vs_leading_vtx_ML2
        sigtag =    sigtag,       # e.g. stop_M600_585_ct20_2018
        isData =  isData,
        )

    sig_hist = th2s['sig']
    bkg_hist = th2s['bkg']

    xax = sig_hist.GetXaxis()
    yax = sig_hist.GetYaxis()

    x_boundaries = np.arange(SCAN_X_MIN, SCAN_X_MAX + 0.5 * SCAN_X_STEP, SCAN_X_STEP)
    y_boundaries = np.arange(SCAN_Y_MIN, SCAN_Y_MAX + 0.5 * SCAN_Y_STEP, SCAN_Y_STEP)

    ML1_boundaryList = np.array(x_boundaries, dtype=np.float64)
    ML2_boundaryList = np.array(y_boundaries, dtype=np.float64)

    ML1_boundaryList = np.round(ML1_boundaryList, 8)
    ML2_boundaryList = np.round(ML2_boundaryList, 8)

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

    close_tfiles(tfiles)
    return myDict


def main(uniquedir: str,
         sigtag: str,
         scan_x_loCut: list[float],
         scan_y_loCut: list[float],
         sigScale: float,
         bkgScale: float,
         tdir: str,
         histname: str,
         isData: bool = False,
         ) -> None:
    
    USER = os.getenv('USER')
    HISTDIR = f'/scratch-cbe/users/{USER}/AN_plots/ParT_hists'
    WORKDIR = os.path.join(HISTDIR, uniquedir)                      # e.g. 'vtx_PART_859_epoch_87_test1'
    if not os.path.isfile(os.path.join(WORKDIR, f"{sigtag}_hist.root")):
        run2plus3_dir = os.path.join(WORKDIR, 'run2plus3')
        if os.path.isfile(os.path.join(run2plus3_dir, f"{sigtag}_hist.root")):
            WORKDIR = run2plus3_dir

    if tdir is None:
        tdirs = find_tdirs(WORKDIR, histname, sigtag)
        if not tdirs:
            raise ValueError(f"Could not find histogram '{histname}' in any TDirectory.")
        myDict = dict()
        for tdir_ in tdirs:
            myDict[tdir_] = make_tdir_tables(
                workdir = WORKDIR,
                sigtag = sigtag,
                scan_x_loCut = scan_x_loCut,
                scan_y_loCut = scan_y_loCut,
                sigScale = sigScale,
                bkgScale = bkgScale,
                tdir = tdir_,
                histname = histname,
                isData = isData,
            )

        TABLEDIR = os.path.join(WORKDIR, 'tables')
        SIGTABLEDIR = os.path.join(TABLEDIR, f"{sigtag}")
        if isData:
            SIGTABLEDIR += "_withdata"
        TABLEPATH = os.path.join(SIGTABLEDIR, f"gridsearch_disco.pkl")
        os.makedirs(SIGTABLEDIR, exist_ok=True)

        save_pickle(myDict, TABLEPATH)
        return

    myDict = make_tdir_tables(
        workdir = WORKDIR,
        sigtag = sigtag,
        scan_x_loCut = scan_x_loCut,
        scan_y_loCut = scan_y_loCut,
        sigScale = sigScale,
        bkgScale = bkgScale,
        tdir = tdir,
        histname = histname,
        isData = isData,
    )
    
    TABLEDIR = os.path.join(WORKDIR, 'tables')
    SIGTABLEDIR = os.path.join(TABLEDIR, f"{sigtag}")
    if isData:
        SIGTABLEDIR += "_withdata"
    TABLEPATH = os.path.join(SIGTABLEDIR, f"gridsearch_disco.pkl")
    os.makedirs(SIGTABLEDIR, exist_ok=True)

    save_pickle(myDict, TABLEPATH)


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
        default=[250.0],
        help="Scan non-closure x lower boundary. Default: [250.0]"
    )
    p.add_argument(
        "--scan-y-loCut",
        nargs="+",
        type=float,
        default=[0.8],
        help="Scan non-closure y lower boundary. Default: [0.8]"
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
    "--tdir",
    type=str,
    default=None,
    help="region in your plotter config: e.g. SP1_evt. Default: run over every TDirectory"
    )
    p.add_argument(
    "--histname",
    type=str,
    default="MET_pt_corr_vs_leadingvtx_MLscore",
    help="Histogram name in your yaml congig: e.g. leading_vtx_ML1_vs_leading_vtx_ML2"
    )
    p.add_argument(
    "--isData",
    action="store_true",
    help="Are you passing the data or the background histograms?"
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

        uniquedir = "AN-25-092_ML_plots_limitcalc_merge_w_Ang_v3/run2plus3"
        sigtag    = "stop_M1000_980_ct2_run2plus3"
        tdir      = None
        histname  = "MET_pt_corr_vs_leadingvtx_MLscore"

    else:
        # User must provide both
        if args.uniquedir is None:
            raise ValueError("Please provide --uniquedir when not using --test.")
        if args.sigtag is None:
            raise ValueError("Please provide --sigtag when not using --test.")

        uniquedir = args.uniquedir
        sigtag    = args.sigtag
        tdir      = args.tdir
        histname  = args.histname if args.histname is not None else "MET_pt_corr_vs_leadingvtx_MLscore"


    # --- Dry-run printing -------------------------------------------------

    if args.dryrun:
        print("main(")
        print(f"    uniquedir      = '{uniquedir}',")
        print(f"    sigtag         = '{sigtag}',")
        print(f"    scan_x_loCut   = {args.scan_x_loCut},")
        print(f"    scan_y_loCut   = {args.scan_y_loCut},")
        print(f"    sigScale       = {args.sigScale},")
        print(f"    bkgScale       = {args.bkgScale},")
        print(f"    tdir           = {tdir if tdir is not None else 'every TDirectory'},")
        print(f"    histname       = {histname},")
        print(f"    isData         = {args.isData},")
        print(")")
    else:
        main(
            uniquedir    = uniquedir,
            sigtag       = sigtag,
            scan_x_loCut = args.scan_x_loCut,
            scan_y_loCut = args.scan_y_loCut,
            sigScale     = args.sigScale,
            bkgScale     = args.bkgScale,
            tdir         = tdir,
            histname     = histname,
            isData       = args.isData,
        )
