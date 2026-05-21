# Run this through CMSSW_14_1_0_pre4
# Example usage:
# python3 store_limit_tables.py

import ROOT
import os
import pandas as pd
import numpy as np

# limit_dir = '/scratch-cbe/users/alikaan.gueven/AN_plots/ParT_hists/plotconfig_Run2_MLscore_first/limits'
# limit_tables_dir = '/scratch-cbe/users/alikaan.gueven/AN_plots/ParT_hists/plotconfig_Run2_MLscore_first/limit_tables/Run2'

limit_dir = '/scratch-cbe/users/alikaan.gueven/AN_plots/ParT_hists/AN-25-092_ML_plots_limitcalc_merge_w_Ang_v3/limits/gmN/'
limit_tables_dir = '/scratch-cbe/users/alikaan.gueven/AN_plots/ParT_hists/AN-25-092_ML_plots_limitcalc_merge_w_Ang_v3/limit_tables/gmN/'


os.makedirs(limit_tables_dir, exist_ok=True)

store = pd.HDFStore(os.path.join(limit_tables_dir, 'limit_table_store.h5'))

quantile_map = {
    0.025: 'Expected 2.5%',
    0.160: 'Expected 16.0%',
    0.500: 'Expected 50.0%',
    0.840: 'Expected 84.0%',
    0.975: 'Expected 97.5%',
}

tol = 1e-3
rows = []

for root, dirs, files in os.walk(limit_dir):
    for filename in files:
        if not filename.endswith('.root'):
            continue

        root_file_path = os.path.join(root, filename)
        parent_dir = os.path.basename(root)

        row = {'sample': parent_dir}
        for col in quantile_map.values():
            row[col] = np.nan

        f = ROOT.TFile(root_file_path, 'READ')
        tree = f.Get('limit')

        for entry in tree:
            q = tree.GetLeaf('quantileExpected').GetValue()
            r = tree.GetLeaf('limit').GetValue()

            for target_q, colname in quantile_map.items():
                if abs(q - target_q) < tol:
                    row[colname] = r
                    break

        f.Close()
        rows.append(row)

df = pd.DataFrame(rows)
df = df.set_index('sample').sort_index()

store['all_limits'] = df
store.close()