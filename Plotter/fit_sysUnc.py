import os
import ROOT
import pandas as pd
import math
from array import array

pd.set_option("display.precision", 2)

# subdirs = [# "jet_nom_met_smear",
           # "jet_jerdown_met_smear_jerdown",
           # "jet_jerup_met_smear_jerup",
           # "jet_jesdown_met_smear_jesdown",
           # "jet_jesup_met_smear_jesup",
           # "jet_nom_met_smear_uedown",
           # "jet_nom_met_smear_ueup"]

subdirs = ["jet_nom_met_smear_2017",
           "jet_jerdown_met_smear_jerdown_2017",
           "jet_jerup_met_smear_jerup_2017",
           "jet_jesdown_met_smear_jesdown_2017",
           "jet_jesup_met_smear_jesup_2017",
           "jet_nom_met_smear_uedown_2017",
           "jet_nom_met_smear_ueup_2017"]

inputDir = "/scratch-cbe/users/alikaan.gueven/AN_plots/jetmet_histograms"

debug = False

titles = [
    "JER syst 2017 region C",
    "JES syst 2017 region C",
    "UE syst 2017 region C"
]

for subdir in subdirs:
    # if subdir[-4:] != 'down':
    #     continue
    if subdir[-9:-5] != 'down':
        continue

    print(subdir)
    print()
    subdir_down = subdir
    subdir_up   = subdir.replace('down', 'up')

    
    storeDir_down = os.path.join(inputDir, subdir_down)
    storeDir_up = os.path.join(inputDir, subdir_up)
    plotDir = os.path.join(storeDir_down, "figures_sysunc")

    store_down = pd.HDFStore(os.path.join(storeDir_down, 'SysUnc.h5'), 'r')
    store_up   = pd.HDFStore(os.path.join(storeDir_up, 'SysUnc.h5'), 'r')

    """
    sample_dict = {}
    for sig in store.keys():
        sig = sig[1:]
        sample_dict[sig] = store[sig].loc['SR', 'C']
    """

    stop_df_n = pd.DataFrame(columns=['ct0p2', 'ct2', 'ct20', 'ct200'], index=['M600', 'M1000', 'M1400'], dtype=float)
    stop_df_s = pd.DataFrame(columns=['ct0p2', 'ct2', 'ct20', 'ct200'], index=['M600', 'M1000', 'M1400'], dtype=float)
    C1N2_df_n = pd.DataFrame(columns=['ct0p2', 'ct2', 'ct20', 'ct200'], index=['M600', 'M1000', 'M1400'], dtype=float)
    C1N2_df_s = pd.DataFrame(columns=['ct0p2', 'ct2', 'ct20', 'ct200'], index=['M600', 'M1000', 'M1400'], dtype=float)

    SR_C_all = []
    for sig in store_down.keys():
        sig = sig[1:]
        sig_split = sig.split('_')
        if sig_split[-1] == 's':
            continue
        values_n = [abs(store_down[sig].loc['SR', 'C']), abs(store_up[sig].loc['SR', 'C'])]
        max_values_n = max(values_n)
        # print('Adding ', sig, ' to the list')
        SR_C_all.append(max_values_n)
    print('SR_C_all: ', SR_C_all)
    print('Mean SR_C_all: ', sum(SR_C_all) / len(SR_C_all))

    for sig in store_down.keys():
        sig = sig[1:]
        sig_split = sig.split('_')
        if sig_split[-1] == 's':
            continue
        values_n = [abs(store_down[sig].loc['SR', 'C']), abs(store_up[sig].loc['SR', 'C'])]
        values_s = [store_down[sig.replace('_n', '_s')].loc['SR', 'C'], store_up[sig.replace('_n', '_s')].loc['SR', 'C']]
        max_values_n = max(values_n)
        argmax_values_n = values_n.index(max_values_n)


        """
        print(sig)
        print('==========================')
        print(store_down[sig].loc['SR', 'C'])
        print(store_up[sig].loc['SR', 'C'])
        print('--------------------------')
        print(store_down[sig.replace('_n', '_s')].loc['SR', 'C'])
        print(store_up[sig.replace('_n', '_s')].loc['SR', 'C'])
        print('--------------------------')
        """


        if sig_split[0] == 'stop':
            stop_df_n.loc[sig_split[1], sig_split[3]] = max_values_n
            stop_df_s.loc[sig_split[1], sig_split[3]] = values_s[argmax_values_n]
        elif sig_split[0] == 'C1N2':
            C1N2_df_n.loc[sig_split[1], sig_split[3]] = max_values_n
            C1N2_df_s.loc[sig_split[1], sig_split[3]] = values_s[argmax_values_n]
    
    stop_df_n *= 100 # Go to percentage (%)
    stop_df_s *= 100 # Go to percentage (%)
    C1N2_df_n *= 100 # Go to percentage (%)
    C1N2_df_s *= 100 # Go to percentage (%)


    if debug:
        stop_df_n[abs(stop_df_n)<0.01] = 0 # Better display
        C1N2_df_n[abs(C1N2_df_n)<0.01] = 0 # Better display
        print('stop_df')
        print(stop_df_n)
        print()
        print('C1N2_df')
        print(C1N2_df_n)
        print()


    # Start plotting

    c1 = ROOT.TCanvas('c1', 'c1', 1200, 1000 )
    c1.SetBottomMargin(0.15)

    sameMass          = []
    sameMassClone     = []
    sameLifetime      = []
    sameLifetimeClone = []

    for mass in stop_df_n.index:
        # print(mass)
        sameMass.append(ROOT.TH1F(f'h_{mass}', f'stop_{mass}', 4, 0, 3))
        for i, ct in enumerate(stop_df_n.columns):
            # print('Bin content: ', i, stop_df_n.loc[mass].iloc[i])
            # print('Bin error: ', i, stop_df_s.loc[mass].iloc[i])
            sameMass[-1].SetBinContent(i+1, stop_df_n.loc[mass].iloc[i])
            sameMass[-1].SetBinError(i+1, stop_df_s.loc[mass].iloc[i])
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
    for i, mass in enumerate(stop_df_n.index):
        legend.AddEntry(sameMass[i], f'stop_{mass}', 'lep')
    legend.SetTextSize(0.03)
    legend.Draw()
    
    c1.SaveAs(os.path.join(inputDir, 'stop2017_' + subdir.replace('down', '') + '_SR_C.png'))

    # Start plotting
    c1 = ROOT.TCanvas('c1', 'c1', 1500, 600 )
    c1.SetBottomMargin(0.15)

    sameMass          = []
    sameMassClone     = []
    sameLifetime      = []
    sameLifetimeClone = []


    for mass in C1N2_df_n.index:
        # print(mass)
        sameMass.append(ROOT.TH1F(f'h_{mass}', f'C1N2_{mass}', 4, 0, 3))
        for i, ct in enumerate(C1N2_df_n.columns):
            # print('Bin content: ', i, C1N2_df_n.loc[mass].iloc[i])
            # print('Bin error: ', i, C1N2_df_s.loc[mass].iloc[i])
            sameMass[-1].SetBinContent(i+1, C1N2_df_n.loc[mass].iloc[i])
            sameMass[-1].SetBinError(i+1, C1N2_df_s.loc[mass].iloc[i])
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
            hist.SetMaximum(70)

            hist.SetStats(0)
            hist.SetTitle(subdir.replace('down', ''))
            hist.GetXaxis().SetTitle('c#tau (mm)')
            hist.GetYaxis().SetTitle('Uncertainty (%)')
            hist.GetXaxis().SetLabelSize(0.05)
            hist.GetXaxis().SetTitleSize(0.04)
            hist.GetXaxis().SetTitleOffset(0.60)

        else:
            hist.Draw('E1 E0 SAME')

        sameMassClone.append(hist.Clone())

    for i, hist in enumerate(sameMass):
        sameMassClone[i].Draw('P SAME')
    
    legend = ROOT.TLegend(0.7,0.7,0.88,0.88)
    for i, mass in enumerate(C1N2_df_n.index):
        legend.AddEntry(sameMass[i], f'C1N2_{mass}', 'lep')
    legend.SetTextSize(0.04)
    legend.Draw()
    
    c1.SaveAs(os.path.join(inputDir, 'C1N2_' + subdir.replace('down', '') + '.png'))
    

    """
    unc   = [value * 100 for sig, value in sample_dict.items()]  # in percent
    unc_e = [abs(value)/2 for value in unc]
    id     = [i for i in range(len(sample_dict))]
    id_e   = [0 for i in range(len(sample_dict))]

    h = ROOT.TH1F('h', 'title', len(id), id[0], id[-1])
    for i, key in enumerate(sample_dict.keys()):
        h.SetBinContent(i+1, unc_e[i])
        h.SetBinError(i+1, unc[i])
        h.GetXaxis().SetBinLabel(i+1, key.split('_')[3][2:])

    h.Draw('E1 E0')
    h.SetMinimum(-20)
    h.SetMaximum(20)

    ROOT.gStyle.SetErrorX(0.)
    h.SetStats(0)
    h.SetTitle('stop_M600')
    h.GetXaxis().SetTitle('#Delta M')
    h.GetYaxis().SetTitle('Uncertainty (%)')
    h.GetXaxis().SetLabelSize(0.05)
    h.GetXaxis().SetTitleSize(0.04)
    h.GetXaxis().SetTitleOffset(0.60)

    hp = h.Clone()
    h.SetMarkerColor(2)
    h.SetMarkerStyle(21)
    h.SetMarkerSize(.9)
    hp.Draw('P SAME')

    # TCanvas.Update() draws the frame, after which one can change it
    c1.Update()
    # c1.GetFrame().SetFillColor( 21 )
    # c1.GetFrame().SetBorderSize( 12 )
    c1.Modified()
    c1.Update()
    c1.SaveAs('tmp.png')
"""
