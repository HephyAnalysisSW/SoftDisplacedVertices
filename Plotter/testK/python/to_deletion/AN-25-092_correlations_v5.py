"""
Use:
mamba activate /groups/hephy/cms/alikaan.gueven/conda/envs/weaver

A separate table is calculated for each feature level.
No cross-level broadcasting.
Each table gets its own correlation matrix.

N.B. Vertices are matched to signal vertices!

Example:

Assume:

10 vertices.
Each vertex has 4 tracks.
For each vertex, the tracks are t0, t1, t2, t3.


Track-level table:

row   vertex   track   tk_log_pt      tk_eta      tk_cos_sv_L_phi_minus_tk_phi
0     v0       t0      log(pt_t0)     eta_t0      cos(phi_v0 - phi_t0)
1     v0       t1      log(pt_t1)     eta_t1      cos(phi_v0 - phi_t1)
2     v0       t2      log(pt_t2)     eta_t2      cos(phi_v0 - phi_t2)
3     v0       t3      log(pt_t3)     eta_t3      cos(phi_v0 - phi_t3)
...

Rows: 10 vertices * 4 tracks = 40
Columns in tk matrix: 7
Track table shape: (40, 7)
Track correlation matrix shape: (7, 7)


SV-level table:

row   vertex   sv_log_pt      sv_L_eta      sv_closestJetdR
0     v0       log(pt_v0)     eta_v0        closestJetdR_v0
1     v1       log(pt_v1)     eta_v1        closestJetdR_v1
2     v2       log(pt_v2)     eta_v2        closestJetdR_v2
...

Rows: 10 vertices
Columns in sv matrix: 10
SV table shape: (10, 10)
SV correlation matrix shape: (10, 10)


Track-pair-level table:

row   vertex   pair       tk_pair_lnkt   tk_pair_lnz   tk_pair_lndelta
0     v0       (t0,t1)    lnkt(t0,t1)    lnz(t0,t1)    lndelta(t0,t1)
1     v0       (t0,t2)    lnkt(t0,t2)    lnz(t0,t2)    lndelta(t0,t2)
2     v0       (t0,t3)    lnkt(t0,t3)    lnz(t0,t3)    lndelta(t0,t3)
3     v0       (t1,t2)    lnkt(t1,t2)    lnz(t1,t2)    lndelta(t1,t2)
4     v0       (t1,t3)    lnkt(t1,t3)    lnz(t1,t3)    lndelta(t1,t3)
5     v0       (t2,t3)    lnkt(t2,t3)    lnz(t2,t3)    lndelta(t2,t3)
...

Pairs per vertex: 4 choose 2 = 6
Rows: 10 vertices * 6 pairs = 60
Columns in tk_pair matrix: 4
Track-pair table shape: (60, 4)
Track-pair correlation matrix shape: (4, 4)
"""

import glob
import math
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-AN-25-092-correlations-v5")
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


N_WORKERS = 30
CHUNK_SIZE = 5000
DASK_SCHEDULER = "processes"
MAX_FILES = None
MAX_EVENTS = None
TK_EPS = 1e-4
PAIR_EPS = 1e-8
PION_MASS = 0.13957039

PATTERNS = [
    # "/scratch-cbe/users/alikaan.gueven/ML_KAAN/20260112/sig_17-18_old_centralprod_merged/stop_M1000*/**/*.root",
    "/scratch-cbe/users/alikaan.gueven/ML_KAAN/20260112/sig_18/**/*.root"
]

OUT_DIR = Path("/scratch-cbe/users/alikaan.gueven/AN_plots/ParT_hists/AN-25-092_ML_plots3/plots/corr_matrix")

EV_BRANCHES = ["nSDVSecVtx"]
SV_BRANCHES = [
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
    "SDVSecVtx_matchedLLPnDau_bydau",
]
TK_BRANCHES = [
    "SDVTrack_pt",
    "SDVTrack_eta",
    "SDVTrack_phi",
    "SDVTrack_dxy",
    "SDVTrack_dxyError",
    "SDVTrack_dz",
    "SDVTrack_normalizedChi2",
    "SDVTrack_pfRelIso03_all",
]
LUT_BRANCHES = [
    "SDVIdxLUT_SecVtxIdx",
    "SDVIdxLUT_TrackIdx",
]
JET_BRANCHES = [
    "Jet_phi",
    "Jet_eta",
    "Jet_jetId",
    "Jet_pt",
    "Jet_chEmEF",
    "Jet_neEmEF",
    "Jet_muonIdx1",
    "Jet_muonIdx2",
]

TK_COLUMNS = [
    "tk_log_pt",
    "tk_eta",
    "tk_dxy_over_dz",
    "tk_dxy_over_dxyError",
    "tk_normalizedChi2",
    "tk_log_pfRelIso03_all",
    "tk_cos_sv_L_phi_minus_tk_phi",
]

SV_COLUMNS = [
    "sv_log_pt",
    "sv_L_eta",
    "sv_log_LxySig",
    "sv_pAngle",
    "sv_charge",
    "sv_chi2_over_ndof",
    "sv_sum_tkW_over_tracksSize",
    "sv_closestJetdR",
]

TK_PAIR_COLUMNS = [
    "tk_pair_lnkt",
    "tk_pair_lnz",
    "tk_pair_lndelta",
    "tk_pair_lnm2",
]


@njit
def deepTable(tkBranch, trIdx, svIdx, n_sv, sv_mask, builder):
    for ev in range(len(n_sv)):
        builder.begin_list()
        for sv in range(n_sv[ev]):
            if not sv_mask[ev][sv]:
                continue
            builder.begin_list()
            for i2, col in enumerate(svIdx[ev]):
                if col == sv:
                    builder.append(tkBranch[ev][trIdx[ev][i2]])
            builder.end_list()
        builder.end_list()


def deepTable_lazy(tkBranch, trIdx, svIdx, n_sv, sv_mask):
    builder = ak.ArrayBuilder()
    deepTable(tkBranch, trIdx, svIdx, n_sv, sv_mask, builder)
    return builder.snapshot()


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
def fill_pairwise_lv_fts_same_vtx(
    pt,
    eta,
    phi,
    sv_idx,
    tk_idx,
    n_sv,
    sv_mask,
    eps,
    pion_mass,
    builder,
):
    for ev in range(len(n_sv)):
        builder.begin_list()
        n_tracks = len(pt[ev])
        n_lut = len(sv_idx[ev])

        for ivtx in range(n_sv[ev]):
            if not sv_mask[ev][ivtx]:
                continue
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

                    builder.begin_list()
                    builder.append(log_max(ptmin * delta, eps))
                    builder.append(log_max(ptmin / ptsum, eps))
                    builder.append(log_max(delta, eps))
                    builder.append(log_max(m2, eps))
                    builder.end_list()

        builder.end_list()


def make_pairwise_lv_fts_same_vtx(events):
    sv_mask = matched_sv_mask(events)
    builder = ak.ArrayBuilder()
    fill_pairwise_lv_fts_same_vtx(
        events["SDVTrack_pt"],
        events["SDVTrack_eta"],
        events["SDVTrack_phi"],
        events["SDVIdxLUT_SecVtxIdx"],
        events["SDVIdxLUT_TrackIdx"],
        events["nSDVSecVtx"],
        sv_mask,
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
    return EV_BRANCHES + SV_BRANCHES + TK_BRANCHES + LUT_BRANCHES + JET_BRANCHES


def validate_branches(available):
    missing = sorted(set(selected_branches()) - set(available))
    if missing:
        raise KeyError(f"Missing required branches: {missing}")


def matched_sv_mask(events):
    return events["SDVSecVtx_matchedLLPnDau_bydau"] >= 2


def to_flat_dataframe(features, columns):
    return pd.DataFrame(
        {
            name: ak.to_numpy(ak.flatten(features[name], axis=None))
            for name in columns
        }
    )


def make_tk_table(events):
    sv_mask = matched_sv_mask(events)
    arrays = {name: events[name] for name in events.fields}
    for tk in TK_BRANCHES:
        arrays[tk] = deepTable_lazy(
            arrays[tk],
            arrays["SDVIdxLUT_TrackIdx"],
            arrays["SDVIdxLUT_SecVtxIdx"],
            arrays["nSDVSecVtx"],
            sv_mask,
        )

    sv_phi = ak.broadcast_arrays(
        arrays["SDVSecVtx_L_phi"][sv_mask][..., np.newaxis],
        arrays["SDVTrack_pt"],
    )[0]

    return to_flat_dataframe(
        {
            "tk_log_pt": np.log(arrays["SDVTrack_pt"]),
            "tk_eta": arrays["SDVTrack_eta"],
            "tk_dxy_over_dz": arrays["SDVTrack_dxy"] / (arrays["SDVTrack_dz"] + TK_EPS),
            "tk_dxy_over_dxyError": arrays["SDVTrack_dxy"] / (arrays["SDVTrack_dxyError"] + TK_EPS),
            "tk_normalizedChi2": arrays["SDVTrack_normalizedChi2"],
            "tk_log_pfRelIso03_all": np.log(TK_EPS + arrays["SDVTrack_pfRelIso03_all"]),
            "tk_cos_sv_L_phi_minus_tk_phi": np.cos(sv_phi - arrays["SDVTrack_phi"]),
        },
        TK_COLUMNS,
    )


def make_sv_table(events):
    sv_mask = matched_sv_mask(events)
    return to_flat_dataframe(
        {
            "sv_log_pt": np.log(events["SDVSecVtx_pt"])[sv_mask],
            "sv_L_eta": events["SDVSecVtx_L_eta"][sv_mask],
            "sv_log_LxySig": np.log(events["SDVSecVtx_LxySig"])[sv_mask],
            "sv_pAngle": events["SDVSecVtx_pAngle"][sv_mask],
            "sv_charge": events["SDVSecVtx_charge"][sv_mask],
            "sv_chi2_over_ndof": (events["SDVSecVtx_chi2"] / events["SDVSecVtx_ndof"])[sv_mask],
            "sv_sum_tkW_over_tracksSize": (events["SDVSecVtx_sum_tkW"] / events["SDVSecVtx_tracksSize"])[sv_mask],
            "sv_closestJetdR": closest_jet_dr(events)[sv_mask],
        },
        SV_COLUMNS,
    )


def make_tk_pair_table(events):
    pair_features = make_pairwise_lv_fts_same_vtx(events)
    return pd.DataFrame(
        {
            name: ak.to_numpy(ak.flatten(pair_features[..., i], axis=None))
            for i, name in enumerate(TK_PAIR_COLUMNS)
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

    return {
        "tk": corr_stats(make_tk_table(events)),
        "sv": corr_stats(make_sv_table(events)),
        "tk_pair": corr_stats(make_tk_pair_table(events)),
    }


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


def add_cms_label(ax):
    ax.text(
        0.0,
        1.025,
        "CMS",
        ha="left",
        va="bottom",
        fontsize=18,
        fontweight="bold",
        transform=ax.transAxes,
    )
    ax.text(
        0.185,
        1.028,
        "Simulation Preliminary",
        ha="left",
        va="bottom",
        fontsize=14,
        fontstyle="italic",
        transform=ax.transAxes,
    )
    ax.text(
        1.2,
        1.028,
        "(13 TeV)",
        ha="right",
        va="bottom",
        fontsize=14,
        transform=ax.transAxes,
    )


def plot_corr(corr, out_png, out_pdf):
    size = max(7.0, 0.75 * len(corr.columns))
    fig, ax = plt.subplots(figsize=(size, size), dpi=200)
    sns.heatmap(
        corr * 100.0,
        annot=True,
        ax=ax,
        cmap="vlag",
        fmt=".0f",
        annot_kws={"size": 8},
        vmin=-100,
        vmax=100,
        cbar_kws={"label": "Pearson correlation coefficient, r (%)"},
    )
    ax.set_xticks(np.arange(len(corr.columns)) + 0.5)
    ax.set_xticklabels(corr.columns, rotation=75, ha="right")
    ax.set_yticklabels(corr.index, rotation=0)
    add_cms_label(ax)
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.92))
    fig.savefig(out_png)
    fig.savefig(out_pdf)
    plt.close(fig)


def save_outputs(level, corr):
    out_csv = OUT_DIR / f"AN-25-092_correlations_v5_{level}.csv"
    out_png = OUT_DIR / f"AN-25-092_correlations_v5_{level}.png"
    out_pdf = OUT_DIR / f"AN-25-092_correlations_v5_{level}.pdf"
    corr.to_csv(out_csv)
    plot_corr(corr, out_png, out_pdf)
    print(f"saved {out_csv}")
    print(f"saved {out_png}")
    print(f"saved {out_pdf}")


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
    chunk_stats = compute(*tasks, scheduler=DASK_SCHEDULER, num_workers=N_WORKERS)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for level in ("tk", "sv", "tk_pair"):
        corr = combine_stats([item[level] for item in chunk_stats])
        save_outputs(level, corr)


if __name__ == "__main__":
    main()
