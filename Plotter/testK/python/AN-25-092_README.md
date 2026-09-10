## Plots

### Prepare plots

Cleans up the directory, and fills with plotter commands.
```
cd SoftDisplacedVertices/Plotter/testK
cmssw-el9
cmsenv
python3 python/AN-25-092_prepare_jobs.py
```

### Submit plots

```
 python3 python/AN-25-092_submit_jobs.py --uniquedir AN-25-092_ML_plots_loMET
```

### Resubmit plots

Same as the initial submission.







### Reweighted datacards

```
limitcalc_oop_v2/AN-25-092_make_reweighted_pkl_datacards_v2.py
```

### Limit calculation
```
limitcalc_oop_v2/AN-25-092_submit_limit_jobs_v2.py
```


### Limit plotting

```
limitcalc_oop_v2/AN-25-092_plot_limits_v2.py
```

