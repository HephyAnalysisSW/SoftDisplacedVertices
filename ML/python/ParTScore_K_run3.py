from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
import ROOT
ROOT.PyConfig.IgnoreCommandLineOptions = True

import onnxruntime as ort
import numpy as np
import json

# per-vertex inputs: name -> branch suffix of SDVSecVtx
SV_BRANCHES = ["pt", "L_eta", "L_phi", "LxySig", "pAngle", "charge", "chi2", "ndof", "sum_tkW", "tracksSize"]
TRACK_BRANCHES = ["pt", "eta", "phi", "dxy", "dxyError", "dz", "normalizedChi2", "pfRelIso03_all"]
PION_MASS = 0.13957018

class ParTScoreProducer(Module):
    def __init__(self,model_path='',preprocess_json_path=''):
        self.model_path = model_path
        self.preprocess_json_path = preprocess_json_path

    def deltaPhi(self,dphi):
        o2pi = 1. / (2. * np.pi)
        mask = np.abs(dphi) > np.pi
        n = np.round(dphi*o2pi)
        return dphi - n * mask * (2. * np.pi)

    def deltaR(self,deta,dphi):
        dphi = self.deltaPhi(dphi)
        return np.hypot(dphi,deta)

    def ArraytoNumpy(self,array,dtype=np.float64):
        # index access: iterating over a TTreeReaderArray leaks memory in PyROOT
        return np.array([array[i] for i in range(array.GetSize())], dtype=dtype)

    def CharArraytoNumpy(self,array):
        # UChar_t branches are returned by PyROOT as 1-character strings
        return np.array([ord(array[i]) for i in range(array.GetSize())], dtype=np.int32)

    def beginJob(self):
        self.ort_sess = ort.InferenceSession(self.model_path, providers=['CPUExecutionProvider'])
        self.excludeinput = ['pf_points']
        with open(self.preprocess_json_path,'r') as fj:
          self.params = json.load(fj)
        self.input_names = [n for n in self.params['input_names'] if n not in self.excludeinput]
        for input_name in self.input_names:
          # this implementation applies no normalisation
          assert not self.params[input_name]['var_infos'], "var_infos normalisation not supported"

    def endJob(self):
        pass

    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.out = wrappedOutputTree
        self.out.branch("SDVSecVtx_ParTScore", "F", lenVar="nSDVSecVtx")
        # the output tree inherits AutoFlush=0 from the input, which keeps all baskets in memory;
        # flush every ~30 MB instead (changes only the on-disk clustering, not the content)
        self.out.tree().SetAutoFlush(-30000000)

    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        pass

    def selectedJets(self, event):
        """eta, phi of jets passing jetId>=2, pt>15, EM fraction<0.9 and no matched muon"""
        Jet_eta = self.ArraytoNumpy(event.Jet_eta)
        Jet_phi = self.ArraytoNumpy(event.Jet_phi)
        Jet_jetId = self.CharArraytoNumpy(event.Jet_jetId)
        Jet_sel_vetomapsel = (
                (Jet_jetId>=2) &
                (self.ArraytoNumpy(event.Jet_pt) > 15) &
                (self.ArraytoNumpy(event.Jet_chEmEF)+self.ArraytoNumpy(event.Jet_neEmEF) < 0.9) &
                (self.ArraytoNumpy(event.Jet_muonIdx1) == -1) &
                (self.ArraytoNumpy(event.Jet_muonIdx2) == -1)
                )
        return Jet_eta[Jet_sel_vetomapsel], Jet_phi[Jet_sel_vetomapsel]

    def analyze(self, event):
        """process event, return True (go to next module) or False (fail, go to next event)"""
        nvtx = event.nSDVSecVtx
        if nvtx == 0:
          self.out.fillBranch("SDVSecVtx_ParTScore", np.zeros(0))
          return True

        Jet_eta_sel, Jet_phi_sel = self.selectedJets(event)

        # per-vertex variables, shape (nvtx,)
        sv = {b: self.ArraytoNumpy(getattr(event, "SDVSecVtx_"+b)) for b in SV_BRANCHES}
        dv = {
            "SDVSecVtx_pt_log": np.log(sv["pt"]),
            "SDVSecVtx_L_eta": sv["L_eta"],
            "SDVSecVtx_LxySig_log": np.log(sv["LxySig"]),
            "SDVSecVtx_pAngle": sv["pAngle"],
            "SDVSecVtx_charge": sv["charge"],
            "SDVSecVtx_chi2_norm": sv["chi2"]/sv["ndof"],
            "SDVSecVtx_sum_tkW_norm": sv["sum_tkW"]/sv["tracksSize"],
        }
        if len(Jet_eta_sel)>0:
          dRs = self.deltaR(Jet_eta_sel[None,:]-sv["L_eta"][:,None], Jet_phi_sel[None,:]-sv["L_phi"][:,None])
          dv["SDVSecVtx_closestJetdR"] = np.min(dRs, axis=1)
        else:
          dv["SDVSecVtx_closestJetdR"] = np.full(nvtx, np.nan)

        # per-track variables for the whole track collection, shape (ntrk,)
        tk = {b: self.ArraytoNumpy(getattr(event, "SDVTrack_"+b)) for b in TRACK_BRANCHES}
        # four-vector with pion mass, same formulas as vector.array({"pt","phi","eta","M"})
        expmeta = np.exp(-tk["eta"])
        invsintheta = 0.5 * (1 + expmeta ** 2) / expmeta
        mass = np.full(len(tk["pt"]), PION_MASS)
        dt = {
            "SDVTrack_pt_log": np.log(tk["pt"]),
            "SDVTrack_eta": tk["eta"],
            "SDVTrack_dxydzratio": tk["dxy"]/(tk["dz"]+1e-4),
            "SDVTrack_dxySig": tk["dxy"]/(tk["dxyError"]+1e-4),
            "SDVTrack_normalizedChi2": tk["normalizedChi2"],
            "SDVTrack_pfRelIso03_all_log": np.log(tk["pfRelIso03_all"]+1e-4),
            "SDVTrack_px": tk["pt"] * np.cos(tk["phi"]),
            "SDVTrack_py": tk["pt"] * np.sin(tk["phi"]),
            "SDVTrack_pz": tk["pt"] * np.sinh(tk["eta"]),
            "SDVTrack_E": np.sqrt(np.maximum(np.copysign(mass ** 2, mass) + tk["pt"] ** 2 * invsintheta ** 2, 0)),
            "SDVTrack_mask": np.ones(len(tk["pt"])),
        }

        # first npfs tracks of each vertex, in IdxLUT order; -1 marks padding
        npfs = self.params['pf_features']['var_length']
        SVIdx = self.ArraytoNumpy(event.SDVIdxLUT_SecVtxIdx)
        TkIdx = self.ArraytoNumpy(event.SDVIdxLUT_TrackIdx)
        tkidx = np.full((nvtx, npfs), -1, dtype=np.int64)
        for ivtx in range(nvtx):
          vtxtksIdx = TkIdx[SVIdx==ivtx].astype(np.int32)[:npfs]
          tkidx[ivtx, :len(vtxtksIdx)] = vtxtksIdx
        haspf = tkidx >= 0
        dvtx_phi = np.where(haspf, tk["phi"][tkidx], 0.) - sv["L_phi"][:,None]
        dt_vtx = {"SDVTrack_cosdphivtx": np.cos(self.deltaPhi(dvtx_phi))}

        d_input = {}
        for input_name in self.input_names:
          var_names = self.params[input_name]['var_names']
          if input_name == 'sv_features':
            arr = np.stack([dv[vn] for vn in var_names], axis=1)[:,:,None]
          else:
            arr = np.zeros((nvtx, len(var_names), npfs))
            for ivn, vn in enumerate(var_names):
              if vn in dt_vtx:
                arr[:,ivn,:] = np.where(haspf, dt_vtx[vn], 0.)
              else:
                arr[:,ivn,:] = np.where(haspf, dt[vn][tkidx], 0.)
          d_input[input_name] = arr.astype(np.float32)

        outputs = self.ort_sess.run(None, d_input)[0]
        self.out.fillBranch("SDVSecVtx_ParTScore", outputs[:,1])
        return True

# define modules using the syntax 'name = lambda : constructor' to avoid having them loaded when not needed

ParTScoreModuleConstr = lambda : ParTScoreProducer('/groups/hephy/cms/ang.li/MLModels/ParT_1111.onnx', '/groups/hephy/cms/ang.li/MLModels/preprocess_ParT_1111.json')
