# limitcalc_oop

This directory contains the reusable OOP limit workflow.

## Environment Rule

- Run submission scripts outside `cmssw-el9`.
- Run datacard creation and limit calculation inside `cmssw-el9`.
- The submission scripts satisfy this by writing `job_ids.json` and submitting
  jobs through the existing parent wrapper:

```text
../submit_limitcalc.sh
```

That wrapper enters `cmssw-el9`, runs `cmsenv`, and executes the command.

## Main Scripts

Create datacards for one threshold point:

```bash
python3 AN-25-092_make_multiplane_datacards_v3.py --xcut 350 --ycut 0.999
```

Run limits for one datacard:

```bash
python3 AN-25-092_run_limits_v3.py --datacard card.txt --limitdir limits
```

Write datacard job JSON for the full ABCD scan and submit it:

```bash
python3 AN-25-092_submit_datacard_jobs_v3.py --uniquedir AN-25-092_ML_plots_limitcalc_merge_w_Ang_v3
```

Use custom scan ranges with `MIN MAX STEP` syntax:

```bash
python3 AN-25-092_submit_datacard_jobs_v3.py \
  --uniquedir AN-25-092_ML_plots_limitcalc_merge_w_Ang_v3 \
  --x-scan 350 700 50 \
  --y-scan 0.990 1.0 0.0002
```

After the datacard jobs are finished, write limit job JSON and submit it:

```bash
python3 AN-25-092_submit_limit_jobs_v3.py --uniquedir AN-25-092_ML_plots_limitcalc_merge_w_Ang_v3
```

Use the same `--x-scan` and `--y-scan` values you used for datacard jobs if
they were not the defaults.

## Files

- `datacards.py`: datacard classes.
- `limits.py`: one-datacard limit runner.
- `jobs.py`: ABCD scan, command building, and `job_ids.json` handling.
- `systematics_sig.yaml`: local signal systematic uncertainties.

## Design

The code intentionally uses plain classes and common libraries. The useful
classes are:

- `DatacardInputs`: years, planes, file names, histogram names.
- `RunOptions`: thresholds, input directory, output directory, mode, data flag.
- `RegionIntegrator`: ABCD integration from a ROOT histogram.
- `DatacardGenerator`: sample discovery, CombineHarvester setup, writing, and
  datacard text clean-up.
- `LimitRunner`: one `combine -M AsymptoticLimits` run.
- `ABCDScan`: scan point names and output paths.
- `JobIds`: read, write, and submit jobs listed in `job_ids.json`.

The scripts are thin wrappers around these classes. For a future custom scan,
load `ABCDScan`, `CmsswJobCommand`, and `JobIds` from `jobs.py`, then write the
commands you need.
