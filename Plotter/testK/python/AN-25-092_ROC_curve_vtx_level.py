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


BASE_DIR = (
    "/scratch-cbe/users/alikaan.gueven/AN_plots/ParT_hists/"
    "AN-25-092_cut_and_count_ROC_v2"
)
INPUT_DIR = os.path.join(BASE_DIR, "run2plus3")
OUT_DIR = os.path.join(BASE_DIR, "plots")

SIGNAL_FILE = os.path.join(
    INPUT_DIR, "stopML_M1000_985_ct20_run2plus3_hist.root"
)
BACKGROUND_FILE = os.path.join(INPUT_DIR, "bkg_run2plus3_hist.root")

ML_HISTOGRAM = "all_SDVSecVtx_all/ML_score"
ALL_VERTEX_HISTOGRAM = "all_SDVSecVtx_all/SDVSecVtx_LxySig"
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


def integral_with_overflow(histogram, first_bin=1):
    return histogram.Integral(first_bin, histogram.GetNbinsX() + 1)


def check_matching_binning(signal_histogram, background_histogram, label):
    signal_axis = signal_histogram.GetXaxis()
    background_axis = background_histogram.GetXaxis()
    same_binning = (
        signal_histogram.GetNbinsX() == background_histogram.GetNbinsX()
        and signal_axis.GetXmin() == background_axis.GetXmin()
        and signal_axis.GetXmax() == background_axis.GetXmax()
    )
    if not same_binning:
        raise ValueError(f"The signal and background {label} histograms differ in binning")


def make_ml_roc(signal_histogram, background_histogram):
    check_matching_binning(signal_histogram, background_histogram, "ML-score")
    n_bins = signal_histogram.GetNbinsX()
    signal_total = integral_with_overflow(signal_histogram)
    background_total = integral_with_overflow(background_histogram)
    if signal_total <= 0.0 or background_total <= 0.0:
        raise ValueError("The signal and background ML-score integrals must be positive")

    graph = ROOT.TGraph(n_bins + 1)
    points = []
    for bin_index in range(1, n_bins + 2):
        tpr = integral_with_overflow(signal_histogram, bin_index) / signal_total
        fpr = integral_with_overflow(background_histogram, bin_index) / background_total
        graph.SetPoint(bin_index - 1, tpr, fpr)
        points.append((tpr, 1.0 - fpr))

    points.sort()
    auc = sum(
        (x_next - x) * (y_next + y) / 2.0
        for (x, y), (x_next, y_next) in zip(points, points[1:])
    )

    graph.SetName("ROC_vertex_ML_score")
    graph.SetLineColor(ROOT.kBlue + 1)
    graph.SetLineWidth(3)
    return graph, auc, signal_total, background_total


def make_cut_and_count_point(
    signal_all, signal_selected, background_all, background_selected
):
    check_matching_binning(
        signal_all, background_all, "all-vertex LxySig"
    )
    check_matching_binning(
        signal_selected, background_selected, "cut-and-count LxySig"
    )
    check_matching_binning(
        signal_all, signal_selected, "signal LxySig"
    )
    check_matching_binning(
        background_all, background_selected, "background LxySig"
    )
    first_passing_bin = signal_selected.GetXaxis().FindFixBin(
        CUT_AND_COUNT_THRESHOLD
    )

    signal_total = integral_with_overflow(signal_all)
    background_total = integral_with_overflow(background_all)
    signal_pass = integral_with_overflow(signal_selected, first_passing_bin)
    background_pass = integral_with_overflow(background_selected, first_passing_bin)
    if signal_total <= 0.0 or background_total <= 0.0:
        raise ValueError("The cut-and-count baseline integrals must be positive")

    tpr = signal_pass / signal_total
    fpr = background_pass / background_total
    if not 0.0 <= tpr <= 1.0 or not 0.0 <= fpr <= 1.0:
        raise ValueError(f"Invalid cut-and-count efficiencies: TPR={tpr}, FPR={fpr}")

    point = ROOT.TGraph(1)
    point.SetPoint(0, tpr, fpr)
    point.SetName("ROC_cut_and_count_LxySig20")
    point.SetMarkerStyle(20)
    point.SetMarkerSize(1.6)
    point.SetMarkerColor(ROOT.kRed + 1)
    point.SetLineColor(ROOT.kRed + 1)

    return point, tpr, fpr, signal_pass, signal_total, background_pass, background_total


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    signal_file = open_root_file(SIGNAL_FILE)
    background_file = open_root_file(BACKGROUND_FILE)

    signal_ml = get_histogram(signal_file, ML_HISTOGRAM)
    background_ml = get_histogram(background_file, ML_HISTOGRAM)
    ml_roc, auc, ml_signal_total, ml_background_total = make_ml_roc(
        signal_ml, background_ml
    )

    signal_all = get_histogram(signal_file, ALL_VERTEX_HISTOGRAM)
    background_all = get_histogram(background_file, ALL_VERTEX_HISTOGRAM)
    signal_cut_and_count = get_histogram(signal_file, CUT_AND_COUNT_HISTOGRAM)
    background_cut_and_count = get_histogram(
        background_file, CUT_AND_COUNT_HISTOGRAM
    )
    (
        cut_point,
        cut_tpr,
        cut_fpr,
        cut_signal_pass,
        cut_signal_total,
        cut_background_pass,
        cut_background_total,
    ) = make_cut_and_count_point(
        signal_all,
        signal_cut_and_count,
        background_all,
        background_cut_and_count,
    )

    canvas = ROOT.TCanvas("c", "", 800, 700)
    canvas.SetLeftMargin(0.14)
    canvas.SetRightMargin(0.045)
    canvas.SetBottomMargin(0.13)
    canvas.SetTopMargin(0.12)
    canvas.SetTicks(1, 1)
    canvas.SetLogy()

    frame = canvas.DrawFrame(0.0, 1.0e-5, 1.0, 1.0)
    frame.GetXaxis().SetTitle("Signal efficiency (TPR)")
    frame.GetYaxis().SetTitle("False-positive rate (FPR)")

    random_classifier = ROOT.TGraph(501)
    random_classifier.SetName("ROC_random_classifier")
    for point_index in range(501):
        value = 10.0 ** (-5.0 + point_index / 100.0)
        random_classifier.SetPoint(point_index, value, value)
    random_classifier.SetLineStyle(2)
    random_classifier.SetLineColor(ROOT.kGray + 2)
    random_classifier.SetLineWidth(2)
    random_classifier.Draw("L SAME")
    ml_roc.Draw("L SAME")
    cut_point.Draw("P SAME")

    legend = ROOT.TLegend(0.62, 0.20, 0.91, 0.34)
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

    output_base = os.path.join(OUT_DIR, "AN-25-092_ROC_curve_vtx_level")
    canvas.SaveAs(f"{output_base}.png")
    canvas.SaveAs(f"{output_base}.pdf")

    output_file = ROOT.TFile(f"{output_base}.root", "RECREATE")
    ml_roc.Write()
    cut_point.Write()
    output_file.Close()

    print(f"ML signal total:          {ml_signal_total:.6g}")
    print(f"ML background total:      {ml_background_total:.6g}")
    print(f"ML AUC:                   {auc:.6f}")
    print(f"Cut-and-count signal:     {cut_signal_pass:.6g} / {cut_signal_total:.6g}")
    print(
        "Cut-and-count background: "
        f"{cut_background_pass:.6g} / {cut_background_total:.6g}"
    )
    print(f"Cut-and-count TPR:        {cut_tpr:.6f}")
    print(f"Cut-and-count FPR:        {cut_fpr:.6f}")
    print(f"Background rejection:     {1.0 - cut_fpr:.6f}")
    print(f"Saved outputs under:      {OUT_DIR}")

    signal_file.Close()
    background_file.Close()


if __name__ == "__main__":
    main()
