"""
Use:
mamba activate /groups/hephy/cms/alikaan.gueven/conda/envs/weaver

A table is prepared like the following, and then the correlation matrix is computed from this table.
Example:

Assume:

10 vertices.
Each vertex has 4 tracks.
For each vertex, the tracks are t0, t1, t2, t3.


row   vertex   pair       track   tk_log_pt      sv_log_pt      SDVTrack_pair_lnkt
0     v0       (t0,t1)    t0      log(pt_t0)     log(pt_v0)     lnkt(t0,t1)
1     v0       (t0,t1)    t1      log(pt_t1)     log(pt_v0)     lnkt(t0,t1)

2     v0       (t0,t2)    t0      log(pt_t0)     log(pt_v0)     lnkt(t0,t2)
3     v0       (t0,t2)    t2      log(pt_t2)     log(pt_v0)     lnkt(t0,t2)

4     v0       (t0,t3)    t0      log(pt_t0)     log(pt_v0)     lnkt(t0,t3)
5     v0       (t0,t3)    t3      log(pt_t3)     log(pt_v0)     lnkt(t0,t3)

6     v0       (t1,t2)    t1      log(pt_t1)     log(pt_v0)     lnkt(t1,t2)
7     v0       (t1,t2)    t2      log(pt_t2)     log(pt_v0)     lnkt(t1,t2)

8     v0       (t1,t3)    t1      log(pt_t1)     log(pt_v0)     lnkt(t1,t3)
9     v0       (t1,t3)    t3      log(pt_t3)     log(pt_v0)     lnkt(t1,t3)

10    v0       (t2,t3)    t2      log(pt_t2)     log(pt_v0)     lnkt(t2,t3)
11    v0       (t2,t3)    t3      log(pt_t3)     log(pt_v0)     lnkt(t2,t3)


So the final dimensions will be:

Input vertices:              10
Tracks per vertex:            4
Pairs per vertex:             6
Rows per pair:                2
Rows per vertex:             12
Total rows:                 120
Columns in v3:               21

Final table shape:       (120, 21)
Correlation matrix shape: (21, 21)


N.B. The correlation matrix is weighted by track multiplicity.
     Therefore, high-multiplicity vertices dominate the matrix.


N.B. This version is useful for this kind of question:
         For tracks that appear inside same-vertex track pairs, how do the properties of
         the individual track relate to the properties of the pair it belongs to?

"""

import glob
import math
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-AN-25-092-correlations-v3")
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
PAIR_EPS = 1e-8
PION_MASS = 0.13957039

PATTERNS = [
    "/scratch-cbe/users/alikaan.gueven/ML_KAAN/20260112/sig_17-18_old_centralprod_merged/stop_M1000*/**/*.root",
]

OUT_DIR = Path("/scratch-cbe/users/alikaan.gueven/AN_plots/ParT_hists/AN-25-092_ML_plots3/plots/corr_matrix")
OUT_PNG = OUT_DIR / "AN-25-092_correlations_v3.png"
OUT_CSV = OUT_DIR / "AN-25-092_correlations_v3.csv"

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
    "tk_pair_lnkt",
    "tk_pair_lnz",
    "tk_pair_lndelta",
    "tk_pair_lnm2",
    "sv_log_pt",
    "sv_L_eta",
    "sv_log_LxySig",
    "sv_pAngle",
    "sv_charge",
    "sv_chi2_over_ndof",
    "sv_sum_tkW_over_tracksSize",
    "sv_closestJetdR",
    "vtx_PART_1111best_valloss_epoch",
    "sv_matchedLLPnDau_bydau",
]


@njit
def rapidity(pt, eta, mass):
    pz = pt * math.sinh(eta)
    energy = math.sqrt(pt * pt + pz * pz + mass * mass)
    return 0.5 * math.log((energy + pz) / (energy - pz))


@njit
def log_max(value, eps):
    if math.isnan(value):
        return value
    if value < eps:
        value = eps
    return math.log(value)


@njit
def log_raw(value):
    if math.isnan(value):
        return value
    if value <= 0.0:
        return float("nan")
    return math.log(value)


@njit
def fill_track_pair_rows_same_vtx(
    pt,
    eta,
    phi,
    dxy,
    dxy_error,
    dz,
    normalized_chi2,
    pf_rel_iso03_all,
    sv_idx,
    tk_idx,
    n_sv,
    sv_pt,
    sv_l_eta,
    sv_l_phi,
    sv_lxy_sig,
    sv_pangle,
    sv_charge,
    sv_chi2,
    sv_ndof,
    sv_sum_tkw,
    sv_tracks_size,
    sv_closest_jet_dr,
    vtx_score,
    sv_label,
    tk_eps,
    eps,
    pion_mass,
    builder,
):
    for ev in range(len(n_sv)):
        builder.begin_list()
        n_tracks = len(pt[ev])
        n_lut = len(sv_idx[ev])

        for ivtx in range(n_sv[ev]):
            for a in range(n_lut):
                if sv_idx[ev][a] != ivtx:
                    continue

                i = tk_idx[ev][a]
                if i < 0 or i >= n_tracks:
                    continue

                pti = pt[ev][i]
                etai = eta[ev][i]
                phii = phi[ev][i]
                yi = rapidity(pti, etai, pion_mass)
                pxi = pti * math.cos(phii)
                pyi = pti * math.sin(phii)
                pzi = pti * math.sinh(etai)
                ei = math.sqrt(pti * pti + pzi * pzi + pion_mass * pion_mass)

                for b in range(a + 1, n_lut):
                    if sv_idx[ev][b] != ivtx:
                        continue

                    j = tk_idx[ev][b]
                    if j < 0 or j >= n_tracks:
                        continue

                    ptj = pt[ev][j]
                    etaj = eta[ev][j]
                    phij = phi[ev][j]
                    yj = rapidity(ptj, etaj, pion_mass)
                    pxj = ptj * math.cos(phij)
                    pyj = ptj * math.sin(phij)
                    pzj = ptj * math.sinh(etaj)
                    ej = math.sqrt(ptj * ptj + pzj * pzj + pion_mass * pion_mass)

                    dphi = math.atan2(math.sin(phii - phij), math.cos(phii - phij))
                    dy = yi - yj
                    delta = math.sqrt(dy * dy + dphi * dphi)
                    ptmin = pti if pti < ptj else ptj
                    ptsum = pti + ptj
                    if (not math.isnan(ptsum)) and ptsum < eps:
                        ptsum = eps

                    esum = ei + ej
                    pxsum = pxi + pxj
                    pysum = pyi + pyj
                    pzsum = pzi + pzj
                    m2 = esum * esum - pxsum * pxsum - pysum * pysum - pzsum * pzsum

                    lnkt = log_max(ptmin * delta, eps)
                    lnz = log_max(ptmin / ptsum, eps)
                    lndelta = log_max(delta, eps)
                    lnm2 = log_max(m2, eps)

                    for idx in (i, j):
                        builder.begin_list()
                        builder.append(log_raw(pt[ev][idx]))
                        builder.append(eta[ev][idx])
                        builder.append(dxy[ev][idx] / (dz[ev][idx] + tk_eps))
                        builder.append(dxy[ev][idx] / (dxy_error[ev][idx] + tk_eps))
                        builder.append(normalized_chi2[ev][idx])
                        builder.append(log_raw(tk_eps + pf_rel_iso03_all[ev][idx]))
                        builder.append(math.cos(sv_l_phi[ev][ivtx] - phi[ev][idx]))
                        builder.append(lnkt)
                        builder.append(lnz)
                        builder.append(lndelta)
                        builder.append(lnm2)
                        builder.append(log_raw(sv_pt[ev][ivtx]))
                        builder.append(sv_l_eta[ev][ivtx])
                        builder.append(log_raw(sv_lxy_sig[ev][ivtx]))
                        builder.append(sv_pangle[ev][ivtx])
                        builder.append(sv_charge[ev][ivtx])
                        builder.append(sv_chi2[ev][ivtx] / sv_ndof[ev][ivtx])
                        builder.append(sv_sum_tkw[ev][ivtx] / sv_tracks_size[ev][ivtx])
                        builder.append(sv_closest_jet_dr[ev][ivtx])
                        builder.append(vtx_score[ev][ivtx])
                        builder.append(sv_label[ev][ivtx])
                        builder.end_list()

        builder.end_list()


def make_track_pair_table(events, sv_closest_jet_dr):
    builder = ak.ArrayBuilder()
    fill_track_pair_rows_same_vtx(
        events["SDVTrack_pt"],
        events["SDVTrack_eta"],
        events["SDVTrack_phi"],
        events["SDVTrack_dxy"],
        events["SDVTrack_dxyError"],
        events["SDVTrack_dz"],
        events["SDVTrack_normalizedChi2"],
        events["SDVTrack_pfRelIso03_all"],
        events["SDVIdxLUT_SecVtxIdx"],
        events["SDVIdxLUT_TrackIdx"],
        events["nSDVSecVtx"],
        events["SDVSecVtx_pt"],
        events["SDVSecVtx_L_eta"],
        events["SDVSecVtx_L_phi"],
        events["SDVSecVtx_LxySig"],
        events["SDVSecVtx_pAngle"],
        events["SDVSecVtx_charge"],
        events["SDVSecVtx_chi2"],
        events["SDVSecVtx_ndof"],
        events["SDVSecVtx_sum_tkW"],
        events["SDVSecVtx_tracksSize"],
        sv_closest_jet_dr,
        events["vtx_PART_1111best_valloss_epoch"],
        events["SDVSecVtx_matchedLLPnDau_bydau"],
        1e-4,
        PAIR_EPS,
        PION_MASS,
        builder,
    )
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
    sv_closest_jet_dr = closest_jet_dr(events)
    rows = make_track_pair_table(events, sv_closest_jet_dr)

    return pd.DataFrame(
        {
            name: ak.to_numpy(ak.flatten(rows[..., i], axis=None))
            for i, name in enumerate(FEATURE_COLUMNS)
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
    plt.figure(figsize=(13, 11), dpi=200)
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
