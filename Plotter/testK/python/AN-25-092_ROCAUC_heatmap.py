"""
Make AUC heatmaps from the 2018 signal ROOT files.

The script reads the ML-score histogram used in the ROC script, compares each
signal file in sig18 against the combined 2018 background file, and computes the
area under the ROC curve. Files must end exactly in "_hist.root"; files such as
"_hist0.root" are ignored.

The sample name is interpreted as:
    process_Mparent_Mdaughter_ctVALUE_run2_hist.root

For each process and parent mass, the script writes one heatmap. The x axis is
Delta M = Mparent - Mdaughter, and the y axis is ctau.
"""

import os
import re
from collections import defaultdict

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
ROOT.gStyle.SetNumberContours(255)
ROOT.gStyle.SetPalette(getattr(ROOT, "kViridis", 112))


# uniquedir = "AN-25-092_ML_plots_ROC"
uniquedir = "AN-25-092_ML_plots_inputs"



BASE_DIR = f"/scratch-cbe/users/alikaan.gueven/AN_plots/ParT_hists/{uniquedir}"
SIG_DIR = f"{BASE_DIR}/sig_run2"
BKG_FILE = f"{BASE_DIR}/bkg_run2/all_run2_hist.root"
OUT_DIR = f"{BASE_DIR}/plots/ROC_AUC_heatmap"
HNAME = "all_evt/Max_ML_score"

SAMPLE_RE = re.compile(r"^(.+)_M(\d+)_(\d+)_ct([0-9]+(?:p[0-9]+)?)_run2_hist\.root$")


def ct_value(text):
    return float(text.replace("p", "."))


def ct_label(value):
    return f"{value:g}"


def get_hist(path, name):
    root_file = ROOT.TFile.Open(path)
    if not root_file or root_file.IsZombie():
        raise RuntimeError(f"Could not open {path}")

    hist = root_file.Get(name)
    if not hist:
        root_file.Close()
        raise RuntimeError(f"Could not find {name} in {path}")

    hist = hist.Clone(f"{hist.GetName()}_{abs(hash(path))}")
    hist.SetDirectory(0)
    root_file.Close()
    return hist


def auc_from_hists(signal, background):
    nbins = signal.GetNbinsX()
    signal_total = signal.Integral(1, nbins + 1)
    background_total = background.Integral(1, nbins + 1)
    if signal_total <= 0.0 or background_total <= 0.0:
        return None

    points = []
    for ibin in range(1, nbins + 2):
        signal_eff = signal.Integral(ibin, nbins + 1) / signal_total
        background_rej = 1.0 - background.Integral(ibin, nbins + 1) / background_total
        points.append((signal_eff, background_rej))

    points = sorted(points)
    return sum(
        (points[i + 1][0] - points[i][0]) * (points[i + 1][1] + points[i][1]) / 2.0
        for i in range(len(points) - 1)
    )


def read_auc_values():
    background = get_hist(BKG_FILE, HNAME)
    groups = defaultdict(dict)

    for fname in sorted(os.listdir(SIG_DIR)):
        if not fname.endswith("_hist.root"):
            continue

        match = SAMPLE_RE.match(fname)
        if not match:
            print(f"Skipping file with unexpected name: {fname}")
            continue

        process, parent_mass, daughter_mass, ct_text = match.groups()
        parent_mass = int(parent_mass)
        delta_m = parent_mass - int(daughter_mass)
        ctau = ct_value(ct_text)

        signal = get_hist(f"{SIG_DIR}/{fname}", HNAME)
        auc = auc_from_hists(signal, background)
        if auc is None:
            print(f"Skipping file with zero integral: {fname}")
            continue

        groups[(process, parent_mass)][(delta_m, ctau)] = auc

    return groups


def draw_text(x, y, text, size=0.030, colour=ROOT.kBlack):
    latex = ROOT.TLatex()
    latex.SetTextAlign(22)
    latex.SetTextFont(42)
    latex.SetTextSize(size)
    latex.SetTextColor(colour)
    latex.DrawLatex(x, y, text)


def draw_header(process, mass):
    latex = ROOT.TLatex()
    latex.SetNDC(True)
    latex.SetTextColor(ROOT.kBlack)
    latex.SetTextAlign(11)
    latex.SetTextFont(61)
    latex.SetTextSize(0.055)
    latex.DrawLatex(0.120, 0.815, "CMS")
    latex.SetTextFont(52)
    latex.SetTextSize(0.040)
    latex.DrawLatex(0.220, 0.815, "Simulation Preliminary")
    latex.SetTextFont(42)
    latex.SetTextAlign(31)
    latex.DrawLatex(0.855, 0.815, f"{process}, M = {mass} GeV")


def make_heatmap(process, mass, values, root_output):
    delta_ms = sorted({point[0] for point in values})
    ctaus = sorted({point[1] for point in values})

    hist_name = f"auc_heatmap_{process}_M{mass}"
    hist = ROOT.TH2D(
        hist_name,
        "",
        len(delta_ms),
        0.5,
        len(delta_ms) + 0.5,
        len(ctaus),
        0.5,
        len(ctaus) + 0.5,
    )
    hist.SetMinimum(0.0)
    hist.SetMaximum(1.0)

    for ibin, delta_m in enumerate(delta_ms, start=1):
        hist.GetXaxis().SetBinLabel(ibin, str(delta_m))
    for ibin, ctau in enumerate(ctaus, start=1):
        hist.GetYaxis().SetBinLabel(ibin, ct_label(ctau))

    for (delta_m, ctau), auc in values.items():
        hist.SetBinContent(delta_ms.index(delta_m) + 1, ctaus.index(ctau) + 1, auc)

    canvas = ROOT.TCanvas(f"c_{hist_name}", "", 900, 760)
    canvas.SetLeftMargin(0.12)
    canvas.SetRightMargin(0.15)
    canvas.SetBottomMargin(0.13)
    canvas.SetTopMargin(0.20)
    canvas.SetTicks(1, 1)

    hist.GetXaxis().SetTitle("#Delta M [GeV]")
    hist.GetYaxis().SetTitle("c#tau [mm]")
    hist.GetZaxis().SetTitle("AUC")
    hist.GetXaxis().SetTitleOffset(1.10)
    hist.GetYaxis().SetTitleOffset(1.15)
    hist.GetZaxis().SetTitleOffset(1.10)
    hist.GetXaxis().LabelsOption("h")
    hist.Draw("COLZ")

    missing_box = ROOT.TBox()
    missing_box.SetFillColor(ROOT.kWhite)
    missing_box.SetLineColor(ROOT.kGray + 1)
    missing_box.SetLineWidth(1)

    for ix in range(1, len(delta_ms) + 1):
        for iy in range(1, len(ctaus) + 1):
            delta_m = delta_ms[ix - 1]
            ctau = ctaus[iy - 1]
            if (delta_m, ctau) not in values:
                missing_box.DrawBox(ix - 0.5, iy - 0.5, ix + 0.5, iy + 0.5)

    for (delta_m, ctau), auc in values.items():
        ix = delta_ms.index(delta_m) + 1
        iy = ctaus.index(ctau) + 1
        draw_text(ix, iy, f"{auc:.3f}", colour=ROOT.kWhite if auc < 0.35 else ROOT.kBlack)

    draw_header(process, mass)

    out_base = f"{OUT_DIR}/AN-25-092_ROC_AUC_heatmap_{process}_M{mass}_run2"
    canvas.SaveAs(f"{out_base}.png")
    canvas.SaveAs(f"{out_base}.pdf")

    root_output.cd()
    hist.Write()
    canvas.Write()
    print(f"Wrote {out_base}.png")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    groups = read_auc_values()

    root_output = ROOT.TFile(f"{OUT_DIR}/AN-25-092_ROC_AUC_heatmaps_run2.root", "RECREATE")
    for (process, mass), values in sorted(groups.items()):
        make_heatmap(process, mass, values, root_output)
    root_output.Close()


if __name__ == "__main__":
    main()
