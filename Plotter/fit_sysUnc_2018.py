import os
import ROOT
import pandas as pd
import math
from array import array

pd.set_option("display.precision", 2)

subdirs = ["jet_nom_met_smear_2018",
           "jet_jerdown_met_smear_jerdown_2018",
           "jet_jerup_met_smear_jerup_2018",
           "jet_jesdown_met_smear_jesdown_2018",
           "jet_jesup_met_smear_jesup_2018",
           "jet_nom_met_smear_uedown_2018",
           "jet_nom_met_smear_ueup_2018"]

inputDir = "/scratch-cbe/users/alikaan.gueven/AN_plots/jetmet_histograms"
outDir = os.path.join(inputDir, "same_mass_comparison")
os.makedirs(outDir, exist_ok=True)


debug = False

titles = [
    "JER syst 2018 region C",
    "JES syst 2018 region C",
    "UE  syst 2018 region C"
]

def plot_df(df_n, df_s, signal, SR):
    assert (signal == "stop" or signal == "C1N2")
    assert (SR == "A" or SR == "C")
    c1 = ROOT.TCanvas('c1', 'c1', 1200, 1000 )
    c1.SetBottomMargin(0.15)

    sameMass          = []
    sameMassErrors    = []
    data_to_fit       = []
    errs_to_fit       = []

    for mass in df_n.index:
        # print(mass)
        sameMass.append(ROOT.TH1F(f'h_{mass}', signal + f'_{mass}', 4, 0, 3))
        sameMassErrors.append(ROOT.TH1F(f'herr_{mass}', signal + f'_{mass}', 4, 0, 3))
        for i, ct in enumerate(df_n.columns):
            # print('Bin content: ', i, df_n.loc[mass].iloc[i])
            # print('Bin error: ', i, df_s.loc[mass].iloc[i])
 
            sameMass[-1].SetBinContent(i+1, df_n.loc[mass].iloc[i])
            sameMass[-1].GetXaxis().SetBinLabel(i+1, ct)

            sameMassErrors[-1].SetBinContent(i+1, df_n.loc[mass].iloc[i])
            sameMassErrors[-1].SetBinError(i+1,   df_s.loc[mass].iloc[i])
            sameMassErrors[-1].GetXaxis().SetBinLabel(i+1, ct)
            
            if df_n.loc[mass].iloc[i] != 0:
                # print("mass: ", mass)
                data_to_fit.append(df_n.loc[mass].iloc[i])
                errs_to_fit.append(df_s.loc[mass].iloc[i])
            else: pass

    histogram_to_fit = ROOT.TH1F(f'hist_to_fit', 'Fit Values', len(data_to_fit), 0, len(data_to_fit) - 1)
    for i in range(len(data_to_fit)):
        histogram_to_fit.SetBinContent(i+1, data_to_fit[i])
        histogram_to_fit.SetBinError(i+1,   errs_to_fit[i])
    
    fit_function = ROOT.TF1("fit_function", "[0]", -10, len(data_to_fit) +100)
    histogram_to_fit.Fit("fit_function")
    print("data_to_fit: ", data_to_fit)
            
    
    ROOT.gStyle.SetErrorX(0.)
    ROOT.gStyle.SetEndErrorSize(4)
    ROOT.gStyle.SetOptFit(1)
    
    mycolors = [ROOT.kSpring-4, ROOT.kTeal, ROOT.kAzure+6]
    for i, hist in enumerate(sameMass):
        hist.SetFillColor(mycolors[i])
        hist.SetLineColor(ROOT.kBlack)
        hist.SetMarkerColor(mycolors[i])
        hist.SetMarkerStyle(21)
        hist.SetMarkerSize(.9)
        hist.SetBarWidth(0.2)
        hist.SetBarOffset(0.2 + i*0.2)

        if i==0:
            hist.Draw('b')
            hist.SetMinimum(0)
            hist.SetMaximum(20)

            hist.SetStats(0)
            hist.SetTitle(subdir.replace('down', ''))
            hist.GetXaxis().SetTitle('c#tau (mm)')
            hist.GetYaxis().SetTitle('Uncertainty (%)')
            hist.GetXaxis().SetLabelSize(0.025)
            hist.GetXaxis().SetTitleSize(0.02)
            hist.GetXaxis().SetTitleOffset(0.60)

        else:
            hist.Draw('b SAME')

            
    for i, hist in enumerate(sameMassErrors):
        hist.SetBarWidth(0.2)
        hist.SetBarOffset(0.2 + i*0.2)
        # hist.SetFillStyle(3353)
        hist.SetMarkerStyle(21)
        hist.SetMarkerSize(.9)
        hist.SetLineColor(ROOT.kBlack)
        # hist.SetFillColor(ROOT.kBlack)
        hist.Draw('e0 SAME')

    # histogram_to_fit.Draw('func same')
    fit_function.Draw('sames')
    
    legend = ROOT.TLegend(0.6,0.7,0.88,0.88)
    for i, mass in enumerate(df_n.index):
        legend.AddEntry(sameMass[i], signal + f'_{mass}', 'lep')
    legend.SetTextSize(0.03)
    legend.Draw()

    pt = ROOT.TPaveText(.15, .75, .35, .85, "NDC") # casting shadow on Bottom Left and using NormaliZed Coordiantes
    chi2 = fit_function.GetChisquare ()
    ndof = fit_function.GetNDF()
    prob = fit_function.GetProb()
    par = fit_function.GetParameter(0)
    parerr = fit_function.GetParError(0)
    if ndof != 0:
        pt.AddText("#chi^{2}/ndf = " + f"{chi2/ndof:.2g}")
        pt.AddText("P(#chi^{2}, ndf) = " + f"{prob:.2g}")
    else:
        pt.AddText("ndof = " + f"{ndof:.2g}")
    
    pt.AddText("y = " + f"{par:.2g}" + "#pm" + f"{parerr:.2g}")
    pt.Draw()
    
    # c1.SetLogy()
    c1.SaveAs(os.path.join(outDir, signal + '2018_' + subdir.replace('down', '') + '_SR_' + SR + '.png'))
    # ----------------------------------------------------------------------------------------------------



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

    # print(stop_dfC_n)
    # print(stop_dfC_s)
    # break

    # Start plotting
    plot_df(stop_dfA_n, stop_dfA_s, "stop", "A")
    plot_df(stop_dfC_n, stop_dfC_s, "stop", "C")

    