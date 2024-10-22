# Plotter

A plotter is developed to make plots in a flexible way. 

## Script description:

- autoplotter.py
This script generates root files that include histograms. Histograms will be organized in different directories based on search region definition and object selections.
Parameters:
`--sample`: input samples to make histograms. It has to be defined in the [Samples module](https://github.com/HephyAnalysisSW/SoftDisplacedVertices/blob/new_CMSSW/Samples/python/Samples.py) and can be a single sample (such as `wjetstolnuht0600_2018`) or a list of samples (`wlnu_2018`). For a list of samples, the script will generate one root file for each sample.

`--output`: directory of output.

`--config`: configure file that defines event selections and what variables to plot. [Example config](https://github.com/HephyAnalysisSW/SoftDisplacedVertices/blob/new_CMSSW/Plotter/configs/plotconfig_diffregions.yaml) is provided. When new variables are added, please add a new entry in the [plot\_setting module](https://github.com/HephyAnalysisSW/SoftDisplacedVertices/blob/new_CMSSW/Plotter/python/plot_setting.py) to set the plot binning and title.

`--lumi`: luminosity to normalise the MC, unit in `pb-1`.

`--json`: Name of the json file that records the file path of the samples. The default path is under `SoftDisplacedVertices/Samples/json`.

`--metadata`: This is deprecated. Name of the yaml file that records the GenSumWeight of MC samples. The default path is under `SoftDisplacedVertices/Samples/json`.

`--datalabel`: Lable of the dataset used for making histogram. It should be consistent with what is available in the json file.

`--data`: Optional. Specifies whether the input is data.

`--year`: The data-taking year of the input data or MC.

`--submit`: Optional. Whether to submit jobs to slurm. Only works in CLIP.

## Prerequisites:

- The NanoAOD files are recorded in a json file, like the ones under `SoftDisplacedVertices/Samples/json`.
- The json file should also include the total number of events generated without filters. This information was provided by the metadata yaml file before. It can be obtained by running [getMCInfo.py](https://github.com/HephyAnalysisSW/SoftDisplacedVertices/blob/new_CMSSW/Plotter/getMCInfo.py).
- (Outdated) If Filters are applied before or during the generation of MiniAOD, a metadata yaml file should be available to provide the information of total events generated without filters. This ensures the normalisation for MC is done correctly.

## Environmental setup:

For the first time to run the code, set up CMSSW 13 or above:

```
cmsrel CMSSW_13_0_0
cd CMSSW_13_3_0/src
git clone git@github.com:HephyAnalysisSW/SoftDisplacedVertices.git
git checkout new_CMSSW
scram b -j 8
cmsenv
```

The above setup has to be done only once. If already set up, just do:
```
cd CMSSW_13_3_0/src
cmsenv
```

## Steps:

First, generate the metadata yaml files if not already available. Note that one need to modify the python script to specify the `input_samples`.
```
python3 getMCInfo.py --sample_version CustomMiniAOD_v3 --json CustomMiniAOD_v3 --outDir ../Samples/json/
```

Then generate the histograms:

To run interactively:
For MC:
```
python3 autoplotter.py --sample stop_M600_580_ct2_2018 --output ./ --config configs/plotconfig.yaml --lumi 59683. --json MC_RunIISummer20UL18.json --datalabel CustomNanoAOD --year 2018
```
For data:
```
python3 autoplotter.py --sample met_2018 --output ./ --config configs/plotconfig.yaml --lumi -1 --json Data_production_20240326.json --datalabel CustomNanoAOD --data --year 2018
```

To submit jobs, simply add the `--submit` to the commands above.

When jobs finish, one can use the haddplots.py to `hadd` the output files together for each process.
```
python3 haddplots.py --dir /path/to/job
```

To compare histograms, do:
```
python3 compare.py --input /users/ang.li/public/SoftDV/CMSSW_13_3_0/src/SoftDisplacedVertices/Plotter/plots_ML_METSlice/bkg_2018_MLNanoAODv0_hist.root /users/ang.li/public/SoftDV/CMSSW_13_3_0/src/SoftDisplacedVertices/Plotter/plots_ML_METSlice/stop_M600_588_ct200_2018_MLNanoAODv0_hist.root --dirs '' --nice 'signal' 'bkg' --scale
```

To [make CMS style comparison plots](https://cms-analysis.docs.cern.ch/guidelines/plotting/#__tabbed_1_2), new package is required:

Do this once in CMSSW:
```
cd CMSSW_13_3_0/src
scram-venv
pip3 install cmsstyle
```

Once the enviroment is set up, multiple different kind of plots can be made:
- Stacked background MC with data and signal (if data or signal is not specified, it will only plot whatever is available):
```
python3 compare_data_new.py --data data_hist.root --bkg wjets_2018_hist.root zjets_2018_hist.root --bkgnice "WJets" "ZJets" --signal stop_M600_585_ct20_2018_hist.root --signice "signal" --output dir_output/ --dirs "All_SDVTrack_all" --commands "h.Rebin(5) if ('LxySig' in h.GetName()) else None" --ratio 
```
- Stacked background MC with signal, all histograms normalised to 1:
```
python3 compare_data_new.py  --bkg qcd_2018_hist.root wjets_2018_hist.root zjets_2018_hist.root  --bkgnice "QCD" "WJets" "ZJets" --signal stop_M600_585_ct20_2018_hist.root --signice "signal" --output ./ --dirs "All_SDVTrack_all" --commands "h.Rebin(5) if ('LxySig' in h.GetName()) else h.GetXaxis().SetRangeUser(0,20) if ('pfRel' in  h.GetName()) else None" --norm
```

# Closure test / Event yield check

Scripts are provided to print out the number of events in different serach regions:
- To print events when search regions are defined individually in different directories in the root file: 
```
python3 printNevt.py --input /eos/vbc/group/cms/ang.li/MCHistos_VRCRdatacard_1/ --SR SR_evt SR_CRlowMET_evt SR_CRlowLxy_evt SR_CRlowLxylowMET_evt VR1_evt VR1_CRlowMET_evt VR1_CRlowLxy_evt VR1_CRlowLxylowMET_evt VR2_evt VR2_CRlowMET_evt VR2_CRlowLxy_evt VR2_CRlowLxylowMET_evt --metcut 0
```
- To print events when there are 2D histograms in the root file directories. Will integral the 2D histogram depending on cut values. Currently, the script takes the 2D histogram of MET vs. Lxy significance, and integral the histogram using different MET and Lxy significance cut to get the number of events in different regions.
```
python3 printNevt2D.py --input /eos/vbc/group/cms/ang.li/DataHistos_VRCRVRdPhirevert_12/ --SR VR1s_evt/MET_pt_corr_vs_SDVSecVtx_LxySig_max_val1 VR2s_evt/MET_pt_corr_vs_SDVSecVtx_LxySig_max_val2 --metcut 0
```

Two different sets of scripts are provided, `printNevt` and `getNevt`, basically they do the same thing. But the printouts are formatted differently.


# JETMET Uncertainty Calculation

```
python3 Plotter/testK/submit_jetmet_hists.py
```

```
python3 print_jetmet_2017.py --input /scratch-cbe/users/alikaan.gueven/AN_plots/jetmet_histograms --SR SRs_evt/MET_pt_corr_vs_SRsMaxLxySig VR1s_evt/MET_pt_corr_vs_VR1sMaxLxySig VR2s_evt/MET_pt_corr_vs_VR2sMaxLxySig --metcut 0
python3 print_jetmet_2018.py --input /scratch-cbe/users/alikaan.gueven/AN_plots/jetmet_histograms --SR SRs_evt/MET_pt_corr_vs_SRsMaxLxySig VR1s_evt/MET_pt_corr_vs_VR1sMaxLxySig VR2s_evt/MET_pt_corr_vs_VR2sMaxLxySig --metcut 0
```

```
python3 plot_jetmet.py 
```

```
python3 fit_sysUnc_2017.py
python3 fit_sysUnc_2018.py
```
