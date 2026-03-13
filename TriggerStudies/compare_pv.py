import ROOT
import os
import glob
ROOT.gROOT.SetBatch(True)

base_dir = "/scratch/lisa.benato/SDV/trigger_muon_histo_IsoMu27/"

# --- user configuration
ch_era="2017"
muon_eras = ["muon2017b","muon2017c","muon2017d","muon2017e","muon2017f","muon2017g","muon2017h"]
ch_era="2018"
muon_eras = ["muon2018a","muon2018b","muon2018c","muon2018d"]

base_dir = "/scratch/lisa.benato/SDV/trigger_muon_histo_IsoMu27_run3/"

ch_era="2022pre"
muon_eras = ["muon2022prec","muon2022pred"]

ch_era="2022post"
muon_eras = ["muon2022poste","muon2022postf","muon2022postg"]

#ch_era="2023pre"
#muon_eras = ["muon02023prec","muon12023prec"]

#ch_era="2023post"
#muon_eras = ["muon02023postd","muon12023postd"]

# find all WJets folders automatically
wjets_dirs = [d for d in os.listdir(base_dir) if (d.startswith("wjetstolnu") and ch_era in d)]

# container for histograms
muon_hists = {}
wjets_hist = None

# helper function to sum histograms inside a folder
def get_hist_from_dir(folder):

    hist_sum = None
    root_files = glob.glob(os.path.join(folder, "*.root"))

    #print("Collected root files:",root_files)

    for rf in root_files:

        f = ROOT.TFile.Open(rf)
        if not f or f.IsZombie():
            continue

        h = f.Get("All_evt/PV_npvsGood")

        if not h:
            print("Histogram not found in:", rf)
            f.Close()
            continue

        h_clone = h.Clone()
        h_clone.SetDirectory(0)

        if hist_sum is None:
            hist_sum = h_clone
        else:
            hist_sum.Add(h_clone)

        f.Close()
        
    #print(hist_sum.Print())
    return hist_sum


def get_hist_from_dir_old(folder):

    hist_sum = None

    root_files = glob.glob(os.path.join(folder,"*.root"))

    for rf in root_files:

        f = ROOT.TFile.Open(rf)
        if not f or f.IsZombie():
            continue

        h = f.Get("All_evt/PV_npvsGood")
        if not h:
            f.Close()
            continue

        h = h.Clone()
        h.SetDirectory(0)

        if hist_sum is None:
            hist_sum = h.Clone()
        else:
            hist_sum.Add(h)

        f.Close()

    return hist_sum


# --- process muon eras
for era in muon_eras:

    folder = os.path.join(base_dir, era)
    print("Looking for root files in ..", folder)
    hist = get_hist_from_dir(folder)

    if hist:
        hist.SetLineWidth(3)
        muon_hists[era] = hist


# --- process WJets (all folders combined)
for d in wjets_dirs:

    folder = os.path.join(base_dir, d)
    hist = get_hist_from_dir(folder)

    if hist:

        if wjets_hist is None:
            wjets_hist = hist.Clone("wjets_total")
        else:
            wjets_hist.Add(hist)

if wjets_hist:
    wjets_hist.SetLineColor(ROOT.kBlack)
    wjets_hist.SetLineWidth(1)
    wjets_hist.SetFillColorAlpha(ROOT.kBlack,0.2)


# --- plotting
c = ROOT.TCanvas("c","nPV comparison",800,700)

legend = ROOT.TLegend(0.65,0.65,0.88,0.88)

#colors = [ROOT.kRed+1, ROOT.kBlue+1, ROOT.kGreen+2, ROOT.kMagenta+1]
colors = [
    ROOT.kRed+1,
    ROOT.kBlue+1,
    ROOT.kGreen+2,
    ROOT.kMagenta+1,
    ROOT.kOrange+7,
    ROOT.kCyan+2,
    ROOT.kViolet+1,
    ROOT.kTeal+3,
    ROOT.kPink+6,
    ROOT.kAzure+1,
    ROOT.kSpring+5,
    ROOT.kYellow+2
]

for i,(era,h) in enumerate(muon_hists.items()):

    print(i,era,h.Print())
    h.SetLineColor(colors[i])
    h.SetStats(0)
    h.SetTitle("SingleMuon "+ch_era)

    h.Scale(1./h.Integral())

    if i==0:
        h.Draw("hist")
    else:
        h.Draw("hist same")

    legend.AddEntry(h,era,"l")
    h.SetMaximum(0.07)
    h.GetXaxis().SetTitle("n PV")

# draw WJets
if wjets_hist:
    wjets_hist.Scale(1./wjets_hist.Integral())
    wjets_hist.Draw("hist same")
    legend.AddEntry(wjets_hist,"WJets","F")

legend.Draw()

c.SaveAs("plot_pu/nPV_comparison_"+ch_era+".png")
c.SaveAs("plot_pu/nPV_comparison_"+ch_era+".pdf")
