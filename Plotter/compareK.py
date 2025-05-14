"""
Example usage:

Compare histograms for different directories in different files:
python3 compare.py --input /path/to/stop_M600_588_ct200_2018_hist.root /path/to/stop_M600_580_ct2_2018_hist.root --dirs histtag histuntag --nice 588 580 --scale --output /path/to/output

Compare histograms for the same directory in different files:
python3 compare.py --input /path/to/stop_M600_588_ct200_2018_hist.root /path/to/stop_M600_580_ct2_2018_hist.root --dirs histtag --nice 588 580 --scale --output /path/to/output

Compare histograms for different directories in the same file:
python3 compare.py --input /path/to/stop_M600_588_ct200_2018_hist.root --dirs histtag histuntag --nice tag untag --scale --output /path/to/output
"""

import os
import math
from array import array
import argparse

import ROOT
import cmsstyle as CMS
import SoftDisplacedVertices.Samples.Samples as s

# ROOT configuration
ROOT.EnableImplicitMT()
ROOT.gROOT.SetBatch(ROOT.kTRUE)
ROOT.TH1.SetDefaultSumw2(True)
ROOT.gStyle.SetOptStat(0)
ROOT.TGaxis.SetExponentOffset(-0.10, 0.01, "Y")


# --------------------------------------------------
# Helper class to preserve histogram entries
# --------------------------------------------------
class TH1EntriesProtector:
    """Context manager to preserve the fEntries of a TH1 histogram.
    
    This is used to avoid the side effects of operations that change fEntries.
    """
    def __init__(self, h):
        self.h = h

    def __enter__(self):
        self.n = self.h.GetEntries()
        return self  # not used but available if needed

    def __exit__(self, *args):
        self.h.ResetStats()  # Reset stats (may not be necessary)
        self.h.SetEntries(self.n)


# --------------------------------------------------
# Functions to adjust histogram bins
# --------------------------------------------------
def move_below_into_bin(h, a):
    """
    Add the contents of all bins below the bin corresponding to 'a' into that bin,
    then zero the lower bins.
    """
    assert h.Class().GetName().startswith('TH1'), "h must be a TH1 object"
    with TH1EntriesProtector(h):
        bin_index = h.FindBin(a)
        content = h.GetBinContent(bin_index)
        error2 = h.GetBinError(bin_index) ** 2
        for nb in range(0, bin_index):
            content += h.GetBinContent(nb)
            error2 += h.GetBinError(nb) ** 2
            h.SetBinContent(nb, 0)
            h.SetBinError(nb, 0)
        h.SetBinContent(bin_index, content)
        h.SetBinError(bin_index, math.sqrt(error2))


def move_above_into_bin(h, a, minus_one=False):
    """
    Add the contents of all bins above the bin corresponding to 'a' into that bin,
    then zero the upper bins.

    If 'minus_one' is True, the bin immediately below the found bin is used.
    """
    assert h.Class().GetName().startswith('TH1'), "h must be a TH1 object"
    with TH1EntriesProtector(h):
        bin_index = h.FindBin(a)
        if minus_one:
            bin_index -= 1
        content = h.GetBinContent(bin_index)
        error2 = h.GetBinError(bin_index) ** 2
        for nb in range(bin_index + 1, h.GetNbinsX() + 2):
            content += h.GetBinContent(nb)
            error2 += h.GetBinError(nb) ** 2
            h.SetBinContent(nb, 0)
            h.SetBinError(nb, 0)
        h.SetBinContent(bin_index, content)
        h.SetBinError(bin_index, math.sqrt(error2))


def move_overflow_into_last_bin(h):
    """
    Add the contents of the overflow bin into the last visible bin,
    then zero the overflow.
    """
    assert h.Class().GetName().startswith('TH1'), "h must be a TH1 object"
    with TH1EntriesProtector(h):
        last_bin = h.GetNbinsX()
        last_content = h.GetBinContent(last_bin) + h.GetBinContent(last_bin + 1)
        last_error = math.sqrt(h.GetBinError(last_bin) ** 2 + h.GetBinError(last_bin + 1) ** 2)
        h.SetBinContent(last_bin, last_content)
        h.SetBinError(last_bin, last_error)
        h.SetBinContent(last_bin + 1, 0)
        h.SetBinError(last_bin + 1, 0)


def move_overflows_into_visible_bins(h, opt='under over'):
    """
    Adjust the histogram by moving the underflow and/or overflow into the visible bins.
    Requires that the histogram has a defined user range.
    
    :param opt: A string containing 'under', 'over', or both to specify which direction to adjust.
    """
    if not h.Class().GetName().startswith('TH1'):
        return

    opt = str(opt).strip().lower()
    if 'under' in opt:
        lower_edge = h.GetBinLowEdge(h.GetXaxis().GetFirst())
        move_below_into_bin(h, lower_edge)
    if 'over' in opt:
        upper_edge = h.GetBinLowEdge(h.GetXaxis().GetLast())
        move_above_into_bin(h, upper_edge)


# --------------------------------------------------
# Argument parsing
# --------------------------------------------------
parser = argparse.ArgumentParser()
parser.add_argument('--data', type=str, nargs='+', default=[],
                    help='Data file(s) to compare')
parser.add_argument('--datanice', type=str, nargs='+', default=[],
                    help='Data legend name')
parser.add_argument('--bkg', type=str, nargs='+', default=[],
                    help='Background file(s) to compare')
parser.add_argument('--bkgnice', type=str, nargs='+', default=[],
                    help='Background legend names')
parser.add_argument('--signal', type=str, nargs='+', default=[],
                    help='Signal file(s) to compare')
parser.add_argument('--signice', type=str, nargs='+', default=[],
                    help='Signal legend names')
parser.add_argument('--output', type=str,
                    help='Output directory')
parser.add_argument('--dirs', type=str, nargs='+',
                    help='Directories to compare')
parser.add_argument('--scale_to_data', action='store_true', default=False,
                    help='Scale the background plot according to data')
parser.add_argument('--sig_scale', type=float, nargs='+', default=[],
                    help='Scale factors for signal')
parser.add_argument('--norm', action='store_true', default=False,
                    help='Normalize all the histograms')
parser.add_argument('--commands', type=str, nargs='+',
                    help='Additional commands, such as rebinning or setting ranges')
parser.add_argument('--ratio', action='store_true', default=False,
                    help='Plot the ratio')
args = parser.parse_args()


# --------------------------------------------------
# Global color settings
# --------------------------------------------------
signal_colors = [
    ROOT.kGreen, ROOT.kRed, ROOT.kYellow+1, ROOT.kMagenta+1, ROOT.kCyan+1, ROOT.kOrange+1
]
bkg_colors = [
    ROOT.kBlue-9, ROOT.kBlue-5, ROOT.kCyan-9
]


# --------------------------------------------------
# Histogram utility functions
# --------------------------------------------------
def AddHists(hist_list, weight_list):
    """
    Add multiple histograms after scaling by the corresponding weights.
    
    :param hist_list: List of TH1 histograms.
    :param weight_list: List of weights.
    :return: New histogram that is the sum of the scaled histograms.
    """
    assert len(hist_list) == len(weight_list), "Mismatch between histogram and weight lists."
    h_new = hist_list[0].Clone()
    for i in range(len(hist_list)):
        hist_list[i].Scale(weight_list[i])
        if i > 0:
            h_new.Add(hist_list[i])
    return h_new


def StackHists(hist_list, weight_list):
    """
    Create a THStack from a list of histograms scaled by the corresponding weights.
    
    :param hist_list: List of TH1 histograms.
    :param weight_list: List of weights.
    :return: THStack object.
    """
    assert len(hist_list) == len(weight_list), "Mismatch between histogram and weight lists."
    hist_stack = ROOT.THStack("h", "")
    for i in range(len(hist_list)):
        hist_list[i].Scale(weight_list[i])
        hist_stack.Add(hist_list[i])
    return hist_stack


def h_command(h):
    """
    Execute additional user commands on the histogram.
    
    :param h: TH1 histogram.
    :return: Modified histogram.
    """
    if args.commands is None:
        return h
    for cmd in args.commands:
        local_dict = {'h': h}
        # Execute the command in a local dictionary context
        exec(cmd, globals(), local_dict)
        h = local_dict['h']
    return h


# --------------------------------------------------
# Main plotting function using CMS style
# --------------------------------------------------
def comparehists_cms(name, hs, colors, legends, sig_scale=[], scale_to_data=False, ratio=True, norm=False):
    """
    Compare histograms with CMS style settings.
    
    :param name: Name of the plot.
    :param hs: Dictionary of histograms separated by type ('data', 'bkg', 'sig').
    :param colors: Dictionary of colors for each type.
    :param legends: Dictionary of legend entries.
    :param sig_scale: List of scale factors for signals.
    :param scale_to_data: Boolean flag whether to scale background to data.
    :param ratio: Boolean flag whether to plot ratio.
    :param norm: Boolean flag whether to normalize histograms.
    """
    assert not (scale_to_data and norm), "Cannot set scale_to_data and norm at the same time!"
    
    # Set histogram styling and combine signal, background, and data histograms
    y_max = float('-inf')
    y_min = float("inf")
    y_min_log = float("inf")
    x_max = float('-inf')
    x_min = float("inf")
    x_label = ''
    y_label = ''
    d_bkg = {}

    for h_type in hs:
        for i, h in enumerate(hs[h_type]):
            move_overflows_into_visible_bins(h)
            h.GetYaxis().SetMaxDigits(2)
            
            if h_type == 'bkg':
                d_bkg[legends[h_type][i]] = h
            elif h_type == 'sig':
                h.SetLineColor(colors[h_type][i])
                h.SetLineWidth(3)
                if len(sig_scale) > 0:
                    h.Scale(sig_scale[i])
    
    # Combine data and background histograms
    data = AddHists(hs['data'], [1] * len(hs['data'])) if len(hs['data']) > 0 else None
    bkg_mc = AddHists(hs['bkg'], [1] * len(hs['bkg'])) if len(hs['bkg']) > 0 else None

    if scale_to_data and data is not None and bkg_mc is not None and bkg_mc.Integral() != 0:
        scale_factor = data.Integral(0, 1000000) / bkg_mc.Integral(0, 1000000)
        bkg_mc.Scale(scale_factor)
        for h in d_bkg.values():
            h.Scale(scale_factor)

    if norm:
        # Normalize data, background, and signal histograms
        if data is not None and data.Integral(0, 1000000) != 0:
            data_unnormed = data.Clone("data_unnormed")
            data.Scale(1.0 / data.Integral(0, 1000000))
        if bkg_mc is not None and bkg_mc.Integral(0, 1000000) != 0:
            norm_factor = 1.0 / bkg_mc.Integral(0, 1000000)
            bkg_unnormed = bkg_mc.Clone("bkg_unnormed")
            bkg_mc.Scale(norm_factor)
            for h in d_bkg.values():
                h.Scale(norm_factor)
        for h in hs['sig']:
            if h.Integral(0, 1000000) != 0:
                h.Scale(1.0 / h.Integral(0, 1000000))


    # Collect all histograms for plotting
    hlist = []
    if data is not None:
        hlist.append(data)
    if bkg_mc is not None:
        hlist.append(bkg_mc)
        hlist.append(d_bkg[legends['bkg'][0]])
    hlist.extend(hs['sig'])

    # Determine the axes ranges and labels
    for h in hlist:
        x_label = h.GetXaxis().GetTitle()
        y_label = h.GetYaxis().GetTitle()
        y_max = max(y_max, h.GetMaximum())
        y_min_log = min(y_min_log, h.GetMinimum(1e-08))
        y_min = min(y_min, h.GetMinimum())
        x_max = max(x_max, h.GetXaxis().GetBinUpEdge(h.GetXaxis().GetLast()))
        x_min = min(x_min, h.GetXaxis().GetBinLowEdge(h.GetXaxis().GetFirst()))

    # Set CMS extra text and lumi labels
    if data is not None:
        CMS.SetExtraText("Preliminary")
    else:
        CMS.SetExtraText("Simulation Preliminary")
    CMS.SetLumi("")

    # Setup the canvas for data/MC ratio plots if applicable
    square = CMS.kSquare
    iPos = 0
    do_ratio = ratio and (data is not None and bkg_mc is not None)

    if do_ratio:
        canv = CMS.cmsDiCanvas(
            name, x_min, x_max, y_min, (y_max - y_min) / 0.65 + y_min,
            0, 2.5, x_label, y_label, "Data/MC",
            square=square, extraSpace=0.1, iPos=iPos,
        )
    else:
        canv = CMS.cmsCanvas(
            name, x_min, x_max, y_min, (y_max - y_min) / 0.65 + y_min,
            x_label, y_label, square=CMS.kSquare, extraSpace=0.01, iPos=0
        )

    leg = CMS.cmsLeg(0.2, 0.69, 0.99, 0.89, textSize=0.04, columns=2)
    if data is not None:
        leg.AddEntry(data, legends['data'][0], "pe")
    if bkg_mc is not None:
        stack = ROOT.THStack("stack", "Stacked")
        CMS.cmsDrawStack(stack, leg, d_bkg)
        h_err = bkg_mc.Clone("h_err")
        CMS.cmsDraw(h_err, "e2same0", lcolor=335, lwidth=1,
                    msize=0, fcolor=ROOT.kBlack, fstyle=3004)
    if data is not None:
        CMS.cmsDraw(data, "E1X0", mcolor=ROOT.kBlack)
    for i, sig_hist in enumerate(hs['sig']):
        leg.AddEntry(sig_hist, legends['sig'][i], "l")
        sig_hist.Draw("hist same")

    # Ratio plotting section
    if do_ratio:
        canv.cd(2)
        leg_ratio = CMS.cmsLeg(0.17, 0.97 - 0.05 * 5, 0.35, 0.97, textSize=0.05, columns=2)
        ratio_hist = data.Clone("ratio")
        ratio_hist.Divide(bkg_mc)
        for i in range(1, ratio_hist.GetNbinsX() + 1):
            if ratio_hist.GetBinContent(i):
                ratio_hist.SetBinError(i, bkg_mc.GetBinError(i) / bkg_mc.GetBinContent(i))
            else:
                ratio_hist.SetBinError(i, 1e-99)
            ratio_hist.SetBinContent(i, 1)
        yerr_graph = ROOT.TGraphAsymmErrors()
        yerr_graph.Divide(data, bkg_mc, 'pois')
        for i in range(0, yerr_graph.GetN() + 1):
            err_y_lo = yerr_graph.GetErrorYlow(i)
            err_y_hi = yerr_graph.GetErrorYhigh(i)
            yerr_graph.SetPointError(i, 0,0,err_y_lo,err_y_hi)

        CMS.cmsDraw(yerr_graph, "P", mcolor=ROOT.kBlack)
        # CMS.cmsDraw(yerr_graph, "e2same", lwidth=100, msize=0, fcolor=ROOT.kBlack, fstyle=3004)
        CMS.cmsDraw(ratio_hist, "e2same0", lwidth=100, msize=0, fcolor=ROOT.kBlack, fstyle=3004)
        ref_line = ROOT.TLine(x_min, 1, x_max, 1)
        CMS.cmsDrawLine(ref_line, lcolor=ROOT.kBlack, lstyle=ROOT.kDotted)

    if do_ratio:
        canv.cd(1)
    CMS.cmsCanvasResetAxes(ROOT.gPad, x_min, x_max, y_min, (y_max - y_min) / 0.65 + y_min)
    canv.Update()
    CMS.SaveCanvas(canv, "{}.pdf".format(os.path.join(args.output, name)), False)
    CMS.SaveCanvas(canv, "{}.png".format(os.path.join(args.output, name)), False)

    if do_ratio:
        canv.cd(1)
    CMS.cmsCanvasResetAxes(ROOT.gPad, x_min, x_max, y_min_log, y_min_log * ((y_max / y_min_log) ** (1 / 0.65)))
    ROOT.gPad.SetLogy()
    canv.Update()
    CMS.SaveCanvas(canv, "{}_log.pdf".format(os.path.join(args.output, name)), False)
    CMS.SaveCanvas(canv, "{}_log.png".format(os.path.join(args.output, name)), True)


# --------------------------------------------------
# Function to loop over plots and create canvases
# --------------------------------------------------
def makeplots(data_files, bkg_files, sig_files, bkg_legend, sig_legend, bkg_colors, sig_colors,
              sig_scale, scale_to_data, ratio, norm, data_legend=["Data"]):
    """
    Open ROOT files, retrieve histograms, and process each plot.
    
    :param data_files: List of data ROOT file paths.
    :param bkg_files: List of background ROOT file paths.
    :param sig_files: List of signal ROOT file paths.
    :param bkg_legend: List of legend names for backgrounds.
    :param sig_legend: List of legend names for signals.
    :param bkg_colors: List of background colors.
    :param sig_colors: List of signal colors.
    :param sig_scale: List of signal scale factors.
    :param scale_to_data: Boolean flag to scale backgrounds to data.
    :param ratio: Boolean flag to plot ratio.
    :param norm: Boolean flag to normalize histograms.
    """
    assert len(bkg_files) == len(bkg_legend), "Number of background files and legends must match."
    if len(sig_scale) == 1:
        sig_scale = len(sig_files) * sig_scale
    elif len(sig_scale) > 1:
        assert len(sig_files) == len(sig_scale), "Mismatch in signal files and scale factors."

    legends = {'bkg': bkg_legend, 'sig': sig_legend, 'data':data_legend}
    colors =  {'bkg': bkg_colors, 'sig': sig_colors}

    # Open ROOT files for data, background, and signal
    file_dict = {
        'data': [ROOT.TFile.Open(fn) for fn in data_files],
        'bkg': [ROOT.TFile.Open(fn) for fn in bkg_files],
        'sig': [ROOT.TFile.Open(fn) for fn in sig_files]
    }

    # Determine the directory and available plots
    dir_name = args.dirs[0] if (args.dirs and len(args.dirs) > 0) else ""
    if dir_name:
        if len(file_dict['data']) > 0:
            fdir = file_dict['data'][0].Get(dir_name)
        elif len(file_dict['bkg']) > 0:
            fdir = file_dict['bkg'][0].Get(dir_name)
        else:
            fdir = file_dict['sig'][0].Get(dir_name)

        if not fdir:
            print("{} not available in {}!".format(args.dirs[0], file_dict['data'][0].GetName()))
        plots = [key.GetName() for key in fdir.GetListOfKeys()]
        dir_name += '/'
    else:
        plots = [key.GetName() for key in file_dict['data'][0].GetListOfKeys()]

    # Process each plot
    for plot_name in plots:
        hs = {}
        do_plot = False
        for ftype in file_dict:
            hs.setdefault(ftype, [])
            for f in file_dict[ftype]:
                h = f.Get(dir_name + plot_name)
                if not h:
                    print('{} is not available in {}!'.format(dir_name + plot_name, f.GetName()))
                    continue
                if 'TH1' not in str(type(h)):
                    break
                h.SetDirectory(0)
                h = h_command(h)
                hs[ftype].append(h)
                do_plot = True
        if do_plot:
            comparehists_cms(
                plot_name, hs, colors, legends,
                sig_scale=sig_scale,
                scale_to_data=scale_to_data,
                ratio=ratio,
                norm=norm
            )

    # Close all opened files
    for ftype in file_dict:
        for f in file_dict[ftype]:
            f.Close()


# --------------------------------------------------
# Main execution function
# --------------------------------------------------
def main():
    if not os.path.exists(args.output):
        os.makedirs(args.output)
    makeplots(
        data_files=args.data,
        bkg_files=args.bkg,
        sig_files=args.signal,
        bkg_legend=args.bkgnice,
        sig_legend=args.signice,
        bkg_colors=bkg_colors,
        sig_colors=signal_colors,
        sig_scale=args.sig_scale,
        scale_to_data=args.scale_to_data,
        ratio=args.ratio,
        norm=args.norm,
        data_legend=args.datanice
    )


if __name__ == "__main__":
    main()
