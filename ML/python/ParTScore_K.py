from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
import ROOT
ROOT.PyConfig.IgnoreCommandLineOptions = True

import onnxruntime as ort
import numpy as np
import json
import vector
vector.register_awkward()
import os 

class ParTScoreProducer(Module):
    def __init__(self,model_path='',preprocess_json_path=''):
        self.model_path = model_path
        self.preprocess_json_path = preprocess_json_path
        pass

    def deltaPhi(self,dphi):
        #if np.isscalar(dphi):
        o2pi = 1. / (2. * np.pi)
        mask = np.abs(dphi) > np.pi
        n = np.round(dphi*o2pi)
        return dphi - n * mask * (2. * np.pi)

    def deltaR(self,deta,dphi):
        dphi = self.deltaPhi(dphi)
        return np.hypot(dphi,deta)

    def ArraytoNumpy(self,array):
        arr_np = []
        for i in array:
          arr_np.append(i)
        arr_np = np.array(arr_np,dtype=np.float64)
        return arr_np

    def beginJob(self):
        self.ort_sess = ort.InferenceSession(self.model_path, providers=['CPUExecutionProvider'])
        self.params = None
        self.excludeinput = ['pf_points']
        with open(self.preprocess_json_path,'r') as fj:
          self.params = json.load(fj)

    def endJob(self):
        pass

    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.out = wrappedOutputTree
        self.out.branch("SDVSecVtx_ParTScore", "F", lenVar="nSDVSecVtx")

    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        pass

    def analyze(self, event):
        """process event, return True (go to next module) or False (fail, go to next event)"""

        SDVSecVtx = Collection(event, "SDVSecVtx")
        SDVTrack = Collection(event, "SDVTrack")
        SDVIdxLUT = Collection(event, "SDVIdxLUT")

        Jet = Collection(event, "Jet")

        Jet_eta = self.ArraytoNumpy(event.Jet_eta)
        Jet_phi = self.ArraytoNumpy(event.Jet_phi)

        Jet_jetId = self.ArraytoNumpy(event.Jet_jetId)
        Jet_pt = self.ArraytoNumpy(event.Jet_pt)
        Jet_chEmEF = self.ArraytoNumpy(event.Jet_chEmEF)
        Jet_neEmEF = self.ArraytoNumpy(event.Jet_neEmEF)
        Jet_muonIdx1 = self.ArraytoNumpy(event.Jet_muonIdx1)
        Jet_muonIdx2 = self.ArraytoNumpy(event.Jet_muonIdx2)

        Jet_sel_vetomapsel = ( 
                (Jet_jetId>=2) &
                (Jet_pt > 15) &
                (Jet_chEmEF+Jet_neEmEF < 0.9) & 
                (Jet_muonIdx1 == -1) &
                (Jet_muonIdx2 == -1)
                )

        Jet_eta_vetomapsel = Jet_eta[Jet_sel_vetomapsel]
        Jet_phi_vetomapsel = Jet_phi[Jet_sel_vetomapsel]

        if len(Jet)>0:
          jet0_phi = Jet[0].phi
        else:
          jet0_phi = -1
        #MET = Collection(event, "MET")
        met_phi = event.MET_phi

        SVIdx = event.SDVIdxLUT_SecVtxIdx
        SVIdx = self.ArraytoNumpy(SVIdx)
        TkIdx = event.SDVIdxLUT_TrackIdx
        TkIdx = self.ArraytoNumpy(TkIdx)
        tk_W = event.SDVIdxLUT_TrackWeight
        tk_W = self.ArraytoNumpy(tk_W)
        TrackVtxdist2d = event.SDVIdxLUT_TrackVtxdist2d
        TrackVtxdist2d = self.ArraytoNumpy(TrackVtxdist2d)
        TrackVtxdist2d_err = event.SDVIdxLUT_TrackVtxdist2d_err
        TrackVtxdist2d_err = self.ArraytoNumpy(TrackVtxdist2d_err)
        TrackVtxdist3d = event.SDVIdxLUT_TrackVtxdist3d
        TrackVtxdist3d = self.ArraytoNumpy(TrackVtxdist3d)
        TrackVtxdist3d_err = event.SDVIdxLUT_TrackVtxdist3d_err
        TrackVtxdist3d_err = self.ArraytoNumpy(TrackVtxdist3d_err)

        d = {
          "Track_pt": self.ArraytoNumpy(event.SDVTrack_pt),
          "Track_eta": self.ArraytoNumpy(event.SDVTrack_eta),
          "Track_phi": self.ArraytoNumpy(event.SDVTrack_phi),
          "Track_dxy": self.ArraytoNumpy(event.SDVTrack_dxy),
          "Track_dxyError": self.ArraytoNumpy(event.SDVTrack_dxyError),
          "Track_dz": self.ArraytoNumpy(event.SDVTrack_dz),
          "Track_normalizedChi2": self.ArraytoNumpy(event.SDVTrack_normalizedChi2),
          "Track_pfRelIso03_all": self.ArraytoNumpy(event.SDVTrack_pfRelIso03_all),
        }

        d_vtx_gets = {
            "SDVSecVtx_pt": "pt",
            "SDVSecVtx_L_eta": "L_eta",
            "SDVSecVtx_L_phi": "L_phi",
            "SDVSecVtx_lxySig": "LxySig",
            "SDVSecVtx_pAngle": "pAngle",
            "SDVSecVtx_charge": "charge",
            "SDVSecVtx_chi2": "chi2",
            "SDVSecVtx_ndof": "ndof",
            "SDVSecVtx_sum_tkW": "sum_tkW",
            "SDVSecVtx_tracksSize": "tracksSize",
        }

        d_vtx_evals = {
            "SDVSecVtx_pt_log": "np.log(dv['SDVSecVtx_pt'])",
            "SDVSecVtx_LxySig_log": "np.log(dv['SDVSecVtx_lxySig'])",
            "SDVSecVtx_chi2_norm": "dv['SDVSecVtx_chi2']/dv['SDVSecVtx_ndof']",
            "SDVSecVtx_sum_tkW_norm": "dv['SDVSecVtx_sum_tkW']/dv['SDVSecVtx_tracksSize']",
                }

        evals = {
            "SDVTrack_pt_log": "np.log(dv['SDVTrack_pt'])",
            "SDVTrack_dxydzratio": "dv['SDVTrack_dxy']/(dv['SDVTrack_dz']+1e-4)",
            "SDVTrack_dxySig": "dv['SDVTrack_dxy']/(dv['SDVTrack_dxyError']+1e-4)",
            "SDVTrack_pfRelIso03_all_log": "np.log(dv['SDVTrack_pfRelIso03_all']+1e-4)",
            "SDVTrack_cosdphivtx": "np.cos(self.deltaPhi(dv['SDVTrack_phi']-dv['SDVSecVtx_L_phi']))",
            "SDVTrack_mask": "np.ones_like(dv['SDVTrack_pt_log'])",
            }

        # create input data
        d_input = {}
        for input_name in self.params['input_names']:
          if input_name in self.excludeinput:
            continue
          d_input[input_name] = []

        mass = 0.13957018

        for ivtx in range(len(SDVSecVtx)):
            d_input_pervtx = {}
            for input_name in d_input:
              d_input_pervtx[input_name] = []
            vtxtksIdx = TkIdx[SVIdx==ivtx].astype(np.int32)

            dv = {}
            for ie in d_vtx_gets:
              dv[ie] = getattr(SDVSecVtx[ivtx],d_vtx_gets[ie])
            for ie in d_vtx_evals:
              dv[ie] = eval(d_vtx_evals[ie])

            if (len(Jet_eta_vetomapsel))>0:
                dRs = self.deltaR(Jet_eta_vetomapsel-dv['SDVSecVtx_L_eta'],Jet_phi_vetomapsel-dv['SDVSecVtx_L_phi'])
                dv['SDVSecVtx_closestJetdR'] = np.min(dRs)
            else:
                dv['SDVSecVtx_closestJetdR'] = np.nan

            for ie in d:
              dv["SDV"+ie] = np.array(d[ie])[vtxtksIdx]

            dv["SDVTrack_M"] = np.array([mass]*len(dv["SDVTrack_pt"]))
            p4 = vector.array({
              "pt":dv["SDVTrack_pt"],
              "phi":dv["SDVTrack_phi"],
              "eta":dv["SDVTrack_eta"],
              "M":dv["SDVTrack_M"]
              })
            dv["SDVTrack_px"] = p4.px
            dv["SDVTrack_py"] = p4.py
            dv["SDVTrack_pz"] = p4.pz
            dv["SDVTrack_E"] = p4.E

            for ie in evals:
              dv[ie] = eval(evals[ie])

            for input_name in d_input:
              for vn in self.params[input_name]['var_names']:
                varr = dv[vn]
                if np.isscalar(varr):
                  varr = np.array([varr])
                if vn in self.params[input_name]['var_infos']:
                  # Normalise the data
                  median = self.params[input_name]['var_infos'][vn]['median']
                  norm_factor = self.params[input_name]['var_infos'][vn]['norm_factor']
                  varr = (varr-median)*norm_factor

                # Pad the data (zero-padding)
                npfs = self.params[input_name]['var_length']
                #pad_value = self.params[input_name]['var_infos'][vn]['pad']
                #pad_value = float("nan")
                pad_value = 0
                if vn=="SDVTrack_mask":
                    pad_value = 0
                if npfs-len(varr)>0:
                  varr = np.pad(varr,(0,npfs-len(varr)),'constant',constant_values=pad_value)
                varr = varr[:npfs]

                d_input_pervtx[input_name].append(varr)
              d_input_pervtx[input_name] = np.array(d_input_pervtx[input_name])
              d_input[input_name].append(d_input_pervtx[input_name])

        if (len(SDVSecVtx)>0):
          for input_name in d_input:
                d_input[input_name] = np.array(d_input[input_name]).astype(np.float32)

          # run inference
          outputs = self.ort_sess.run(None, d_input)[0]
          # print input and output
          #for i in d_input:
          #    print(i,d_input[i].shape)
        else:
          outputs = np.zeros((0,2))
        #print('output ->', outputs[:,1])
        #print('origin ->', event.vtx_PART_1111best_valloss_epoch)

        self.out.fillBranch("SDVSecVtx_ParTScore", outputs[:,1])
        if len(outputs[:,1])>0 and (max(outputs[:,1])>0.999):
            print("="*50)
            print('origin ->', self.ArraytoNumpy(event.vtx_PART_1111best_valloss_epoch))
            print("input")
            print(d_input)
            print("score")
            print(outputs[:,1])
            print("="*50)
        return True

# define modules using the syntax 'name = lambda : constructor' to avoid having them loaded when not needed

ParTScoreModuleConstr = lambda : ParTScoreProducer('/groups/hephy/cms/ang.li/MLModels/ParT_1111.onnx', '/groups/hephy/cms/ang.li/MLModels/preprocess_ParT_1111.json')
