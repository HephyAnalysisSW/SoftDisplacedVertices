"""
Use:
mamba activate /groups/hephy/cms/alikaan.gueven/conda/envs/weaver
"""

import glob
import math
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-AN-25-092-correlations-v2")
for thread_var in (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "NUMEXPR_NUM_THREADS",
):
    os.environ.setdefault(thread_var, "1")

import awkward as ak
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import uproot
from dask import compute, delayed
from numba import njit


N_WORKERS = 16
CHUNK_SIZE = 5000
DASK_SCHEDULER = "processes"
MAX_FILES = None
MAX_EVENTS = None
EPS = 1e-4

PATTERNS = [
    "/scratch-cbe/users/alikaan.gueven/ML_KAAN/20260112/sig_17-18_old_centralprod_merged/stop_M1000*/**/*.root",
]

OUT_DIR = Path("/scratch-cbe/users/alikaan.gueven/AN_plots/ParT_hists/AN-25-092_ML_plots3/plots/corr_matrix")
OUT_PNG = OUT_DIR / "AN-25-092_correlations_v2.png"
OUT_CSV = OUT_DIR / "AN-25-092_correlations_v2.csv"

BRANCHES = {
    "ev": [
        "nSDVSecVtx",
    ],
    "sv": [
        "SDVSecVtx_pt",
        "SDVSecVtx_pAngle",
        "SDVSecVtx_charge",
        "SDVSecVtx_ndof",
        "SDVSecVtx_chi2",
        "SDVSecVtx_tracksSize",
        "SDVSecVtx_sum_tkW",
        "SDVSecVtx_LxySig",
        "SDVSecVtx_L_phi",
        "SDVSecVtx_L_eta",
        "vtx_PART_1111best_valloss_epoch",
        "SDVSecVtx_matchedLLPnDau_bydau",
    ],
    "tk": [
        "SDVTrack_pt",
        "SDVTrack_eta",
        "SDVTrack_phi",
        "SDVTrack_dxy",
        "SDVTrack_dxyError",
        "SDVTrack_dz",
        "SDVTrack_normalizedChi2",
        "SDVTrack_pfRelIso03_all",
    ],
    "lut": [
        "SDVIdxLUT_SecVtxIdx",
        "SDVIdxLUT_TrackIdx",
    ],
    "jet": [
        "Jet_phi",
        "Jet_eta",
        "Jet_jetId",
        "Jet_pt",
        "Jet_chEmEF",
        "Jet_neEmEF",
        "Jet_muonIdx1",
        "Jet_muonIdx2",
    ],
}

FEATURE_COLUMNS = [
    "tk_log_pt",
    "tk_eta",
    "tk_dxy_over_dz",
    "tk_dxy_over_dxyError",
    "tk_normalizedChi2",
    "tk_log_pfRelIso03_all",
    "tk_cos_sv_L_phi_minus_tk_phi",
    "sv_log_pt",
    "sv_L_eta",
    "sv_log_LxySig",
    "sv_pAngle",
    "sv_charge",
    "sv_chi2_over_ndof",
    "sv_sum_tkW_over_tracksSize",
    "sv_closestJetdR",
    "vtx_PART_1111best_valloss_epoch",
    "SDVSecVtx_matchedLLPnDau_bydau",
]


@njit
def deepTable(tkBranch, trIdx, svIdx, n_sv, builder):
    for ev in range(len(n_sv)):
        builder.begin_list()
        for sv in range(n_sv[ev]):
            builder.begin_list()
            for i2, col in enumerate(svIdx[ev]):
                if col == sv:
                    builder.append(tkBranch[ev][trIdx[ev][i2]])
            builder.end_list()
        builder.end_list()


def deepTable_lazy(tkBranch, trIdx, svIdx, n_sv):
    builder = ak.ArrayBuilder()
    deepTable(tkBranch, trIdx, svIdx, n_sv, builder)
    return builder.snapshot()


@njit
def vertex_min_dR(v_phi, v_eta, j_phi, j_eta, n_ev, n_vtx, n_jet, builder):
    for ev in range(n_ev):
        builder.begin_list()
        for vtx in range(n_vtx[ev]):
            best_dR = None
            for jet in range(n_jet[ev]):
                dphi = math.acos(math.cos(j_phi[ev][jet] - v_phi[ev][vtx]))
                deta = abs(j_eta[ev][jet] - v_eta[ev][vtx])
                dR = math.hypot(dphi, deta)
                if (best_dR is None) or (dR < best_dR):
                    best_dR = dR
            builder.append(best_dR)
        builder.end_list()


def closest_jet_dr(events):
    jet_is_tight = ak.values_astype(events["Jet_jetId"] & (1 << 1), bool)
    jet_sel = (
        jet_is_tight
        & (events["Jet_pt"] > 15)
        & ((events["Jet_chEmEF"] + events["Jet_neEmEF"]) < 0.9)
        & (events["Jet_muonIdx1"] == -1)
        & (events["Jet_muonIdx2"] == -1)
    )

    jet_phi = ak.fill_none(ak.pad_none(events["Jet_phi"][jet_sel], 1), np.nan)
    jet_eta = ak.fill_none(ak.pad_none(events["Jet_eta"][jet_sel], 1), np.nan)

    builder = ak.ArrayBuilder()
    vertex_min_dR(
        events["SDVSecVtx_L_phi"],
        events["SDVSecVtx_L_eta"],
        jet_phi,
        jet_eta,
        len(events["nSDVSecVtx"]),
        ak.num(events["SDVSecVtx_L_phi"], axis=1),
        ak.num(jet_phi, axis=1),
        builder,
    )
    return builder.snapshot()


def selected_branches():
    return [name for group in BRANCHES.values() for name in group]


def validate_branches(available):
    missing = sorted(set(selected_branches()) - set(available))
    if missing:
        raise KeyError(f"Missing required branches: {missing}")


def flatten_feature_table(events):
    arrays = {name: events[name] for name in events.fields}
    arrays["SDVSecVtx_closestJetdR"] = closest_jet_dr(events)

    for tk in BRANCHES["tk"]:
        arrays[tk] = deepTable_lazy(
            arrays[tk],
            arrays["SDVIdxLUT_TrackIdx"],
            arrays["SDVIdxLUT_SecVtxIdx"],
            arrays["nSDVSecVtx"],
        )

    tk_pt = arrays["SDVTrack_pt"]
    sv_l_phi = ak.broadcast_arrays(arrays["SDVSecVtx_L_phi"][..., np.newaxis], tk_pt)[0]

    features = {
        "tk_log_pt": np.log(arrays["SDVTrack_pt"]),
        "tk_eta": arrays["SDVTrack_eta"],
        "tk_dxy_over_dz": arrays["SDVTrack_dxy"] / (arrays["SDVTrack_dz"] + EPS),
        "tk_dxy_over_dxyError": arrays["SDVTrack_dxy"] / (arrays["SDVTrack_dxyError"] + EPS),
        "tk_normalizedChi2": arrays["SDVTrack_normalizedChi2"],
        "tk_log_pfRelIso03_all": np.log(EPS + arrays["SDVTrack_pfRelIso03_all"]),
        "tk_cos_sv_L_phi_minus_tk_phi": np.cos(sv_l_phi - arrays["SDVTrack_phi"]),
    }

    sv_features = {
        "sv_log_pt": np.log(arrays["SDVSecVtx_pt"]),
        "sv_L_eta": arrays["SDVSecVtx_L_eta"],
        "sv_log_LxySig": np.log(arrays["SDVSecVtx_LxySig"]),
        "sv_pAngle": arrays["SDVSecVtx_pAngle"],
        "sv_charge": arrays["SDVSecVtx_charge"],
        "sv_chi2_over_ndof": arrays["SDVSecVtx_chi2"] / arrays["SDVSecVtx_ndof"],
        "sv_sum_tkW_over_tracksSize": arrays["SDVSecVtx_sum_tkW"] / arrays["SDVSecVtx_tracksSize"],
        "sv_closestJetdR": arrays["SDVSecVtx_closestJetdR"],
        "vtx_PART_1111best_valloss_epoch": arrays["vtx_PART_1111best_valloss_epoch"],
        "SDVSecVtx_matchedLLPnDau_bydau": arrays["SDVSecVtx_matchedLLPnDau_bydau"],
    }

    for name, values in sv_features.items():
        features[name] = ak.broadcast_arrays(values[..., np.newaxis], tk_pt)[0]

    return pd.DataFrame(
        {
            name: ak.to_numpy(ak.flatten(features[name], axis=None))
            for name in FEATURE_COLUMNS
        }
    )


def corr_stats(df):
    values = df.to_numpy(dtype=np.float64, copy=False)
    valid = np.isfinite(values)
    clean = np.where(valid, values, 0.0)
    valid = valid.astype(np.float64)

    return {
        "columns": list(df.columns),
        "count": valid.T @ valid,
        "sum": clean.T @ valid,
        "sum2": (clean * clean).T @ valid,
        "cross": clean.T @ clean,
    }


def process_chunk(file_name, start, stop):
    with uproot.open(file_name)["Events"] as tree:
        events = tree.arrays(
            selected_branches(),
            library="ak",
            entry_start=start,
            entry_stop=stop,
        )

    return corr_stats(flatten_feature_table(events))


def combine_stats(stats):
    columns = stats[0]["columns"]
    count = sum(item["count"] for item in stats)
    sum_x = sum(item["sum"] for item in stats)
    sum_x2 = sum(item["sum2"] for item in stats)
    cross = sum(item["cross"] for item in stats)

    with np.errstate(invalid="ignore", divide="ignore"):
        cov = (cross - (sum_x * sum_x.T / count)) / (count - 1.0)
        var_x = (sum_x2 - (sum_x * sum_x / count)) / (count - 1.0)
        corr = cov / np.sqrt(var_x * var_x.T)

    corr[(count < 2) | (var_x <= 0.0) | (var_x.T <= 0.0)] = np.nan
    np.fill_diagonal(corr, 1.0)
    return pd.DataFrame(corr, index=columns, columns=columns)


def build_chunks(files):
    chunks = []
    remaining = MAX_EVENTS

    for file_name in files:
        with uproot.open(file_name)["Events"] as tree:
            entries = tree.num_entries

        if remaining is not None:
            entries = min(entries, remaining)

        for start in range(0, entries, CHUNK_SIZE):
            chunks.append((file_name, start, min(start + CHUNK_SIZE, entries)))

        if remaining is not None:
            remaining -= entries
            if remaining <= 0:
                break

    return chunks


def plot_corr(corr):
    plt.figure(figsize=(14, 12), dpi=200)
    sns.heatmap(
        corr * 100.0,
        annot=True,
        cmap="vlag",
        fmt=".0f",
        annot_kws={"size": 8},
        vmin=-100,
        vmax=100,
    )
    plt.xticks(np.arange(len(corr.columns)) + 0.5, corr.columns, rotation=75, ha="right")
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.savefig(OUT_PNG)


def main():
    files = sorted(
        file_name
        for pattern in PATTERNS
        for file_name in glob.glob(pattern, recursive=True)
    )
    if MAX_FILES is not None:
        files = files[:MAX_FILES]
    if not files:
        raise FileNotFoundError("No ROOT files matched PATTERNS")

    with uproot.open(files[0])["Events"] as tree:
        validate_branches(tree.keys())

    chunks = build_chunks(files)
    if not chunks:
        raise ValueError("No event chunks were built")

    print(
        f"processing {len(files)} files in {len(chunks)} chunks "
        f"with {N_WORKERS} {DASK_SCHEDULER} workers"
    )
    tasks = [delayed(process_chunk)(*chunk) for chunk in chunks]
    stats = compute(*tasks, scheduler=DASK_SCHEDULER, num_workers=N_WORKERS)
    corr = combine_stats(stats)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    corr.to_csv(OUT_CSV)
    plot_corr(corr)

    print(f"saved {OUT_CSV}")
    print(f"saved {OUT_PNG}")


if __name__ == "__main__":
    main()
