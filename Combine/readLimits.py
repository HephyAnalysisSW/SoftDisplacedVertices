# CMSSW_14 does not have seaborn
# Run this in another environment

# Example usage:
# python3 readLimits.py

import os
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm

limit_tables_dir = '/users/alikaan.gueven/AngPlotter/CMSSW_14_1_0_pre4/src/SoftDisplacedVertices/Plotter/testK/limit_tables/MC_SP'

out_figure_dir = os.path.join(limit_tables_dir, 'figures')
os.makedirs(out_figure_dir, exist_ok=True)

store = pd.HDFStore(os.path.join(limit_tables_dir, 'limit_table_store.h5'), mode='r')
for key in store.keys():
    df = store[key].transpose()
    fig = plt.figure(figsize=(8,6), dpi=300)
    s = sns.heatmap(df, cbar_kws={'label': 'expected signal strength (r)'},
                    cmap=sns.cm.rocket_r, annot=True,
                    annot_kws={"fontsize":6},
                    fmt=".4g")
    s.set(xlabel='MET_pt', ylabel='Max(LxySig)', title=f'Upper Limits on {key[1:]}')
    # s.set_yticklabels([*map(lambda x: round(float(x.get_text()), 1), s.get_yticklabels())])
    s.invert_yaxis()
    fig.tight_layout()
    fig.savefig(f"{os.path.join(out_figure_dir, key[1:])}.png")
    plt.close()
