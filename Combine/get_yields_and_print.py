import pandas as pd
import numpy as np
import os

store_path = '/users/alikaan.gueven/AngPlotter/CMSSW_14_1_0_pre4/src/SoftDisplacedVertices/Plotter/testK/SP_yields/yield_store.h5'

store = pd.HDFStore(store_path, 'r')

MET_cut    = 700
LxySig_cut =  20



store_samples = []
for key in store.keys():
    # print(key)
    store_samples.append('_'.join(key.split('_')[:-1])[1:])

store_samples = list(set(store_samples))
store_samples.sort()
df = pd.DataFrame(np.nan, index=store_samples, columns=['Apred', *'ABCD'])
for sample in store_samples:
    # if sample[:3] == 'all': continue
    for region in ['Apred', *'ABCD']:
        try:
            df.at[sample, region] = store[f'{sample}_{region}'].at[MET_cut, LxySig_cut]
        except KeyError:
            pass


df = df.fillna('')
# print(df.to_latex())
print(df)