# Run this through CMSSW_14_1_0_pre4
# Example usage:
# python3 store_limit_tables.py

import ROOT
import os
import pandas as pd
import numpy as np

limit_dir = '/users/alikaan.gueven/AngPlotter/CMSSW_14_1_0_pre4/src/SoftDisplacedVertices/Plotter/testK/limits/MC_SP'
limit_tables_dir = '/users/alikaan.gueven/AngPlotter/CMSSW_14_1_0_pre4/src/SoftDisplacedVertices/Plotter/testK/limit_tables/MC_SP'
os.makedirs(limit_tables_dir, exist_ok=True)
store = pd.HDFStore(os.path.join(limit_tables_dir, 'limit_table_store.h5'))

for root, dirs, files in os.walk(limit_dir):
    if len(files) != 0:
        df = pd.DataFrame(np.nan, index=np.arange(400, 1000+1, 50), columns=np.arange(15, 100+1, 5))
        # print(df)
        print(root)
    for filename in files:
        if filename.endswith('.root'):
            root_file_path = os.path.join(root, filename)
            limit_at_median = np.nan
            # print(filename)
            with ROOT.TFile(root_file_path, 'READ') as f:
                tree = f.Get('limit')
                # quantiles = []
                # limits =    []
                
                for entry in tree:
                    # quantiles.append(tree.GetLeaf('quantileExpected').GetValue())
                    # limits.append(tree.GetLeaf('limit').GetValue())
                    # print(tree.GetLeaf('quantileExpected').GetValue())
                    if abs(tree.GetLeaf('quantileExpected').GetValue() - 0.50) < 1e-3:
                        # print(limit_at_median)
                        limit_at_median = tree.GetLeaf('limit').GetValue()
            
            root_filename = os.path.split(root_file_path)[1]
            root_filename = root_filename[:-5]
            sample_name = '_'.join(root_filename.split('_')[:-2])
            (MET, LxySig) = root_filename.split('_')[-2:]
            # print(MET, LxySig)
            df.at[int(float(MET)), int(float(LxySig))] = limit_at_median
    if len(files) != 0:
        store[sample_name] = df