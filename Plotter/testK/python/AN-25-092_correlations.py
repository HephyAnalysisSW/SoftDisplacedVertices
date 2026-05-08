"""
Use: 
mamba activate /groups/hephy/cms/alikaan.gueven/conda/envs/weaver
"""

import fnmatch
import glob
import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-AN-25-092-correlations")
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

PATTERNS = [
    "/scratch-cbe/users/alikaan.gueven/ML_KAAN/20260112/sig_17-18_old_centralprod_merged/stop_M1000*/**/*.root",
]

OUT_DIR = Path("/scratch-cbe/users/alikaan.gueven/AN_plots/ParT_hists/AN-25-092_ML_plots3/plots/corr_matrix")
OUT_PNG = OUT_DIR / "AN-25-092_correlations.png"
OUT_CSV = OUT_DIR / "AN-25-092_correlations.csv"


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


def get_branches(available):
    patterns = {
        "ev": ["MET*", "nSDVSec*"],
        "sv": ["vtx_PART_*", "SDVSecVtx*"],
        "id": ["SDVIdxLUT*"],
        "tk": ["SDVTrack*"],
    }
    return {
        key: [name for pattern in pats for name in fnmatch.filter(available, pattern)]
        for key, pats in patterns.items()
    }


def flatten_events(events, branches):
    arrays = {name: events[name] for name in events.fields}

    for tk in branches["tk"]:
        arrays[tk] = deepTable_lazy(
            arrays[tk],
            arrays["SDVIdxLUT_TrackIdx"],
            arrays["SDVIdxLUT_SecVtxIdx"],
            arrays["nSDVSecVtx"],
        )

    template = arrays[branches["sv"][0]]
    broadcasted = {
        name: ak.broadcast_arrays(arrays[name], template)[0]
        for name in branches["ev"]
    }

    ev_sv = ak.zip({**broadcasted, **{name: arrays[name] for name in branches["sv"]}})
    ev_sv_flat = ak.flatten(ev_sv)

    tk_flat = {name: ak.flatten(arrays[name]) for name in branches["tk"]}
    tk_flat = ak.zip(tk_flat)

    flat = ak.zip(
        {field: ev_sv_flat[field] for field in ev_sv_flat.fields}
        | {field: tk_flat[field] for field in tk_flat.fields}
    )
    return ak.flatten(flat)


def corr_stats(df):
    df = df.select_dtypes(include=[np.number])
    columns = list(df.columns)
    values = df.to_numpy(dtype=np.float64, copy=False)
    valid = np.isfinite(values)
    clean = np.where(valid, values, 0.0)
    valid = valid.astype(np.float64)

    return {
        "columns": columns,
        "count": valid.T @ valid,
        "sum": clean.T @ valid,
        "sum2": (clean * clean).T @ valid,
        "cross": clean.T @ clean,
    }


def process_chunk(file_name, start, stop, selected_branches, branches):
    with uproot.open(file_name)["Events"] as tree:
        events = tree.arrays(
            selected_branches,
            library="ak",
            entry_start=start,
            entry_stop=stop,
        )

    flat = flatten_events(events, branches)
    return corr_stats(ak.to_dataframe(flat))


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
    plt.figure(figsize=(24, 24), dpi=200)
    sns.heatmap(
        corr * 100.0,
        annot=True,
        cmap="vlag",
        fmt=".0f",
        annot_kws={"size": 8},
        vmin=-100,
        vmax=100,
    )
    plt.xticks(np.arange(len(corr.columns)) + 0.5, corr.columns, rotation=80)
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
        branches = get_branches(tree.keys())

    selected_branches = branches["ev"] + branches["sv"] + branches["id"] + branches["tk"]
    chunks = build_chunks(files)
    if not chunks:
        raise ValueError("No event chunks were built")

    print(
        f"processing {len(files)} files in {len(chunks)} chunks "
        f"with {N_WORKERS} {DASK_SCHEDULER} workers"
    )
    tasks = [
        delayed(process_chunk)(*chunk, selected_branches, branches)
        for chunk in chunks
    ]

    stats = compute(*tasks, scheduler=DASK_SCHEDULER, num_workers=N_WORKERS)
    corr = combine_stats(stats)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    corr.to_csv(OUT_CSV)
    plot_corr(corr)

    print(f"saved {OUT_CSV}")
    print(f"saved {OUT_PNG}")


if __name__ == "__main__":
    main()
