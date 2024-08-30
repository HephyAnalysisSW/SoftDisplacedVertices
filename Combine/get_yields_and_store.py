
# Example usage:
# 


import ROOT
import os
import matplotlib.pyplot as plt
import numpy as np
import math
import pandas as pd
import seaborn as sns


def calculate_yields(histogram, xLow, yLow, xsplit, ysplit, unblind=True):
    """
    Returns
    -------
    counts : dict (keys are regions)
    errors : dict (keys are regions)
    """
    counts = {}
    errors = {}
    region_dict = { "A": [xsplit, histogram.GetNbinsX() + 1, ysplit, histogram.GetNbinsY() + 1],
                    "B": [xLow, xsplit - 1, ysplit, histogram.GetNbinsY() + 1],
                    "C": [xsplit, histogram.GetNbinsX() + 1, yLow, ysplit - 1],
                    "D": [xLow, xsplit - 1, yLow, ysplit - 1] }

    for region, splits in region_dict.items():
        count = histogram.Integral(int(splits[0]), int(splits[1]), int(splits[2]), int(splits[3]))
        counts[region] = count
        if count == 0:
            errors[region] = 0
            continue
        squared_error = 0.0
        for i in range(splits[0], splits[1]):
            for j in range(splits[2], splits[3]):
                squared_error += histogram.GetBinError(i, j) * histogram.GetBinError(i, j)
        errors[region] = squared_error
    
    if not unblind:
        """
        Asimov dataset --> expectation = observation
        """
        counts['A'] = counts['B'] * counts['C'] / counts['D']
        
        # uncertainty propagation for A = BC/D
        e1 = (counts['C'] / counts['D']) * errors['B']
        e2 = (counts['B'] / counts['D']) * errors['C']
        e3 = (counts['B'] * counts['C'] / (counts['B']**2)) * errors['D']

        errors['A'] = math.sqrt(e1**2 + e2**2 + e3**2)


    return counts, errors



def get_region_boundaries(sample, histdir, histname, MET_bound, LxySig_bound):
    """
    Gets the closest bin number and lower edge given an x,y value.
    """
    region_name, histname = histname.split('.')
    histFile = ROOT.TFile(os.path.join(histdir, f"{sample}_hist.root"))
    hist = histFile.Get(region_name).Get(histname).Clone()

    xSplit = int(hist.GetXaxis().FindBin(MET_bound))
    ySplit = int(hist.GetYaxis().FindBin(LxySig_bound))

    xSplit_val = hist.GetXaxis().GetBinLowEdge(xSplit)
    ySplit_val = hist.GetYaxis().GetBinLowEdge(ySplit)
    return (xSplit, ySplit, xSplit_val, ySplit_val)

def sum_background_hists(bkgSamples, histdir, histname, debug):
    """
    Sum the histograms in the bkgSamples dictionary.
    """
    region_name, histname = histname.split('.')

    histFile = ROOT.TFile(os.path.join(histdir, f"{bkgSamples[0]}_hist.root"), "READ")
    hist = histFile.Get(region_name).Get(histname).Clone()
    nbinsx = hist.GetNbinsX()
    nbinsy = hist.GetNbinsY()
    xlo = hist.GetXaxis().GetBinLowEdge(1)
    ylo = hist.GetYaxis().GetBinLowEdge(1)
    xup = hist.GetXaxis().GetBinLowEdge(nbinsx + 1)
    yup = hist.GetYaxis().GetBinLowEdge(nbinsy + 1)
    histFile.Close()
    if debug: print(xlo, xup, nbinsy, ylo, yup)
    all_bkg = ROOT.TH2D('allbkg', 'sum of all bkgs', nbinsx, xlo, xup, nbinsy, ylo, yup)

    for sample in bkgSamples:
        histFile = ROOT.TFile(os.path.join(histdir, f"{sample}_hist.root"))
        hist = histFile.Get(region_name).Get(histname).Clone()
        all_bkg.Add(hist)
    return all_bkg

def get_histogram(sample, histdir, histname, debug):
    """
    Detaches the histogram from file.
    Thus you can return it safely via a function

    WARNING: Memory leaks!
    Deleting the histogram is your responsibility

    Ref: https://root-forum.cern.ch/t/get-histogram-and-close-file/18867
    """
    region_name, histname = histname.split('.')

    histFile = ROOT.TFile(os.path.join(histdir, f"{sample}_hist.root"), "READ")
    hist = histFile.Get(region_name).Get(histname).Clone()
    hist.SetDirectory(0)
    return hist
        

### main ###

def main_cli():
    sig = ["stop_M600_575_ct0p2_2018","stop_M600_580_ct2_2018","stop_M600_585_ct20_2018","stop_M600_588_ct200_2018",
           "stop_M1000_975_ct0p2_2018","stop_M1000_980_ct2_2018","stop_M1000_985_ct20_2018","stop_M1000_988_ct200_2018",
           "stop_M1400_1375_ct0p2_2018","stop_M1400_1380_ct2_2018","stop_M1400_1385_ct20_2018","stop_M1400_1388_ct200_2018",
           "C1N2_M600_575_ct0p2_2018","C1N2_M600_580_ct2_2018","C1N2_M600_585_ct20_2018","C1N2_M600_588_ct200_2018",
           "C1N2_M1000_975_ct0p2_2018","C1N2_M1000_980_ct2_2018","C1N2_M1000_985_ct20_2018","C1N2_M1000_988_ct200_2018",
           "C1N2_M1400_1375_ct0p2_2018","C1N2_M1400_1380_ct2_2018","C1N2_M1400_1385_ct20_2018","C1N2_M1400_1388_ct200_2018"]
    

    bkg = ["wjetstolnuht0100_2018","wjetstolnuht0200_2018","wjetstolnuht0400_2018","wjetstolnuht0600_2018","wjetstolnuht0800_2018","wjetstolnuht1200_2018","wjetstolnuht2500_2018",
           "zjetstonunuht0100_2018","zjetstonunuht0200_2018","zjetstonunuht0400_2018","zjetstonunuht0600_2018","zjetstonunuht0800_2018","zjetstonunuht1200_2018","zjetstonunuht2500_2018",
           "qcdht0050_2018","qcdht0100_2018","qcdht0200_2018","qcdht0300_2018","qcdht0500_2018","qcdht0700_2018","qcdht1000_2018","qcdht1500_2018","qcdht2000_2018"]
    

    workdir     = "/users/alikaan.gueven/AngPlotter/CMSSW_14_1_0_pre4/src/SoftDisplacedVertices/Plotter/testK"
    histdir     = os.path.join(workdir, 'histograms')
    outDir      = os.path.join(workdir, 'VP2_yields')
    histname    = "VP2_evt.MET_pt_vs_VP2MaxLxySig"
    debug       = False


    os.makedirs(outDir, exist_ok=True)

    MET_range    = np.arange(450, 1000+1, 50)
    LxySig_range = np.arange(10, 100+1, 5)

    bkg_df_Apred = pd.DataFrame(np.nan, index=MET_range, columns=LxySig_range)
    bkg_df_A     = pd.DataFrame(np.nan, index=MET_range, columns=LxySig_range)
    bkg_df_B     = pd.DataFrame(np.nan, index=MET_range, columns=LxySig_range)
    bkg_df_C     = pd.DataFrame(np.nan, index=MET_range, columns=LxySig_range)
    bkg_df_D     = pd.DataFrame(np.nan, index=MET_range, columns=LxySig_range)

    sig_dfs_A    = {}
    sig_dfs_B    = {}
    sig_dfs_C    = {}
    sig_dfs_D    = {}
    store_path = os.path.join(outDir, 'yield_store.h5')
    store = pd.HDFStore(store_path, mode='w')

    
    

    for MET_bound in MET_range:
        for LxySig_bound in LxySig_range:
            print(MET_bound, '\t', LxySig_bound)

            if debug:
                print("Running main...")
                print()

            sampleDict = {
                "bkg" : bkg,
                "sig" : sig
            }


            
            sample =  sampleDict['sig'][0]
            splits = get_region_boundaries(sample, histdir, histname, MET_bound, LxySig_bound)
            xSplit, ySplit, xSplit_val, ySplit_val = splits
            
            xlo = 0    # Control region lower boundaries as bin ids (MET)
            ylo = 0    # Control region lower boundaries as bin ids (LxySig)

            
            all_bkg = sum_background_hists(sampleDict['bkg'], histdir, histname, debug)
            bkg_count_dict, bkg_squared_error_dict = calculate_yields(all_bkg, xlo, ylo, xSplit, ySplit, unblind=False)
            bkg_df_Apred.at[int(float(MET_bound)), int(float(LxySig_bound))] = bkg_count_dict['A']

            bkg_count_dict, bkg_squared_error_dict = calculate_yields(all_bkg, xlo, ylo, xSplit, ySplit, unblind=True)
            bkg_df_A.at[int(float(MET_bound)), int(float(LxySig_bound))] = bkg_count_dict['A']
            bkg_df_B.at[int(float(MET_bound)), int(float(LxySig_bound))] = bkg_count_dict['B']
            bkg_df_C.at[int(float(MET_bound)), int(float(LxySig_bound))] = bkg_count_dict['C']
            bkg_df_D.at[int(float(MET_bound)), int(float(LxySig_bound))] = bkg_count_dict['D']
            del all_bkg    # Remember: deleting is your responsibility

            for sample in sampleDict['sig']:
                if sample not in sig_dfs_A.keys():
                    sig_dfs_A[sample] = pd.DataFrame(np.nan, index=MET_range, columns=LxySig_range)
                    sig_dfs_B[sample] = pd.DataFrame(np.nan, index=MET_range, columns=LxySig_range)
                    sig_dfs_C[sample] = pd.DataFrame(np.nan, index=MET_range, columns=LxySig_range)
                    sig_dfs_D[sample] = pd.DataFrame(np.nan, index=MET_range, columns=LxySig_range)
                

                sigHist = get_histogram(sample, histdir, histname, debug)
                sig_count_dict, sig_squared_error_dict = calculate_yields(sigHist, xlo, ylo, xSplit, ySplit)
                sig_dfs_A[sample].at[int(float(MET_bound)), int(float(LxySig_bound))] = sig_count_dict['A']
                sig_dfs_B[sample].at[int(float(MET_bound)), int(float(LxySig_bound))] = sig_count_dict['B']
                sig_dfs_C[sample].at[int(float(MET_bound)), int(float(LxySig_bound))] = sig_count_dict['C']
                sig_dfs_D[sample].at[int(float(MET_bound)), int(float(LxySig_bound))] = sig_count_dict['D']
                del sigHist    # Remember: deleting is your responsibility


    


    
    # Write to store
    # -------------------------------------
    store["all_bkg_Apred"] = bkg_df_Apred
    store["all_bkg_A"]     = bkg_df_A
    store["all_bkg_B"]     = bkg_df_B
    store["all_bkg_C"]     = bkg_df_C
    store["all_bkg_D"]     = bkg_df_D


    for sample in sampleDict['sig']:
        store[f'{sample}_A'] = sig_dfs_A[sample]
        store[f'{sample}_B'] = sig_dfs_B[sample]
        store[f'{sample}_C'] = sig_dfs_C[sample]
        store[f'{sample}_D'] = sig_dfs_D[sample]

    out_figure_dir = os.path.join(outDir, 'figures')
    os.makedirs(out_figure_dir, exist_ok=True)


    # Plot figures
    # -------------------------------------
    for key in store.keys():
        print('Plotting ...')
        df = store[key].transpose()
        fig = plt.figure(figsize=(8,6), dpi=300)
        s = sns.heatmap(df, cbar_kws={'label': 'nEvents'},
                        cmap=sns.cm.rocket_r, annot=True,
                        annot_kws={"fontsize":6},
                        fmt=".2e")
        s.set(xlabel='MET_pt', ylabel='Max(LxySig)', title=f'Predicted Event Yields {key[1:]}')
        # s.set_yticklabels([*map(lambda x: round(float(x.get_text()), 1), s.get_yticklabels())])
        s.invert_yaxis()
        fig.tight_layout()
        fig.savefig(f"{os.path.join(out_figure_dir, key[1:])}.png")
        plt.close()


    if debug:
        print('Process finished...')

if __name__ == "__main__":
    main_cli()