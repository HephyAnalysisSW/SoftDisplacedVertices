"""

"LIMITDIR" variable contains a directory where the limit files (.pkl) are stored.

"""


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pickle
import re
import glob
import os



# Just parses the sample name.

def parse_M(name: str) -> int:
    m = re.search(r"_M(\d+)", name)
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

# --------------------------------------------------------------------

# Observed cross-sections obtained from HepData

obs_EXO_24_033_C1N2 = {
    'ct': (0.2, 2, 20, 200),
    'xs': (274.09, 61.364, 49.281, 133.81)
    }

obs_EXO_24_033_stop = {
    'ct': (0.2, 2, 20, 200),
    'xs': (8.499, 3.9022, 5.4943, 27.865)
    }

# --------------------------------------------------------------------

# Load the limit calculation results into a pandas dataframe.
USERNAME = os.getlogin()
LIMITDIR = '/scratch-cbe/users/alikaan.gueven/AN_plots/ParT_hists/vtx_PART_1111best_valloss_epoch_multiplane_dphi_test6/limitdir'


PLOTDIR  = os.path.join('/scratch-cbe/users/',
                        USERNAME,
                        'AN_plots/ParT_hists/vtx_PART_1111best_valloss_epoch_multiplane_dphi_test6/limitplotdir')

os.makedirs(PLOTDIR, exist_ok=True)

pickles = glob.glob(LIMITDIR + '/**/limits_summary.pkl', recursive=True)

dfs = []

for i, limit_pickle in enumerate(pickles):
    with open(limit_pickle, 'rb') as pkl_file:
        TABLE = pickle.load(pkl_file)
    dfs.append(TABLE)

TABLE = pd.concat(dfs)

# --------------------------------------------------------------------

# Plotting...

df = TABLE.copy()

xsec_map = {("C1N2", 500): 46.0,
            ("stop", 1000): 7.395}

df["M"] = [parse_M(s) for s in df.index]
df["ct"] = [parse_ct(s) for s in df.index]
df["model"] = [model_group(s) for s in df.index]
df["xs"] = [xsec_map.get((m, M), np.nan) for m, M in zip(df["model"], df["M"])]
df = df[df["model"].isin(["C1N2", "stop"])].dropna(subset=["ct"])

cols = ["m1", "median", "p1"]
linestyles = ["--", "-", "--"]
labels = [r"median exp. $-1 \sigma$", r"median exp.", r"median exp. $+1 \sigma$"]

for model in ["C1N2", "stop"]:
    sub = df[df["model"] == model].sort_values("ct")

    plt.figure()
    for i, c in enumerate(cols):
        lw=1 if i in [0,2] else 2
        plt.plot(sub["ct"], sub[c]*sub['xs'], label=labels[i], color='blue', linestyle=linestyles[i], lw=lw)

    if model == "C1N2":
        plt.plot(obs_EXO_24_033_C1N2['ct'], obs_EXO_24_033_C1N2['xs'], color="black", lw=1, linestyle="-", label='EXO-24-033 obs.')
    elif model == "stop":
        plt.plot(obs_EXO_24_033_stop['ct'], obs_EXO_24_033_stop['xs'], color="black", lw=1, linestyle="-", label='EXO-24-033 obs.')
    
    plt.xscale("log")
    plt.yscale("log")
    plt.xlabel("ct [mm]")
    plt.ylabel(r"95% CL upper limit on cross-section $\sigma$ [fb]")
    plt.title(f'IVF (all vertices) {model} prediction')
    plt.grid(True, which="both", linestyle=":")
    plt.legend()
    plt.tight_layout()


    PLOTNAME = os.path.join(PLOTDIR, f'{model}_limits')
    plt.savefig(PLOTNAME + '.png')
    plt.savefig(PLOTNAME + '.pdf')