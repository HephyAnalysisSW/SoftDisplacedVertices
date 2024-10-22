import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

inputDir = "/scratch-cbe/users/alikaan.gueven/AN_plots/jetmet_histograms"
  
subdirs = ["jet_nom_met_smear_2017",
           "jet_nom_met_smear_2018",

           "jet_jerdown_met_smear_jerdown_2017",
           "jet_jerdown_met_smear_jerdown_2018",

           "jet_jerup_met_smear_jerup_2017",
           "jet_jerup_met_smear_jerup_2018",

           "jet_jesdown_met_smear_jesdown_2017",
           "jet_jesdown_met_smear_jesdown_2018",

           "jet_jesup_met_smear_jesup_2017",
           "jet_jesup_met_smear_jesup_2018",

           "jet_nom_met_smear_uedown_2017",
           "jet_nom_met_smear_uedown_2018",
           
           "jet_nom_met_smear_ueup_2017",
           "jet_nom_met_smear_ueup_2018"]

# Plot systematic uncertainties
print('Plotting systematic uncertainties...')
for subdir in subdirs[1:]:
  print(subdir)
  storeDir = os.path.join(inputDir, subdir)
  plotDir = os.path.join(storeDir, "figures_sysunc")
  store = pd.HDFStore(os.path.join(storeDir, 'SysUnc.h5'), 'r')
  os.makedirs(plotDir, exist_ok=True)
  for sig in store.keys():
    sig = sig[1:]
    fig = plt.figure(figsize=(8,6), dpi=300)
    s = sns.heatmap(store[sig], cmap='vlag', vmin=-0.2, vmax=0.2, annot=True, fmt=".2g")
    plt.suptitle(sig)
    s.set(xlabel='Regions', ylabel='Planes', title=subdir);
    s.invert_yaxis()
    saveName = os.path.join(plotDir, sig + '.png' )
    print('Saving ', saveName)
    fig.savefig(saveName)
    plt.close()

# Plot yields
print()
print('Plotting yields...')
for subdir in subdirs:
  print(subdir)
  storeDir = os.path.join(inputDir, subdir)
  plotDir = os.path.join(storeDir, "figures_yield")
  store = pd.HDFStore(os.path.join(storeDir, 'Yields.h5'), 'r')
  os.makedirs(plotDir, exist_ok=True)
  for sig in store.keys():
    sig = sig[1:]

    # Yield and its uncertainty
    fig = plt.figure(figsize=(8,6), dpi=300)
    s = sns.heatmap(store[sig], cmap='Blues', annot=True, fmt=".2g")
    plt.suptitle(sig)
    s.set(xlabel='Regions', ylabel='Planes', title=subdir);
    s.invert_yaxis()
    saveName = os.path.join(plotDir, sig + '.png' )
    print('Saving ', saveName)
    fig.savefig(saveName)
    plt.close()