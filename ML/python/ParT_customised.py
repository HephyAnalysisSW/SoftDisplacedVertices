import time
import glob
import random

import torch
import torch.nn as nn
import neptune
from neptune.utils import stringify_unsupported

import numpy as np
import awkward as ak
import matplotlib.pyplot as plt

import uproot

import ParT
import MTUprootDataLoaderSimplified as MTUprootDataLoader

print('CPU count: ', torch.multiprocessing.cpu_count())
# torch.set_num_threads(40)


run = neptune.init_run(
    project="alikaan.guven/ParT",
    api_token="eyJhcGlfYWRkcmVzcyI6Imh0dHBzOi8vYXBwLm5lcHR1bmUuYWkiLCJhcGlfdXJsIjoiaHR0cHM6Ly9hcHAubmVwdHVuZS5haSIsImFwaV9rZXkiOiJhNDNjMWJhNS0wMDExLTQ2NzYtOWVjNS1lNzAzOWU4Mzc0MGMifQ==",
)  # your credentials

param = {
    "input_dim": 5,
    "input_svdim": 5,
    "num_classes": 2,
    "pair_input_dim": 4,
    "embed_dims": [128, 512, 128],
    "for_inference": True,
    "lr": 1e-4

}

run["parameters"] = stringify_unsupported(param)




device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')


# model = ParT.ParticleTransformerTagger(pf_input_dim=5,
#                                        sv_input_dim=5,
#                                        num_classes=2,
#                                        pair_input_dim=4,
#                                        # embed_dims=[32, 128, 32],
#                                        for_inference=True).to(device, dtype=float)

model = ParT.ParticleTransformerDVTagger(input_dim=param['input_dim'],
                                         input_svdim=param['input_svdim'],
                                         num_classes=param['num_classes'],
                                         pair_input_dim=param['pair_input_dim'],
                                         embed_dims=param['embed_dims'],
                                         for_inference=param['for_inference']).to(device, dtype=float)

                                                              
optimizer = torch.optim.Adam(model.parameters(), lr=param['lr'])
criterion = nn.CrossEntropyLoss()


num_parameters = sum(parameter.numel() for parameter in model.parameters())
run['num_parameters'] = num_parameters

print(model)
print('num parameters: ', num_parameters)



ModifiedUprootIterator = MTUprootDataLoader.ModifiedUprootIterator

debug = False

if debug:
    shuffle = False
    nWorkers = 1
    step_size = 100
else:
    shuffle = True
    nWorkers = 8
    step_size = 256



MLDATADIR = '/scratch-cbe/users/alikaan.gueven/ML_KAAN'
tmpList = glob.glob(f'{MLDATADIR}/predict/stop_M1000_*/**/*.root', recursive=True)
random.shuffle(tmpList)
tmpList = [file + ':Events' for file in tmpList]
maxTrain = round(len(tmpList)*0.70)
maxVal = round(len(tmpList)*0.80)
# print(maxTrain)
trainList = tmpList[:maxTrain]
valList = tmpList[maxTrain:maxVal]
testList = tmpList[maxVal:]

branchDict = {}
branchDict['ev'] = ['nSDVSecVtx']
branchDict['sv'] = ['SDVSecVtx_Lxy', 'SDVSecVtx_LxySig', 'SDVSecVtx_pAngle', 'SDVSecVtx_charge', 'SDVSecVtx_ndof', 'SDVSecVtx_matchedLLPnDau_bydau',
                    'SDVIdxLUT_SecVtxIdx', 'SDVIdxLUT_TrackIdx']
branchDict['tk'] = ['SDVTrack_pt', 'SDVTrack_dxy', 'SDVTrack_dxyError', 'SDVTrack_dz', 'SDVTrack_dzError',
                    'SDVTrack_normalizedChi2', 'SDVTrack_eta', 'SDVTrack_phi']


trainDataset = ModifiedUprootIterator(trainList, branchDict, shuffle=shuffle, nWorkers=nWorkers, step_size=step_size)
valDataset = ModifiedUprootIterator(valList, branchDict, shuffle=shuffle, nWorkers=nWorkers, step_size=step_size)
testDataset = ModifiedUprootIterator(testList, branchDict, shuffle=shuffle, nWorkers=nWorkers, step_size=step_size)


trainLoader = torch.utils.data.DataLoader(trainDataset, num_workers=min((nWorkers, len(trainList))), prefetch_factor=1, persistent_workers= True)
valLoader = torch.utils.data.DataLoader(valDataset, num_workers=min((nWorkers, len(valList))), prefetch_factor=1, persistent_workers= True)
testLoader = torch.utils.data.DataLoader(testDataset, num_workers=min((nWorkers, len(testList))), prefetch_factor=1, persistent_workers= True)



epochs = 100

model.train()
for epoch in range(epochs):
    start_time = time.time()
    losses = []
    TP_batch = []
    all_batch = []
    
    for batch_num, input_data in enumerate(trainLoader):
        optimizer.zero_grad()
        X = input_data

        tk_pair_features = torch.cat((X['SDVTrack_px'][0],
                                      X['SDVTrack_py'][0],
                                      X['SDVTrack_pz'][0],
                                      X['SDVTrack_E'][0],), dim=1)

        tk_features = torch.cat((X['SDVTrack_dxy'][0],
                                 X['SDVTrack_dxyError'][0],
                                 X['SDVTrack_dz'][0],
                                 X['SDVTrack_dzError'][0],
                                 X['SDVTrack_normalizedChi2'][0]), dim=1)
        
        sv_features = torch.cat((X['SDVSecVtx_Lxy'][0],
                                 X['SDVSecVtx_LxySig'][0],
                                 X['SDVSecVtx_pAngle'][0],
                                 X['SDVSecVtx_charge'][0],
                                 X['SDVSecVtx_ndof'][0]), dim=1)[..., np.newaxis]



        label = X['SDVSecVtx_matchedLLPnDau_bydau'][0]
        y = label
        
        tk_pair_features = tk_pair_features.to(device, dtype=float)
        tk_features = tk_features.to(device, dtype=float)
        sv_features = sv_features.to(device, dtype=float)
        
        y = y.to(device, dtype=float)

        ymaxSig = torch.max(y > 1, axis=-1).values
        ymaxSig = ymaxSig.float()
        yBkg = (ymaxSig != 1).float()
        y = torch.concatenate((yBkg[:, np.newaxis], ymaxSig[:, np.newaxis]), axis=-1)
        
        output = model(x=tk_features,
                       v=tk_pair_features,
                       x_sv=sv_features)
        loss = criterion(output, y)
        loss.backward()
        losses.append(loss.item())

        optimizer.step()
        
        output_mask = sv_features[:,0,0] == 0 # [batch_dim, Lxy, 1-dim]
        acc = (torch.sum((output[~output_mask]>0.5) == y[~output_mask].data)) / (2*len(y[~output_mask])) # 2 is the number of classes
        run["train/accuracy_batch"].append(acc)
        run["train/loss_batch"].append(loss.item())

        TP_batch.append((torch.sum(~output_mask) * acc).item())
        all_batch.append(torch.sum(~output_mask).item())

    
    run["train/accuracy_epoch"].append(sum(TP_batch) / sum(all_batch))
    run["train/losses_epoch"].append(sum(losses)/len(losses))


    ###### Inference on TEST ######
    with torch.no_grad():
        losses = []
        TP_batch = []
        all_batch = []
        for batch_num, input_data in enumerate(valLoader):
            X = input_data

            tk_pair_features = torch.cat((X['SDVTrack_px'][0],
                                          X['SDVTrack_py'][0],
                                          X['SDVTrack_pz'][0],
                                          X['SDVTrack_E'][0],), dim=1)
    
            tk_features = torch.cat((X['SDVTrack_dxy'][0],
                                     X['SDVTrack_dxyError'][0],
                                     X['SDVTrack_dz'][0],
                                     X['SDVTrack_dzError'][0],
                                     X['SDVTrack_normalizedChi2'][0]), dim=1)
            
            sv_features = torch.cat((X['SDVSecVtx_Lxy'][0],
                                     X['SDVSecVtx_LxySig'][0],
                                     X['SDVSecVtx_pAngle'][0],
                                     X['SDVSecVtx_charge'][0],
                                     X['SDVSecVtx_ndof'][0]), dim=1)[..., np.newaxis]
    
    
    
            label = X['SDVSecVtx_matchedLLPnDau_bydau'][0]
            y = label
    
            tk_pair_features = tk_pair_features.to(device, dtype=float)
            tk_features = tk_features.to(device, dtype=float)
            sv_features = sv_features.to(device, dtype=float)
            
            y = y.to(device, dtype=float)
    
            ymaxSig = torch.max(y > 1, axis=-1).values
            ymaxSig = ymaxSig.float()
            yBkg = (ymaxSig != 1).float()
            y = torch.concatenate((yBkg[:, np.newaxis], ymaxSig[:, np.newaxis]), axis=-1)
            
            output = model(x=tk_features,
                           v=tk_pair_features,
                           x_sv=sv_features)
            loss = criterion(output, y)
            losses.append(loss.item())
            
            output_mask = sv_features[:,0,0] == 0 # [batch_dim, Lxy, 1-dim]
            acc = (torch.sum((output[~output_mask]>0.5) == y[~output_mask].data)) / (2*len(y[~output_mask])) # 2 is the number of classes
            run["val/accuracy_batch"].append(acc)
            run["val/loss_batch"].append(loss.item())
    
            TP_batch.append((torch.sum(~output_mask) * acc).item())
            all_batch.append(torch.sum(~output_mask).item())

        run["val/accuracy_epoch"].append(sum(TP_batch) / sum(all_batch))
        run["val/losses_epoch"].append(sum(losses)/len(losses))

run.stop()



