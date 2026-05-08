# Usage:
# python3 make_multiplane_datacards.py --xcut 1.5 --ycut 0.9990 --ylo 0.20 --scale 4.574
#
#

import argparse
from ctypes import c_double
from pathlib import Path

import ROOT
import numpy as np
import pandas as pd

import SoftDisplacedVertices.Samples.Samples as ss


def get_hist(HISTDIR, SAMPLENAME, METCUT, PLANE, sample_type,year=None):
    if sample_type == 'sig':
        file_path = HISTDIR / f'sig{year[-2:]}/{SAMPLENAME}_hist.root'
    else:
        file_path = HISTDIR / f'bkg{year[-2:]}/all_{year}_hist.root'

    # plane_map = {
    #     'SP0': 'MET350SP0_evt/leading_vtx_dphiMET_vs_leading_vtx_MLscore',
    #     'SP1': 'MET350SP1_evt/leading_vtx_dphiMET_vs_leading_vtx_MLscore',
    #     'SP2': 'MET350SP2_evt/leading_vtx_dphiMET_vs_leading_vtx_MLscore',
    #     'SP3': 'MET350SP3_evt/leading_vtx_dphiMET_vs_leading_vtx_MLscore',
    # }

    plane_map = {
    'SP0': 'MET350SP0_evt/leading_vtx_SP0_dphiMET_vs_SP0_Max_ML_score',
    'SP1': 'MET350SP1_evt/leading_vtx_SP1_dphiMET_vs_SP1_Max_ML_score',
    'SP2': 'MET350SP2_evt/leading_vtx_SP2_dphiMET_vs_SP2_Max_ML_score',
    'SP3': 'MET350SP3_evt/leading_vtx_SP3_dphiMET_vs_SP3_Max_ML_score',
    }

    f = ROOT.TFile.Open(str(file_path))
    h = f.Get(plane_map[PLANE])
    h.SetDirectory(0)
    f.Close()
    return h


def get_region_yields(hist, xcut, ycut, ylo, verbose=False):
    xax = hist.GetXaxis()
    yax = hist.GetYaxis()


    xbin = hist.GetXaxis().FindBin(xcut)
    ybin = hist.GetYaxis().FindBin(ycut)
    ybin_low = hist.GetYaxis().FindBin(ylo)

    nx = hist.GetNbinsX()
    ny = hist.GetNbinsY()

    regions = {
        "A": (0,    xbin-1,     ybin,     1000000000),
        "B": (xbin, 1000000000, ybin,     1000000000),
        "C": (0,    xbin-1,     ybin_low, ybin - 1),
        "D": (xbin, 1000000000, ybin_low, ybin - 1),
    }

    out = {}
    for region, (bx1, bx2, by1, by2) in regions.items():
        err = c_double(0.0)
        val = hist.IntegralAndError(bx1, bx2, by1, by2, err)
        out[region] = {'yield': val,
                       'error': err.value}

        if verbose:
            print(
                region,
                "x:[", xax.GetBinLowEdge(bx1), ",", xax.GetBinUpEdge(bx2), "]",
                "y:[", yax.GetBinLowEdge(by1), ",", yax.GetBinUpEdge(by2), "]"
            )

    return out


# ----------------------------------------------------------------------
# Datacard creation
# ----------------------------------------------------------------------
def make_datacard(HISTDIR, SAMPLENAME, METCUT,
                  xcut, ycut, ylo, scale, outfile,
                  mode='observation', noncl_sys=None, year=None):
    """
    mode = 'Asimov' or 'observation'
    """
    bins          = {}
    yields        = {}
    rates         = {}
    processes_num = {}
    processes_str = {}

    PLANEs  = ['SP0', 'SP1', 'SP2', 'SP3']
    REGIONs = ['A', 'B', 'C', 'D']

    for PLANE in PLANEs:
        sig_hist = get_hist(HISTDIR=HISTDIR,
                            SAMPLENAME=SAMPLENAME,
                            METCUT=METCUT,
                            PLANE=PLANE,
                            sample_type='sig',
                            year=year)

        bkg_hist = get_hist(HISTDIR=HISTDIR,
                            SAMPLENAME=SAMPLENAME,
                            METCUT=METCUT,
                            PLANE=PLANE,
                            sample_type='bkg',
                            year=year)

        sig_table = get_region_yields(sig_hist, xcut=xcut, ycut=ycut, ylo=ylo)
        bkg_table = get_region_yields(bkg_hist, xcut=xcut, ycut=ycut, ylo=ylo)

        for REGION in REGIONs:
            bins[f'{PLANE}_{REGION}_sig'] = f'{PLANE}_{REGION}'
            bins[f'{PLANE}_{REGION}_bkg'] = f'{PLANE}_{REGION}'

            sig_val = sig_table[REGION]['yield'] * scale
            bkg_val = bkg_table[REGION]['yield'] * scale

            yields[f'{PLANE}_{REGION}_sig'] = round(sig_val, 4)

            if mode == 'Asimov':
                if REGION != 'A':
                    yields[f'{PLANE}_{REGION}_bkg'] = round(bkg_val, 4)
                else:
                    yields[f'{PLANE}_{REGION}_bkg'] = round(
                        bkg_table['B']['yield'] * scale *
                        bkg_table['C']['yield'] * scale /
                       (bkg_table['D']['yield'] * scale),
                        8
                    )

            if mode == 'observation':
                yields[f'{PLANE}_{REGION}_bkg'] = round(bkg_val, 4)

            if yields[f'{PLANE}_{REGION}_bkg'] < 0:
                yields[f'{PLANE}_{REGION}_bkg'] = 0

            rates[f'{PLANE}_{REGION}_sig'] = round(sig_val, 4)
            rates[f'{PLANE}_{REGION}_bkg'] = 1

            processes_num[f'{PLANE}_{REGION}_sig'] = 0
            processes_num[f'{PLANE}_{REGION}_bkg'] = 1

            processes_str[f'{PLANE}_{REGION}_sig'] = 'sig'
            processes_str[f'{PLANE}_{REGION}_bkg'] = 'bkg'

    systematics_summary = {
        'trigger':    {'2017': 0, '2018': 1.027},
        'qcd_s':      {'2017': 0, '2018': 1.015},
        'pdf':        {'2017': 0, '2018': 1.006},
        'matveto':    {'2017': 0, '2018': 1.01},
        'vtxreco':    {'2017': 0, '2018': 1.107},
        'uncls_es':   {'2017': 0, '2018': 1.013},
        'jes':        {'2017': 0, '2018': 1.034},
        'jer':        {'2017': 0, '2018': 1.008},
        'pu':         {'2017': 0, '2018': 1.032},
        'lumi':       {'2017': 0, '2018': 1.02},
    }

    systematics = {
        'trigger':  {},
        'qcd_s':    {},
        'pdf':      {},
        'matveto':  {},
        'vtxreco':  {},
        'uncls_es': {},
        'jes':      {},
        'jer':      {},
        'pu':       {},
        'lumi':     {},
    }

    for key, value in systematics_summary.items():
        for PLANE in PLANEs:
            for REGION in REGIONs:
                for year in systematics_summary[key].keys():
                    if year == '2018':
                        systematics[key][f'{PLANE}_{REGION}_sig'] = systematics_summary[key][year]
                        systematics[key][f'{PLANE}_{REGION}_bkg'] = '-'

    lines = []

    lines.append('imax 16  number of channels')
    lines.append('jmax 1   number of processes -1')
    lines.append('kmax *   number of nuisance parameters (sources of systematical uncertainties)')

    lines.append('-' * 160)

    line = f'{"bin":<14} '
    for k, v in bins.items():
        if k[-3:] == 'bkg':
            line += f'{v:<18} '
    lines.append(line)

    line = f'{"observation":<14} '
    for k, v in yields.items():
        if k[-3:] == 'bkg':
            line += f'{v:<18} '
    lines.append(line)

    lines.append('-' * 160)

    line = f'{"bin":<20} '
    for k, v in bins.items():
        line += f'{v:<12} '
    lines.append(line)

    line = f'{"process":<20} '
    for k, v in processes_str.items():
        line += f'{v:<12} '
    lines.append(line)

    line = f'{"process":<20} '
    for k, v in processes_num.items():
        line += f'{v:<12} '
    lines.append(line)

    line = f'{"rate":<20} '
    for k, v in rates.items():
        line += f'{v:<12} '
    lines.append(line)

    lines.append('-' * 160)

    for sys_name, sys_dict in systematics.items():
        line = f'{sys_name:<15}{"lnN":<5} '
        for k, v in sys_dict.items():
            line += f'{v:<8} '
        lines.append(line)

    lines.append('')

    for k, v in bins.items():
        if processes_str[k] == 'bkg':
            line  = f'rate_{v:<8}'
            line += f'{"rateParam":<11} '
            line += f'{v:<8} '
            line += f'{processes_str[k]}    '

            if v[-1] == 'A':
                B = f'rate_{v[:-1]}B'
                C = f'rate_{v[:-1]}C'
                D = f'rate_{v[:-1]}D'
                line += f"(@0*@1/@2) {B},{C},{D}"
            else:
                line += f'{yields[k]}'

            lines.append(line)

    lines.append('')

    datacard_str = "\n".join(lines)

    outfile = Path(outfile)
    outfile.parent.mkdir(parents=True, exist_ok=True)
    outfile.write_text(datacard_str + "\n", encoding="utf-8")

    print(f"Wrote datacard to: {outfile}")


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------
def main(HISTDIR, SAMPLENAME, METCUT, xcut, ycut, ylo, scale, outfile, noncl_sys, mode, year):

    make_datacard(
        HISTDIR=HISTDIR,
        SAMPLENAME=SAMPLENAME,
        METCUT=METCUT,
        xcut=xcut,
        ycut=ycut,
        ylo=ylo,
        scale=scale,
        outfile=outfile,
        noncl_sys=noncl_sys,
        mode=mode,
        year=year
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Create Combine ABCD datacard from ROOT histograms"
    )
    parser.add_argument(
        "--xcut",
        type=float,
        help="x threshold, e.g. 1.5",
    )
    parser.add_argument(
        "--ycut",
        type=float,
        help="y threshold, e.g. 0.9998",
    )
    parser.add_argument(
        "--ylo",
        type=float,
        help="y threshold, e.g. 0.20",
    )
    parser.add_argument(
        "--scale",
        type=float,
        default=1.0,
        help="Scale luminosity factor (default: 1.0).",
    )
    parser.add_argument(
        "--sig-sys",
        type=float,
        default=0.20,
        help="Relative signal uncertainty (e.g. 0.20 for 20%%).",
    )
    parser.add_argument(
        "--bkg-sys",
        type=float,
        default=0.10,
        help="Relative per-region background uncertainty (e.g. 0.10 for 10%%).",
    )
    parser.add_argument(
        "--noncl-sys",
        type=float,
        default=None,
        help="Relative non-closure uncertainty on region A background (e.g. 0.20 for 20%%).",
    )
    parser.add_argument(
        "--year",
        type=str,
        help="year, e.g. 2017",
    )
    parser.add_argument(
        "--mode",
        default='observation',
        help="Should set observation to 'observation' or 'Asimov' predicted?",
    )
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output datacard path. If not set, a name is auto-generated.",
    )

    args = parser.parse_args()

    # HISTDIR = Path('/scratch-cbe/users/alikaan.gueven/AN_plots/ParT_hists/plotconfig_Run2_MLscore_first')
    HISTDIR = Path('/scratch-cbe/users/alikaan.gueven/AN_plots/ParT_hists/plotconfig_Run2_goodtk_first_v2')
    datacard_dir = HISTDIR / "datacards"
    datacard_dir.mkdir(parents=True, exist_ok=True)


    METCUT = 350
    
    SAMPLES = ss.private_sig18
    if not isinstance(SAMPLES, list):
        SAMPLES = list(SAMPLES)

    for SAMPLE in SAMPLES:
        SAMPLENAME = SAMPLE.name
        if args.output is None:
            outfile = datacard_dir / f"{SAMPLENAME}.txt"
        else:
            outfile = Path(args.output) / f"{SAMPLENAME[:-5]}_{args.year}.txt"

        main(HISTDIR=HISTDIR,
            SAMPLENAME=SAMPLENAME,
            METCUT=METCUT,
            xcut=args.xcut,
            ycut=args.ycut,
            ylo=args.ylo,
            scale=args.scale,
            outfile=outfile,
            noncl_sys=args.noncl_sys,
            mode=args.mode,
            year=args.year
            )