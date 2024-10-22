import os
import ROOT
import pandas as pd
import math
from array import array

pd.set_option("display.precision", 2)

subdirs = ["jet_nom_met_smear_2017",
           "jet_jerdown_met_smear_jerdown_2017",
           "jet_jerup_met_smear_jerup_2017",
           "jet_jesdown_met_smear_jesdown_2017",
           "jet_jesup_met_smear_jesup_2017",
           "jet_nom_met_smear_uedown_2017",
           "jet_nom_met_smear_ueup_2017"]

inputDir = "/scratch-cbe/users/alikaan.gueven/AN_plots/jetmet_histograms"
outDir = os.path.join(inputDir, "same_mass_comparison")
os.makedirs(outDir, exist_ok=True)


debug = False

titles = [
    "JER syst 2017 region C",
    "JES syst 2017 region C",
    "UE syst 2017 region C"
]

def plot_df(df_n, df_s, signal, SR):
    assert (signal == "stop" or signal == "C1N2")
    assert (SR == "A" or SR == "C")
    c1 = ROOT.TCanvas('c1', 'c1', 1200, 1000 )
    c1.SetBottomMargin(0.15)

    sameMass          = []
    sameMassClone     = []

    for mass in df_n.index:
        # print(mass)
        sameMass.append(ROOT.TH1F(f'h_{mass}', signal + f'_{mass}', 4, 0, 3))
        for i, ct in enumerate(df_n.columns):
            # print('Bin content: ', i, df_n.loc[mass].iloc[i])
            # print('Bin error: ', i, df_s.loc[mass].iloc[i])
            sameMass[-1].SetBinContent(i+1, df_n.loc[mass].iloc[i])
            sameMass[-1].SetBinError(i+1, df_s.loc[mass].iloc[i])
            sameMass[-1].GetXaxis().SetBinLabel(i+1, ct)
    
    ROOT.gStyle.SetErrorX(0.)
        
    for i, hist in enumerate(sameMass):
        hist.SetLineColor(i+1)
        hist.SetMarkerColor(i+1)
        hist.SetMarkerStyle(21)
        hist.SetMarkerSize(.9)

        if i==0:
            hist.Draw('E1 E0')
            hist.SetMinimum(-2)
            hist.SetMaximum(30)

            hist.SetStats(0)
            hist.SetTitle(subdir.replace('down', ''))
            hist.GetXaxis().SetTitle('c#tau (mm)')
            hist.GetYaxis().SetTitle('Uncertainty (%)')
            hist.GetXaxis().SetLabelSize(0.025)
            hist.GetXaxis().SetTitleSize(0.02)
            hist.GetXaxis().SetTitleOffset(0.60)

        else:
            hist.Draw('E1 E0 SAME')

        sameMassClone.append(hist.Clone())

    for i, hist in enumerate(sameMass):
        sameMassClone[i].Draw('P SAME')
    
    legend = ROOT.TLegend(0.6,0.7,0.88,0.88)
    for i, mass in enumerate(df_n.index):
        legend.AddEntry(sameMass[i], signal + f'_{mass}', 'lep')
    legend.SetTextSize(0.03)
    legend.Draw()
    
    c1.SaveAs(os.path.join(outDir, signal + '2017_' + subdir.replace('down', '') + '_SR_' + SR + '.png'))

for subdir in subdirs:
    if subdir[-9:-5] != 'down':
        continue

    print()
    print("Plotting", subdir[:-9])
    print()

    subdir_down = subdir
    subdir_up   = subdir.replace('down', 'up')

    
    storeDir_down = os.path.join(inputDir, subdir_down)
    storeDir_up = os.path.join(inputDir, subdir_up)
    plotDir = os.path.join(storeDir_down, "figures_sysunc")

    store_down = pd.HDFStore(os.path.join(storeDir_down, 'SysUnc.h5'), 'r')
    store_up   = pd.HDFStore(os.path.join(storeDir_up,   'SysUnc.h5'), 'r')


    stop_dfA_n = pd.DataFrame(columns=['ct0p2', 'ct2', 'ct20', 'ct200'], index=['M600', 'M1000', 'M1400'], dtype=float)
    stop_dfA_s = pd.DataFrame(columns=['ct0p2', 'ct2', 'ct20', 'ct200'], index=['M600', 'M1000', 'M1400'], dtype=float)
    C1N2_dfA_n = pd.DataFrame(columns=['ct0p2', 'ct2', 'ct20', 'ct200'], index=['M600', 'M1000', 'M1400'], dtype=float)
    C1N2_dfA_s = pd.DataFrame(columns=['ct0p2', 'ct2', 'ct20', 'ct200'], index=['M600', 'M1000', 'M1400'], dtype=float)

    stop_dfC_n = pd.DataFrame(columns=['ct0p2', 'ct2', 'ct20', 'ct200'], index=['M600', 'M1000', 'M1400'], dtype=float)
    stop_dfC_s = pd.DataFrame(columns=['ct0p2', 'ct2', 'ct20', 'ct200'], index=['M600', 'M1000', 'M1400'], dtype=float)
    C1N2_dfC_n = pd.DataFrame(columns=['ct0p2', 'ct2', 'ct20', 'ct200'], index=['M600', 'M1000', 'M1400'], dtype=float)
    C1N2_dfC_s = pd.DataFrame(columns=['ct0p2', 'ct2', 'ct20', 'ct200'], index=['M600', 'M1000', 'M1400'], dtype=float)


    for sig in store_down.keys():
        sig = sig[1:]
        sig_split = sig.split('_')
        if sig_split[-1] == 's':
            continue

        SR_A_values_n = [abs(store_down[sig].loc['SR', 'A']), abs(store_up[sig].loc['SR', 'A'])]
        SR_A_values_s = [store_down[sig.replace('_n', '_s')].loc['SR', 'A'], store_up[sig.replace('_n', '_s')].loc['SR', 'A']]
        SR_A_max_values_n = max(SR_A_values_n)
        SR_A_argmax_values_n = SR_A_values_n.index(SR_A_max_values_n)

        SR_C_values_n = [abs(store_down[sig].loc['SR', 'C']), abs(store_up[sig].loc['SR', 'C'])]
        SR_C_values_s = [store_down[sig.replace('_n', '_s')].loc['SR', 'C'], store_up[sig.replace('_n', '_s')].loc['SR', 'C']]
        SR_C_max_values_n = max(SR_C_values_n)
        SR_C_argmax_values_n = SR_C_values_n.index(SR_C_max_values_n)


        if sig_split[0] == 'stop':
            stop_dfA_n.loc[sig_split[1], sig_split[3]] = SR_A_max_values_n
            stop_dfA_s.loc[sig_split[1], sig_split[3]] = SR_A_values_s[SR_A_argmax_values_n]

            stop_dfC_n.loc[sig_split[1], sig_split[3]] = SR_C_max_values_n
            stop_dfC_s.loc[sig_split[1], sig_split[3]] = SR_C_values_s[SR_C_argmax_values_n]

        elif sig_split[0] == 'C1N2':
            C1N2_dfA_n.loc[sig_split[1], sig_split[3]] = SR_A_max_values_n
            C1N2_dfA_s.loc[sig_split[1], sig_split[3]] = SR_A_values_s[SR_A_argmax_values_n]

            C1N2_dfC_n.loc[sig_split[1], sig_split[3]] = SR_C_max_values_n
            C1N2_dfC_s.loc[sig_split[1], sig_split[3]] = SR_C_values_s[SR_C_argmax_values_n]


    print('Mean SR_A_all: ', stop_dfA_n.mean(axis=None))
    print('Mean SR_C_all: ', stop_dfC_n.mean(axis=None))
    
    stop_dfA_n *= 100 # Go to percentage (%)
    stop_dfA_s *= 100 # Go to percentage (%)
    C1N2_dfA_n *= 100 # Go to percentage (%)
    C1N2_dfA_s *= 100 # Go to percentage (%)

    stop_dfC_n *= 100 # Go to percentage (%)
    stop_dfC_s *= 100 # Go to percentage (%)
    C1N2_dfC_n *= 100 # Go to percentage (%)
    C1N2_dfC_s *= 100 # Go to percentage (%)


    # Start plotting
    plot_df(stop_dfA_n, stop_dfA_s, "stop", "A")
    plot_df(stop_dfC_n, stop_dfC_s, "stop", "C")

    