================ ATTENTION ====================
Check every script before you run them.
They are highly suboptimal at the moment!!!
================ ========= ====================


Installation Steps
------------------
```
cmsrel CMSSW_14_1_0_pre4
cd CMSSW_14_1_0_pre4/src
cmsenv
git clone https://github.com/cms-analysis/HiggsAnalysis-CombinedLimit.git HiggsAnalysis/CombinedLimit
git clone git@github.com:HephyAnalysisSW/SoftDisplacedVertices.git
cd SoftDisplacedVertices
git checkout Combine_v10.0.2
cd ..
scram b -j16
```


How to Start Running
--------------------

To create datacards:
```
cd SoftDisplacedVertices/Combine
python3 datacardWriter.py all_sig_2018 all_bkg_2018 test/histograms/ SP_evt.MET_pt_vs_SPMaxLxySig test/datacards/
```

To mass produce limits for MET_vs_LxySig scan:
```
python submit_limit_calculations.py
```
But this does not work within Singularity container.
So step out of this container and submit in an environment where you have python3 installed.
If there are no errors at this stage your Combine/test/limits directory should not contain random directory names.

You can as well submit single datacard within Singularity container:
```
python3 makeLimits.py --datacard {datacard} --limitdir {limitdir}
```

You can store these limits as Pandas DataFrames like this:
```
python3 store_limit_tables.py
```

If you have a different environment where you have seaborn installed you can produce beautiful annotated heatmaps.
```
python3 readLimits.py
```

Similarly you can calculate the yields for every scanned cut and for every ABCD region.
You will need an environemnt where ROOT, python3, pandas, and seaborn installed all together.
```
python3 get_yields_and_store.py
```

If you want to create LaTeX table by using these yields:
```
python3 get_yields_and_print.py
```