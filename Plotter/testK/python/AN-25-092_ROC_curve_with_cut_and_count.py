import os

import ROOT


ROOT.gROOT.SetBatch(True)
ROOT.gStyle.SetOptStat(0)
ROOT.gStyle.SetOptTitle(0)
ROOT.gStyle.SetTitleFont(42, "XYZ")
ROOT.gStyle.SetLabelFont(42, "XYZ")
ROOT.gStyle.SetTitleSize(0.046, "XYZ")
ROOT.gStyle.SetLabelSize(0.040, "XYZ")
ROOT.gStyle.SetPadTickX(1)
ROOT.gStyle.SetPadTickY(1)


BASE_DIR = "/scratch-cbe/users/alikaan.gueven/AN_plots/ParT_hists"
ML_DIR = os.path.join(BASE_DIR, "AN-25-092_ML_plots_inputs")
CUT_AND_COUNT_DIR = os.path.join(BASE_DIR, "AN-25-092_cut_and_count_ROC")
OUT_DIR = os.path.join(CUT_AND_COUNT_DIR, "plots")

ML_HISTOGRAM = "all_evt/Max_ML_score"
ML_BACKGROUND_FILE = os.path.join(ML_DIR, "bkg_run2", "all_run2_hist.root")
ML_SIGNAL_FILE = os.path.join(
    ML_DIR, "sig_run2", "stop_M1000_985_ct20_run2_hist.root"
)

CUT_AND_COUNT_BACKGROUND_FILE = os.path.join(
    CUT_AND_COUNT_DIR, "run2plus3", "bkg_run2plus3_hist.root"
)
CUT_AND_COUNT_SIGNAL_FILE = os.path.join(
    CUT_AND_COUNT_DIR,
    "run2plus3",
    "stopML_M1000_985_ct20_run2plus3_hist.root",
)
CUT_AND_COUNT_HISTOGRAM = "all_SDVSecVtx_cc1/SDVSecVtx_LxySig"
CUT_AND_COUNT_THRESHOLD = 20.0


def open_root_file(path):
    root_file = ROOT.TFile.Open(path)
    if not root_file or root_file.IsZombie():
        raise OSError(f"Could not open ROOT file: {path}")
    return root_file


def get_histogram(root_file, name):
    histogram = root_file.Get(name)
    if not histogram:
        raise KeyError(f"Histogram '{name}' not found in {root_file.GetName()}")
    return histogram


def integral_with_overflow(histogram):
    return histogram.Integral(1, histogram.GetNbinsX() + 1)


def make_ml_roc(signal_histogram, background_histogram):
    n_bins = signal_histogram.GetNbinsX()
    if background_histogram.GetNbinsX() != n_bins:
        raise ValueError("The signal and background ML histograms have different binning")

    signal_total = integral_with_overflow(signal_histogram)
    background_total = integral_with_overflow(background_histogram)
    if signal_total <= 0.0 or background_total <= 0.0:
        raise ValueError("The signal and background ML histogram integrals must be positive")

    graph = ROOT.TGraph(n_bins + 1)
    points = []
    for bin_index in range(1, n_bins + 2):
        tpr = signal_histogram.Integral(bin_index, n_bins + 1) / signal_total
        fpr = background_histogram.Integral(bin_index, n_bins + 1) / background_total
        graph.SetPoint(bin_index - 1, tpr, 1.0 - fpr)
        points.append((tpr, 1.0 - fpr))

    points.sort()
    auc = sum(
        (x_next - x) * (y_next + y) / 2.0
        for (x, y), (x_next, y_next) in zip(points, points[1:])
    )

    graph.SetName("ROC_Max_ML_score")
    graph.SetLineColor(ROOT.kBlue + 1)
    graph.SetLineWidth(3)
    return graph, auc


def make_cut_and_count_point(signal_file, background_file):
    signal_histogram = get_histogram(signal_file, CUT_AND_COUNT_HISTOGRAM)
    background_histogram = get_histogram(background_file, CUT_AND_COUNT_HISTOGRAM)
    if signal_histogram.GetXaxis().GetXmin() != background_histogram.GetXaxis().GetXmin():
        raise ValueError("The cut-and-count signal and background axes differ")
    if signal_histogram.GetXaxis().GetXmax() != background_histogram.GetXaxis().GetXmax():
        raise ValueError("The cut-and-count signal and background axes differ")
    if signal_histogram.GetNbinsX() != background_histogram.GetNbinsX():
        raise ValueError("The cut-and-count signal and background binning differs")

    first_passing_bin = signal_histogram.GetXaxis().FindFixBin(
        CUT_AND_COUNT_THRESHOLD
    )
    last_bin = signal_histogram.GetNbinsX() + 1
    signal_total = integral_with_overflow(signal_histogram)
    signal_pass = signal_histogram.Integral(first_passing_bin, last_bin)
    background_total = integral_with_overflow(background_histogram)
    background_pass = background_histogram.Integral(first_passing_bin, last_bin)
    if signal_total <= 0.0 or background_total <= 0.0:
        raise ValueError("The cut-and-count baseline integrals must be positive")

    tpr = signal_pass / signal_total
    fpr = background_pass / background_total
    if not 0.0 <= tpr <= 1.0 or not 0.0 <= fpr <= 1.0:
        raise ValueError(f"Invalid cut-and-count efficiencies: TPR={tpr}, FPR={fpr}")

    point = ROOT.TGraph(1)
    point.SetPoint(0, tpr, 1.0 - fpr)
    point.SetName("ROC_cut_and_count_LxySig20")
    point.SetMarkerStyle(20)
    point.SetMarkerSize(1.6)
    point.SetMarkerColor(ROOT.kRed + 1)
    point.SetLineColor(ROOT.kRed + 1)

    yields = {
        "signal_baseline": signal_total,
        "signal_selected": signal_pass,
        "background_baseline": background_total,
        "background_selected": background_pass,
    }
    return point, tpr, fpr, yields


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    ml_background_file = open_root_file(ML_BACKGROUND_FILE)
    ml_signal_file = open_root_file(ML_SIGNAL_FILE)
    cut_background_file = open_root_file(CUT_AND_COUNT_BACKGROUND_FILE)
    cut_signal_file = open_root_file(CUT_AND_COUNT_SIGNAL_FILE)

    ml_background = get_histogram(ml_background_file, ML_HISTOGRAM)
    ml_signal = get_histogram(ml_signal_file, ML_HISTOGRAM)
    ml_roc, auc = make_ml_roc(ml_signal, ml_background)
    cut_point, cut_tpr, cut_fpr, yields = make_cut_and_count_point(
        cut_signal_file, cut_background_file
    )

    canvas = ROOT.TCanvas("c", "", 800, 700)
    canvas.SetLeftMargin(0.14)
    canvas.SetRightMargin(0.045)
    canvas.SetBottomMargin(0.13)
    canvas.SetTopMargin(0.12)
    canvas.SetTicks(1, 1)

    frame = canvas.DrawFrame(0.0, 0.0, 1.0, 1.0)
    frame.GetXaxis().SetTitle("Signal efficiency (TPR)")
    frame.GetYaxis().SetTitle("Background rejection (1 - FPR)")

    random_classifier = ROOT.TLine(0.0, 1.0, 1.0, 0.0)
    random_classifier.SetLineStyle(2)
    random_classifier.SetLineColor(ROOT.kGray + 2)
    random_classifier.SetLineWidth(2)
    random_classifier.Draw()
    ml_roc.Draw("L SAME")
    cut_point.Draw("P SAME")

    legend = ROOT.TLegend(0.20, 0.36, 0.53, 0.50)
    legend.SetBorderSize(0)
    legend.SetFillStyle(0)
    legend.SetTextFont(42)
    legend.SetTextSize(0.030)
    legend.AddEntry(ml_roc, "ParT", "l")
    legend.AddEntry(cut_point, "Cut&count", "p")
    legend.AddEntry(random_classifier, "Random classifier", "l")
    legend.Draw()

    latex = ROOT.TLatex()
    latex.SetNDC(True)
    latex.SetTextColor(ROOT.kBlack)
    latex.SetTextAlign(11)
    latex.SetTextFont(61)
    latex.SetTextSize(0.050)
    latex.DrawLatex(0.138, 0.894, "CMS")
    latex.SetTextFont(52)
    latex.SetTextSize(0.036)
    latex.DrawLatex(0.234, 0.894, "Simulation Preliminary")
    latex.SetTextFont(42)
    latex.SetTextAlign(31)
    latex.DrawLatex(0.955, 0.894, "100 fb^{-1} (13 TeV)")
    latex.SetTextAlign(11)
    latex.SetTextSize(0.030)
    latex.DrawLatex(0.247, 0.20, f"AUC (Run-2) = {auc:.3f}")

    output_base = os.path.join(OUT_DIR, "AN-25-092_ROC_curve_with_cut_and_count")
    canvas.SaveAs(f"{output_base}.png")
    canvas.SaveAs(f"{output_base}.pdf")

    output_file = ROOT.TFile(f"{output_base}.root", "RECREATE")
    ml_roc.Write()
    cut_point.Write()
    output_file.Close()

    print(f"Cut-and-count signal:     {yields['signal_selected']:.6g} / {yields['signal_baseline']:.6g}")
    print(f"Cut-and-count background: {yields['background_selected']:.6g} / {yields['background_baseline']:.6g}")
    print(f"Cut-and-count TPR:         {cut_tpr:.6f}")
    print(f"Cut-and-count FPR:         {cut_fpr:.6f}")
    print(f"Background rejection:      {1.0 - cut_fpr:.6f}")
    print(f"Saved outputs under:       {OUT_DIR}")

    for root_file in (
        ml_background_file,
        ml_signal_file,
        cut_background_file,
        cut_signal_file,
    ):
        root_file.Close()


if __name__ == "__main__":
    main()
