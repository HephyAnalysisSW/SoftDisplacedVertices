from copy import deepcopy
from pathlib import Path
import pandas as pd
import numpy as np
import re

import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
from matplotlib.lines import Line2D
from scipy.interpolate import LinearNDInterpolator

TICK_LABEL_SIZE = 16
AXIS_LABEL_SIZE = 18

# Just parses the sample name.

def parse_M(name: str) -> int:
    m = re.search(r"_M(\d+)", name)
    if not m:
        raise ValueError(f"Could not parse M from: {name}")
    return int(m.group(1))

def parse_M2(name: str) -> int:
    m = re.search(r"_(\d+)_ct", name)
    if not m:
        raise ValueError(f"Could not parse M from: {name}")
    return int(m.group(1))

def parse_ct(name: str) -> float:
    m = re.search(r"ct([0-9]+(?:p[0-9]+)?)", name)
    if not m:
        return np.nan
    return float(m.group(1).replace("p", "."))

def model_group(name: str) -> str:
    if name.startswith("C1N2"):
        return "C1N2"
    if name.startswith("stop"):
        return "stop"
    return "other"



uniquedir = 'AN-25-092_ML_plots_limitcalc_merge_w_Ang_v3'



limit_tables_dir = Path(f'/scratch-cbe/users/alikaan.gueven/AN_plots/ParT_hists/{uniquedir}/limit_tables/gmN')
pdf_dir = limit_tables_dir / 'pdf'
pdf_dir.mkdir(parents=True, exist_ok=True)

with pd.HDFStore(limit_tables_dir / 'limit_table_store.h5', 'r') as store:
    df = deepcopy(store['all_limits'])
df['M']     = df.index.map(parse_M)
df['dM']    = df['M'] - df.index.map(parse_M2)
df['ct']    = df.index.map(parse_ct)
df['model'] = df.index.map(model_group)

obs_EXO_24_033_C1N2 = {
    'ct': (0.2, 2, 20, 200),
    'xs': (274.09, 61.364, 49.281, 133.81)
    }

obs_EXO_24_033_stop = {
    'ct': (0.2, 2, 20, 200),
    'xs': (8.499, 3.9022, 5.4943, 27.865)
    }



C1N2ML_M500_xs  =  46
stopML_M1000_xs =  7.395


cols = ["Expected 16.0%", "Expected 50.0%", "Expected 84.0%"]
linestyles = ["--", "-", "--"]
labels = [r"median exp. $-1 \sigma$", r"median exp.", r"median exp. $+1 \sigma$"]

for model in ["C1N2", "stop"]:
    if model =="C1N2":
        xs = C1N2ML_M500_xs
        M = 500
        sub = df[(df["M"] == M) & (df["model"] == model) & (df["dM"] == 15)].sort_values("ct")
    elif model =="stop":
        xs = stopML_M1000_xs
        M = 1000
        sub = df[
            ((df["M"] == M) & (df["model"] == model) & (df["dM"] == 25) & (df["ct"] == 0.2)) | 
            ((df["M"] == M) & (df["model"] == model) & (df["dM"] == 20) & (df["ct"] == 2))   | 
            ((df["M"] == M) & (df["model"] == model) & (df["dM"] == 15) & (df["ct"] == 20))  | 
            ((df["M"] == M) & (df["model"] == model) & (df["dM"] == 12) & (df["ct"] == 200))
            ].sort_values("ct")
    # print(sub)
    

    plt.figure()
    for i, c in enumerate(cols):
        lw=1 if i in [0,2] else 2
        plt.plot(sub["ct"], sub[c]*xs, label=labels[i], color='blue', linestyle=linestyles[i], lw=lw)

    if model == "C1N2":
        plt.plot(obs_EXO_24_033_C1N2['ct'], obs_EXO_24_033_C1N2['xs'], color="black", lw=1, linestyle="-", label='EXO-24-033 obs.')
    elif model == "stop":
        plt.plot(obs_EXO_24_033_stop['ct'], obs_EXO_24_033_stop['xs'], color="black", lw=1, linestyle="-", label='EXO-24-033 obs.')
    
    plt.xscale("log")
    plt.yscale("log")
    plt.xlabel("ct [mm]", fontsize=14)
    plt.ylabel(r"95% CL upper limit on cross-section $\sigma$ [fb]", fontsize=14)
    plt.title(f'{model} M={M} GeV')
    plt.grid(True, which="both", linestyle=":")
    plt.tick_params(axis="both", which="both", labelsize=14)
    plt.legend()
    plt.tight_layout()

    pdf_path = pdf_dir / f'{model}_M{M}_limit.pdf'
    plt.savefig(pdf_path)
    plt.close()
    print(f'Wrote {pdf_path}')





# Ref: https://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.LinearNDInterpolator.html#scipy.interpolate.LinearNDInterpolator

for dM in [5,10,15,25]:

    # dM = 10
    model = 'C1N2'

    mask = (df['dM'] == dM) & (df['model'] == model)

    x = df.loc[mask, 'M']
    y = df.loc[mask, 'ct']
    z = df.loc[mask, 'Expected 50.0%']

    X = np.linspace(x.min(), x.max(), 100)
    Y = np.logspace(np.log10(y.min()), np.log10(y.max()), 100)
    X, Y = np.meshgrid(X, Y)

    interp = LinearNDInterpolator(list(zip(x, y)), z)
    Z = interp(X, Y)

    Z = np.ma.masked_invalid(Z)
    Z = np.ma.masked_less_equal(Z, 0)

    z16 = df.loc[mask, 'Expected 16.0%']
    z84 = df.loc[mask, 'Expected 84.0%']

    Z16 = LinearNDInterpolator(list(zip(x, y)), z16)(X, Y)
    Z84 = LinearNDInterpolator(list(zip(x, y)), z84)(X, Y)

    Z16 = np.ma.masked_invalid(Z16)
    Z16 = np.ma.masked_less_equal(Z16, 0)

    Z84 = np.ma.masked_invalid(Z84)
    Z84 = np.ma.masked_less_equal(Z84, 0)

    plt.figure(figsize=(10, 7.5))
    pcm = plt.pcolormesh(X, Y, Z, shading='auto', norm=LogNorm())

    c50 = plt.contour(X, Y, Z, levels=[1], colors='w', linewidths=2)
    c16 = plt.contour(X, Y, Z16, levels=[1], colors='w', linewidths=2, linestyles='--')
    c84 = plt.contour(X, Y, Z84, levels=[1], colors='w', linewidths=2, linestyles='--')

    pts = plt.plot(x, y, '*k', markersize=10)[0]

    plt.yscale('log')
    cbar = plt.colorbar(pcm)
    cbar.set_label(r'Signal strength $r$', fontsize=18)
    cbar.ax.tick_params(labelsize=TICK_LABEL_SIZE)
    plt.xlim(150, 550)
    plt.ylim(1.5, 4e2)
    plt.xlabel('M', fontsize=AXIS_LABEL_SIZE)
    plt.ylabel(r'c$\tau$', fontsize=AXIS_LABEL_SIZE)
    plt.tick_params(axis="both", which="both", labelsize=TICK_LABEL_SIZE)
    plt.annotate(f'{model}\n$\\Delta M = {dM}$ GeV', (0.80, 0.90), xycoords='axes fraction', fontsize=14)



    plt.legend(handles=[
        Line2D([0], [0], color='k', lw=2, label='Expected mean'),
        Line2D([0], [0], color='k', lw=2, ls='--', label='68% CL'),
        Line2D([0], [0], color='k', marker='*', lw=0, markersize=10, label='Input points'),
    ], loc='upper left'
    )

    plt.tight_layout()
    pdf_path = pdf_dir / f'{model}_dM{dM}_limit_map.pdf'
    plt.savefig(pdf_path)
    plt.close()
    print(f'Wrote {pdf_path}')
