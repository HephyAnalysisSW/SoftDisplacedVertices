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
import math

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
        self.out.branch("nRotateVtx", "I")
        self.out.branch("RotateVtx_mass", "F", lenVar="nRotateVtx")
        self.out.branch("RotateVtx_mass_before", "F", lenVar="nRotateVtx")
        self.out.branch("RotateVtx_pt", "F", lenVar="nRotateVtx")
        self.out.branch("RotateVtx_pAngle", "F", lenVar="nRotateVtx")
        self.out.branch("RotateVtx_trackphi0", "F", lenVar="nRotateVtx")
        self.out.branch("RotateVtx_trackphi1", "F", lenVar="nRotateVtx")
        self.out.branch("RotateVtx_trackphi2", "F", lenVar="nRotateVtx")
        self.out.branch("RotateVtx_MLScore", "F", lenVar="nRotateVtx")
        self.out.branch("RotateVtx_MLScore_before", "F", lenVar="nRotateVtx")
        self.out.branch("RotateVtx_vtxIdx", "I", lenVar="nRotateVtx")
        self.out.branch("RotateVtx_tk0Idx", "I", lenVar="nRotateVtx")
        self.out.branch("RotateVtx_tk1Idx", "I", lenVar="nRotateVtx")
        self.out.branch("RotateVtx_tk2Idx", "I", lenVar="nRotateVtx")
        self.out.branch("RotateVtx_refittk0Idx", "I", lenVar="nRotateVtx")
        self.out.branch("RotateVtx_refittk1Idx", "I", lenVar="nRotateVtx")
        self.out.branch("RotateVtx_refittk2Idx", "I", lenVar="nRotateVtx")

    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        pass

    def analyze(self, event):
        """process event, return True (go to next module) or False (fail, go to next event)"""

        pvx = event.PV_x
        pvy = event.PV_y
        pvz = event.PV_z


        SDVSecVtx = Collection(event, "SDVSecVtx")
        SDVTrack = Collection(event, "SDVTrack")
        SDVIdxLUT = Collection(event, "SDVIdxLUT")

        SDVMLScore = self.ArraytoNumpy(event.vtx_PART_1111best_valloss_epoch)

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
        #TrackVtxdist2d = event.SDVIdxLUT_TrackVtxdist2d
        #TrackVtxdist2d = self.ArraytoNumpy(TrackVtxdist2d)
        #TrackVtxdist2d_err = event.SDVIdxLUT_TrackVtxdist2d_err
        #TrackVtxdist2d_err = self.ArraytoNumpy(TrackVtxdist2d_err)
        #TrackVtxdist3d = event.SDVIdxLUT_TrackVtxdist3d
        #TrackVtxdist3d = self.ArraytoNumpy(TrackVtxdist3d)
        #TrackVtxdist3d_err = event.SDVIdxLUT_TrackVtxdist3d_err
        #TrackVtxdist3d_err = self.ArraytoNumpy(TrackVtxdist3d_err)

        Track_pt = self.ArraytoNumpy(event.SDVTrack_pt)
        Track_eta = self.ArraytoNumpy(event.SDVTrack_eta)
        Track_phi = self.ArraytoNumpy(event.SDVTrack_phi)
        Track_dxy = self.ArraytoNumpy(event.SDVTrack_dxy)
        Track_dxyError = self.ArraytoNumpy(event.SDVTrack_dxyError)
        Track_dz = self.ArraytoNumpy(event.SDVTrack_dz)
        Track_normalizedChi2 = self.ArraytoNumpy(event.SDVTrack_normalizedChi2)
        Track_pfRelIso03_all = self.ArraytoNumpy(event.SDVTrack_pfRelIso03_all)
        Track_charge = self.ArraytoNumpy(event.SDVTrack_charge)

        RefitTrack_pt = self.ArraytoNumpy(event.SDVRefitTrack_pt)
        RefitTrack_eta = self.ArraytoNumpy(event.SDVRefitTrack_eta)
        RefitTrack_phi = self.ArraytoNumpy(event.SDVRefitTrack_phi)
        RefitTrack_tkIdx = self.ArraytoNumpy(event.SDVRefitTrack_tkIdx)

        d = {
          "Track_pt": self.ArraytoNumpy(event.SDVTrack_pt),
          "Track_eta": self.ArraytoNumpy(event.SDVTrack_eta),
          #"Track_phi": self.ArraytoNumpy(event.SDVTrack_phi),
          #"Track_dxy": self.ArraytoNumpy(event.SDVTrack_dxy),
          "Track_dxyError": self.ArraytoNumpy(event.SDVTrack_dxyError),
          "Track_dz": self.ArraytoNumpy(event.SDVTrack_dz),
          "Track_normalizedChi2": self.ArraytoNumpy(event.SDVTrack_normalizedChi2),
          "Track_pfRelIso03_all": self.ArraytoNumpy(event.SDVTrack_pfRelIso03_all),
        }

        d_derive = {
                'Track_phi': "VtxTrack_phi_rot",
                'Track_dxy': "vtx_Lxy",
                }

        d_vtx_gets = {
            #"SDVSecVtx_pt": "pt",
            "SDVSecVtx_L_eta": "L_eta",
            "SDVSecVtx_L_phi": "L_phi",
            "SDVSecVtx_lxySig": "LxySig",
            #"SDVSecVtx_pAngle": "pAngle",
            "SDVSecVtx_charge": "charge",
            "SDVSecVtx_chi2": "chi2",
            "SDVSecVtx_ndof": "ndof",
            "SDVSecVtx_sum_tkW": "sum_tkW",
            "SDVSecVtx_tracksSize": "tracksSize",
        }

        d_vtx_derives = {
            "SDVSecVtx_pt": "vtx_pt_rot",
            "SDVSecVtx_pAngle": "vtx_pAngle_rot",
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

        mass_pion = 0.13957039
        mass_kaon = 0.493677
        n_vtx = 0
        new_branches = {
                "nRotateVtx": 0,
                "RotateVtx_mass": [],
                "RotateVtx_mass_before": [],
                "RotateVtx_pt": [],
                "RotateVtx_pAngle": [],
                "RotateVtx_trackphi0": [],
                "RotateVtx_trackphi1": [],
                "RotateVtx_trackphi2": [],
                "RotateVtx_MLScore": [],
                "RotateVtx_MLScore_before": [],
                "RotateVtx_vtxIdx": [],
                "RotateVtx_tk0Idx": [],
                "RotateVtx_tk1Idx": [],
                "RotateVtx_tk2Idx": [],
                "RotateVtx_refittk0Idx": [],
                "RotateVtx_refittk1Idx": [],
                "RotateVtx_refittk2Idx": [],
                }

        for ivtx in range(len(SDVSecVtx)):

            vtx = SDVSecVtx[ivtx]

            if not ( (abs(vtx.charge)==1) and (vtx.nTracks==3) and (vtx.tracksSize==3)):
                continue
            # reconstruct the vertex mass with different mass assumption
            # obtain the original and refitted track indices
            vtxtksIdx = TkIdx[SVIdx==ivtx].astype(np.int32)
            vtxrefittksIndices = np.arange(len(RefitTrack_tkIdx))
            mapping = dict(zip(RefitTrack_tkIdx, vtxrefittksIndices))
            vtxrefittksIdx = np.array([mapping[x] for x in vtxtksIdx])

            VtxTrack_pt = Track_pt[vtxtksIdx]
            VtxTrack_eta = Track_eta[vtxtksIdx]
            VtxTrack_phi = Track_phi[vtxtksIdx]
            VtxTrack_charge = Track_charge[vtxtksIdx]

            VtxRefitTrack_pt = RefitTrack_pt[vtxrefittksIdx]
            VtxRefitTrack_eta = RefitTrack_eta[vtxrefittksIdx]
            VtxRefitTrack_phi = RefitTrack_phi[vtxrefittksIdx]
            assert len(VtxTrack_pt)==len(VtxRefitTrack_pt),f"Sizes of Track ({len(VtxTrack_pt)}) and refitted track ({len(VtxRefitTrack_pt)}) are different!"

            # Calculate the new vertex variables
            vtx_p4 = ROOT.Math.PtEtaPhiMVector()
            for itk in range(len(VtxRefitTrack_pt)):
                tk_p4 = ROOT.Math.PtEtaPhiMVector()
                tk_p4.SetPt(VtxRefitTrack_pt[itk])
                tk_p4.SetEta(VtxRefitTrack_eta[itk])
                tk_p4.SetPhi(VtxRefitTrack_phi[itk])
                if VtxTrack_charge[itk]==-vtx.charge:
                    tk_p4.SetM(mass_kaon)
                else:
                    tk_p4.SetM(mass_pion)
                vtx_p4 += tk_p4

            vtx_mass = vtx_p4.mass()

            # select only K0 candidate vertices
            if not ( (vtx_mass>1.75) and (vtx_mass<2) ):
                continue

            # Rotate the phi of both original and refitted tracks
            rotate_phi = np.random.uniform(
                -np.pi/2,
                np.pi/2,
                size=len(VtxRefitTrack_pt)
            )
            VtxRefitTrack_phi_rot = VtxRefitTrack_phi + rotate_phi
            VtxTrack_phi_rot = VtxTrack_phi + rotate_phi

            # Calculate the new vertex variables
            vtx_p4_rot = ROOT.Math.PtEtaPhiMVector()
            for itk in range(len(VtxRefitTrack_pt)):
                tk_p4_rot = ROOT.Math.PtEtaPhiMVector()
                tk_p4_rot.SetPt(VtxRefitTrack_pt[itk])
                tk_p4_rot.SetEta(VtxRefitTrack_eta[itk])
                tk_p4_rot.SetPhi(VtxRefitTrack_phi_rot[itk])
                if VtxTrack_charge[itk]==-vtx.charge:
                    tk_p4_rot.SetM(mass_kaon)
                else:
                    tk_p4_rot.SetM(mass_pion)
                vtx_p4_rot += tk_p4_rot

            dx = vtx.x - pvx
            dy = vtx.y - pvy
            dz = vtx.z - pvz
            pdotv_rot = (dx * vtx_p4_rot.Px() + dy * vtx_p4_rot.Py() + dz * vtx_p4_rot.Pz()) / math.sqrt(vtx_p4_rot.P2()) / math.sqrt(dx*dx + dy*dy + dz*dz)
            vtx_pAngle_rot = math.acos(pdotv_rot)
            vtx_pt_rot = vtx_p4_rot.pt()
            vtx_mass_rot = vtx_p4_rot.mass()
            vtx_Lxy = vtx.Lxy

            new_branches["nRotateVtx"] += 1
            new_branches["RotateVtx_mass"].append(vtx_mass_rot)
            new_branches["RotateVtx_mass_before"].append(vtx_mass)
            new_branches["RotateVtx_pt"].append(vtx_pt_rot)
            new_branches["RotateVtx_pAngle"].append(vtx_pAngle_rot)
            new_branches["RotateVtx_trackphi0"].append(VtxTrack_phi_rot[0])
            new_branches["RotateVtx_trackphi1"].append(VtxTrack_phi_rot[1])
            new_branches["RotateVtx_trackphi2"].append(VtxTrack_phi_rot[2])
            new_branches["RotateVtx_MLScore_before"].append(SDVMLScore[ivtx])
            new_branches["RotateVtx_vtxIdx"].append(ivtx)
            new_branches["RotateVtx_tk0Idx"].append(vtxtksIdx[0])
            new_branches["RotateVtx_tk1Idx"].append(vtxtksIdx[1])
            new_branches["RotateVtx_tk2Idx"].append(vtxtksIdx[2])
            new_branches["RotateVtx_refittk0Idx"].append(vtxrefittksIdx[0])
            new_branches["RotateVtx_refittk1Idx"].append(vtxrefittksIdx[1])
            new_branches["RotateVtx_refittk2Idx"].append(vtxrefittksIdx[2])
            
            d_input_pervtx = {}
            for input_name in d_input:
              d_input_pervtx[input_name] = []
            vtxtksIdx = TkIdx[SVIdx==ivtx].astype(np.int32)

            dv = {}
            for ie in d_vtx_gets:
              dv[ie] = getattr(vtx,d_vtx_gets[ie])
            for ie in d_vtx_derives:
              dv[ie] = eval(d_vtx_derives[ie])
            for ie in d_vtx_evals:
              dv[ie] = eval(d_vtx_evals[ie])

            if (len(Jet_eta_vetomapsel))>0:
                dRs = self.deltaR(Jet_eta_vetomapsel-dv['SDVSecVtx_L_eta'],Jet_phi_vetomapsel-dv['SDVSecVtx_L_phi'])
                dv['SDVSecVtx_closestJetdR'] = np.min(dRs) 
            else:
                dv['SDVSecVtx_closestJetdR'] = np.nan

            for ie in d:
              dv["SDV"+ie] = np.array(d[ie])[vtxtksIdx]
            for ie in d_derive:
              dv["SDV"+ie] = eval(d_derive[ie])

            dv["SDVTrack_M"] = np.array([mass_pion]*len(dv["SDVTrack_pt"]))
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

              n_vtx += 1

        if (n_vtx>0):
          for input_name in d_input:
                d_input[input_name] = np.array(d_input[input_name]).astype(np.float32)

          # run inference
          outputs = self.ort_sess.run(None, d_input)[0]
          # print input and output
          #for i in d_input:
          #    print(i,d_input[i].shape)
        else:
          outputs = np.zeros((0,2))
        new_branches["RotateVtx_MLScore"] = outputs[:,1]
        #print(new_branches["RotateVtx_MLScore_before"])
        #print(new_branches["RotateVtx_MLScore"])
        for ib in new_branches:
            self.out.fillBranch(ib, new_branches[ib])

        #self.out.fillBranch("SDVSecVtx_ParTScore", outputs[:,1])
        return True

# define modules using the syntax 'name = lambda : constructor' to avoid having them loaded when not needed

ParTScoreModuleConstr = lambda : ParTScoreProducer('/groups/hephy/cms/ang.li/MLModels/ParT_1111.onnx', '/groups/hephy/cms/ang.li/MLModels/preprocess_ParT_1111.json')
