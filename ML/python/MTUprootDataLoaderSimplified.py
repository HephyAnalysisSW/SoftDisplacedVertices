import random

import torch
import numpy as np
import awkward as ak

import uproot

from numba import njit
from numba import jit


@njit
def deepTable(tkBranch, trIdx, svIdx, n_sv, builder):
    """
    svIdx: [[0, 0, 1, 1, 2, 2, 3, 3, ...], ...]
    trIdx: [[1, 3, 3, 28, 7, 8, 10, 11, ...], ...]
    n_sv: [4, 0, 6, 1, 1, 7, ...]
    """
    # at event level depth already
    # every element added are at event level depth
    for ev in range(len(tkBranch)):
        builder.begin_list()                      # adding sv level depth
        for sv in range(n_sv[ev]):                # for each vtx ... 
            builder.begin_list()
            for i2, col in enumerate(svIdx[ev]):  # getting an svIdx from the svIdxs for that event
                if col == sv:                     # if the same svIdx 
                    builder.append(tkBranch[ev][trIdx[ev][i2]])
            builder.end_list()
        builder.end_list()


def pad_and_fill(X, branchDict, svDim=12, tkDim=10, fillValue=-9e10):
    X_dict = {}
    for field in X.fields:
        if branchDict['ev'] is not None and field in branchDict['ev']:
            if field.startswith('n'):
                X[field] = ak.values_astype(X[field], np.int32)
            X_np = X[field].to_numpy()
            X_tensor = torch.tensor(X_np)
            X_dict[field] = X_tensor
        
        elif branchDict['sv'] is not None and field in branchDict['sv']:
            padded = ak.pad_none(X[field], target=svDim, clip=True, axis=1)
            filled = ak.fill_none(padded, fillValue, axis=1)
            
            X_np = filled.to_numpy()
            X_tensor = torch.tensor(X_np)

            #### optional (convert to vtx level like weaver)
            ####
            X_tensor = torch.flatten(X_tensor, start_dim=0, end_dim=1)[:,np.newaxis]
            
            X_dict[field] = X_tensor

        elif branchDict['tk'] is not None and field in branchDict['tk']:
            trIdx = X.SDVIdxLUT_TrackIdx
            svIdx = X.SDVIdxLUT_SecVtxIdx
            n_sv  = X.nSDVSecVtx
            
            builder = ak.ArrayBuilder()
            deepTable(X[field], trIdx, svIdx, n_sv, builder)
            deepX = builder.snapshot()

            if field == 'SDVTrack_E':
                fillValue = 1e3
            elif field == 'SDVTrack_pz':
                fillValue = 0
            
            padded = ak.pad_none(deepX, target=tkDim, clip=True, axis=2)
            filled = ak.fill_none(padded, fillValue, axis=2)
            
            padded = ak.pad_none(filled, target=svDim, clip=True, axis=1)
            filled = ak.fill_none(padded, [fillValue]*tkDim, axis=1)

            
            
            X_np = filled.to_numpy()
            X_tensor = torch.tensor(X_np)

            #### optional (convert to vtx level like weaver)
            ####
            X_tensor = torch.flatten(X_tensor, start_dim=0, end_dim=1)[:,np.newaxis,:]
            
            
            X_dict[field] = X_tensor

        
    return X_dict

def ptetaphim_to_epxpypz(pt, eta, phi, m=0.13957):
    px = pt * np.cos(phi)
    py = pt * np.sin(phi)
    pz = pt * np.sinh(eta)
    E = np.sqrt(px*px + py*py + pz*pz + m*m)
    return (E, px, py, pz)



class ModifiedUprootIterator(torch.utils.data.IterableDataset):
    def __init__(self, files, branches, shuffle=True, nWorkers=1, step_size=1024):
        """
        Parameters
        ----------
        files : list
                list of files with the TTree (e.g. ['path_to_file:Events', ...])
        branches : dict
                dict of branches in TTree.
                keys should be ev,sv,tk.
                values should be of type list.
        nWorkers : int
                Files will be divided among the workers.
                Therefore, nWorkers determines number of divisions.
                nWorkers=0 will be treated as nWorkers=1.
        step_size : int
                number of Events to be read from the files at each iteration.
        """
        
        print('Initialize iterable dataset')
        self.files = files
        self.branches = branches

        self.branchList = []
        for key, value in branches.items():
            if value is not None:
                self.branchList.extend(value)
            
        self.step_size = step_size
        self.nWorkers = nWorkers
        
        if shuffle:
            random.shuffle(self.files)

        if nWorkers == 0: nWorkers=1 # Min nWorkers should be great
        self.workerTrainList = [[self.files[i] for i in range(len(self.files)) if i % nWorkers == worker_info_id] for worker_info_id in range(nWorkers)]
        
        self.iteratorList = [uproot.iterate(workerXInput, self.branchList, step_size=self.step_size) for workerXInput in self.workerTrainList]
        self.x = None
        

    def __iter__(self):
        """
        Refresh all the iterators in the iteratorList.
        Will be run at the end of each epoch.
        """
        self.iteratorList = [uproot.iterate(workerXInput, self.branchList, step_size=self.step_size) for workerXInput in self.workerTrainList]
        return self

    
    def __next__(self):
        """
        next method to get the inputs to the network.

        Note to myself (KAAN): Maybe I can separate some part of the code into the preprocessing step.
                               But remember that DataLoader always return torch tensors or numpy arrays etc.
        """
        worker_info = torch.utils.data.get_worker_info()
        if worker_info:
            self.x = next(self.iteratorList[worker_info.id])
        elif not worker_info and self.nWorkers < 2: # Single threaded
            self.x = next(self.iteratorList[0])
        else:
            self.x = next(self.iteratorList[0])

        # Add 4 vector branches.
        # Currently not present in NanoAOD.
        if all(x in self.branchList for x in ['SDVTrack_pt', 'SDVTrack_eta', 'SDVTrack_phi']) and \
           any(x not in self.branchList for x in ['SDVTrack_E', 'SDVTrack_px', 'SDVTrack_py', 'SDVTrack_pz']):
            
            self.branches['tk'].append('SDVTrack_E')
            self.branches['tk'].append('SDVTrack_px')
            self.branches['tk'].append('SDVTrack_py')
            self.branches['tk'].append('SDVTrack_pz')
            
            E, px, py, pz = ptetaphim_to_epxpypz(self.x['SDVTrack_pt'], self.x['SDVTrack_eta'], self.x['SDVTrack_phi'])
            self.x['SDVTrack_E'] = E
            self.x['SDVTrack_px'] = px
            self.x['SDVTrack_py'] = py
            self.x['SDVTrack_pz'] = py
            
        
        X_out = pad_and_fill(self.x, self.branches, svDim=12, tkDim=10, fillValue=0.)

        return X_out






