import argparse
import fnmatch
import glob
import os
import resource
import time
from contextlib import contextmanager

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-profile-dask")

import dask
from dask.distributed import Client, LocalCluster
import awkward as ak
import uproot
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


DEFAULT_PATTERNS = [
    "/scratch-cbe/users/alikaan.gueven/ML_KAAN/20260112/sig_17-18_old_centralprod_merged/stop_M1000*/**/*.root",
]


TIMINGS = []


def rss_mb():
    usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return usage / 1024.0


@contextmanager
def timed(label):
    start = time.perf_counter()
    start_rss = rss_mb()
    print(f"[START] {label}", flush=True)
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        end_rss = rss_mb()
        TIMINGS.append((label, elapsed, end_rss))
        print(
            f"[DONE ] {label}: {elapsed:.3f} s, max RSS {end_rss:.1f} MB "
            f"(delta {end_rss - start_rss:+.1f} MB)",
            flush=True,
        )


try:
    from numba import njit

    HAS_NUMBA = True
except ImportError:
    HAS_NUMBA = False
    njit = None


if HAS_NUMBA:

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


def deepTable_numba(partition, trIdx, svIdx, n_sv):
    builder = ak.ArrayBuilder()
    deepTable(partition, trIdx, svIdx, n_sv, builder)
    return builder.snapshot()


def deepTable_python(partition, trIdx, svIdx, n_sv):
    out = []
    for ev in range(len(n_sv)):
        event_out = []
        for sv in range(int(n_sv[ev])):
            sv_out = []
            for i2, col in enumerate(svIdx[ev]):
                if int(col) == sv:
                    sv_out.append(partition[ev][int(trIdx[ev][i2])])
            event_out.append(sv_out)
        out.append(event_out)
    return ak.Array(out)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pattern", action="append", default=None)
    parser.add_argument("--max-files", type=int, default=0)
    parser.add_argument("--max-events", type=int, default=0)
    parser.add_argument("--max-tk-branches", type=int, default=0)
    parser.add_argument("--n-workers", type=int, default=16)
    parser.add_argument("--threads-per-worker", type=int, default=1)
    parser.add_argument(
        "--processes",
        action="store_true",
        help="Use process-based Dask workers. The default uses threaded workers.",
    )
    parser.add_argument(
        "--no-client",
        action="store_true",
        help="Do not start dask.distributed; use the local threaded scheduler.",
    )
    parser.add_argument("--skip-corr", action="store_true")
    parser.add_argument("--skip-plot", action="store_true")
    parser.add_argument(
        "--chunked-corr",
        action="store_true",
        help=(
            "Process file/event chunks as Dask tasks and combine correlation "
            "statistics, instead of materialising one full Awkward array first."
        ),
    )
    parser.add_argument("--chunk-size", type=int, default=50000)
    parser.add_argument("--max-chunks", type=int, default=0)
    parser.add_argument(
        "--output",
        default="/tmp/profile_dask_deeptable_corr_heatmap.png",
    )
    return parser.parse_args()


def branch_list(available_branches):
    ev_branches = ["MET*", "nSDVSec*"]
    sv_branches = ["vtx_PART_338_epoch_*", "SDVSecVtx*"]
    id_branches = ["SDVIdxLUT*"]
    tk_branches = ["SDVTrack*"]

    branches = {"ev": [], "sv": [], "id": [], "tk": []}
    for pattern in ev_branches:
        branches["ev"].extend(fnmatch.filter(available_branches, pattern))
    for pattern in sv_branches:
        branches["sv"].extend(fnmatch.filter(available_branches, pattern))
    for pattern in id_branches:
        branches["id"].extend(fnmatch.filter(available_branches, pattern))
    for pattern in tk_branches:
        branches["tk"].extend(fnmatch.filter(available_branches, pattern))
    return branches


def flatten_for_corr(events, branches, deep_table_impl):
    arrays = {name: events[name] for name in events.fields}
    for tk in branches["tk"]:
        arrays[tk] = deep_table_impl(
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
    ev_sv_df = ak.zip({**broadcasted, **{k: arrays[k] for k in branches["sv"]}})
    ev_sv_flat_df = ak.flatten(ev_sv_df)

    tk_semi_flat = {name: ak.flatten(arrays[name]) for name in branches["tk"]}
    tk_semi_flat_df = ak.zip(tk_semi_flat)

    zipped = ak.zip(
        {field: ev_sv_flat_df[field] for field in ev_sv_flat_df.fields}
        | {field: tk_semi_flat_df[field] for field in tk_semi_flat_df.fields}
    )
    return ak.flatten(zipped)


def dataframe_pair_stats(df):
    df = df.select_dtypes(include=[np.number])
    columns = list(df.columns)
    values = df.to_numpy(dtype=np.float64, copy=False)
    valid = np.isfinite(values)
    clean = np.where(valid, values, 0.0)
    valid_float = valid.astype(np.float64)
    count = valid_float.T @ valid_float
    sum_x = clean.T @ valid_float
    sum_x2 = (clean * clean).T @ valid_float
    cross = clean.T @ clean
    return {
        "columns": columns,
        "count": count,
        "sum_x": sum_x,
        "sum_x2": sum_x2,
        "cross": cross,
        "rows": len(df),
    }


def combine_pair_stats(partials):
    if not partials:
        raise RuntimeError("No chunk statistics were produced.")

    columns = partials[0]["columns"]
    totals = {
        "count": np.zeros_like(partials[0]["count"], dtype=np.float64),
        "sum_x": np.zeros_like(partials[0]["sum_x"], dtype=np.float64),
        "sum_x2": np.zeros_like(partials[0]["sum_x2"], dtype=np.float64),
        "cross": np.zeros_like(partials[0]["cross"], dtype=np.float64),
    }
    rows = 0
    for partial in partials:
        if partial["columns"] != columns:
            raise RuntimeError("Column order changed between chunks.")
        for key in totals:
            totals[key] += partial[key]
        rows += partial["rows"]

    count = totals["count"]
    sum_x = totals["sum_x"]
    sum_y = sum_x.T
    sum_x2 = totals["sum_x2"]
    cross = totals["cross"]
    denom = count - 1.0

    with np.errstate(invalid="ignore", divide="ignore"):
        cov = (cross - (sum_x * sum_y / count)) / denom
        var_x = (sum_x2 - (sum_x * sum_x / count)) / denom
        var_y = var_x.T
        corr = cov / np.sqrt(var_x * var_y)

    corr[(count < 2) | (var_x <= 0.0) | (var_y <= 0.0)] = np.nan
    np.fill_diagonal(corr, 1.0)
    return pd.DataFrame(corr, index=columns, columns=columns), rows


def process_corr_chunk(file_name, entry_start, entry_stop, selected_branches, branches):
    deep_table_impl = deepTable_numba if HAS_NUMBA else deepTable_python
    timings = {}

    start = time.perf_counter()
    with uproot.open(file_name)["Events"] as tree:
        events = tree.arrays(
            selected_branches,
            library="ak",
            entry_start=entry_start,
            entry_stop=entry_stop,
        )
    timings["read"] = time.perf_counter() - start

    start = time.perf_counter()
    flat = flatten_for_corr(events, branches, deep_table_impl)
    timings["flatten"] = time.perf_counter() - start

    start = time.perf_counter()
    df = ak.to_dataframe(flat)
    timings["to_dataframe"] = time.perf_counter() - start

    start = time.perf_counter()
    stats = dataframe_pair_stats(df)
    timings["pair_stats"] = time.perf_counter() - start
    stats["timings"] = timings
    stats["source"] = f"{file_name}:{entry_start}-{entry_stop}"
    return stats


def run_chunked_corr(args, files, selected_branches, branches):
    from dask import compute, delayed

    with timed("build chunk tasks"):
        chunks = []
        remaining_events = args.max_events if args.max_events > 0 else None
        for file_name in files:
            with uproot.open(file_name)["Events"] as tree:
                entries = tree.num_entries
            if remaining_events is not None:
                entries = min(entries, remaining_events)
            for start in range(0, entries, args.chunk_size):
                stop = min(start + args.chunk_size, entries)
                chunks.append((file_name, start, stop))
                if args.max_chunks > 0 and len(chunks) >= args.max_chunks:
                    break
            if remaining_events is not None:
                remaining_events -= entries
                if remaining_events <= 0:
                    break
            if args.max_chunks > 0 and len(chunks) >= args.max_chunks:
                break
        print(f"chunks: {len(chunks)}", flush=True)
        if chunks:
            print(f"first chunk: {chunks[0]}", flush=True)

    partials = []
    chunks_for_dask = chunks
    if HAS_NUMBA and chunks:
        with timed("warm up Numba on first chunk"):
            file_name, start, stop = chunks[0]
            partials.append(
                process_corr_chunk(
                    file_name, start, stop, selected_branches, branches
                )
            )
        chunks_for_dask = chunks[1:]

    with timed("compute chunked correlation statistics"):
        tasks = [
            delayed(process_corr_chunk)(
                file_name, start, stop, selected_branches, branches
            )
            for file_name, start, stop in chunks_for_dask
        ]
        if tasks:
            partials.extend(compute(*tasks))

    with timed("combine correlation statistics"):
        corr, rows = combine_pair_stats(partials)
        print(f"flattened rows: {rows}", flush=True)
        print(f"corr shape: {corr.shape}", flush=True)

    if not args.skip_plot:
        import seaborn as sns

        with timed("plot heatmap"):
            corr_res_scaled = corr * 100
            plt.figure(figsize=(24, 24), dpi=200)
            sns.heatmap(
                corr_res_scaled,
                annot=True,
                cmap="vlag",
                fmt=".0f",
                annot_kws={"size": 8},
                vmin=-100,
                vmax=100,
            )
            plt.xticks(
                range(len(corr_res_scaled)),
                corr_res_scaled.columns,
                rotation=80,
            )
            plt.tight_layout()
            plt.savefig(args.output)
            print(f"saved: {args.output}", flush=True)

    timing_totals = {}
    for partial in partials:
        for key, value in partial["timings"].items():
            timing_totals[key] = timing_totals.get(key, 0.0) + value
    print("Chunk worker CPU-time totals:", flush=True)
    for key, value in sorted(timing_totals.items(), key=lambda item: item[1], reverse=True):
        print(f"{value:10.3f} s  {key}", flush=True)


def main():
    args = parse_args()
    patterns = args.pattern or DEFAULT_PATTERNS

    print(f"numba available: {HAS_NUMBA}", flush=True)
    if not HAS_NUMBA:
        print(
            "WARNING: numba is not installed in this environment; "
            "using a pure-Python deepTable fallback.",
            flush=True,
        )

    client = None
    cluster = None
    if args.no_client:
        with timed("configure local threaded Dask scheduler"):
            dask.config.set(scheduler="threads", num_workers=args.n_workers)
            print(f"using local threaded scheduler with {args.n_workers} workers", flush=True)
    else:
        with timed("start LocalCluster"):
            cluster = LocalCluster(
                n_workers=args.n_workers,
                threads_per_worker=args.threads_per_worker,
                processes=args.processes,
                dashboard_address=None,
                local_directory="/tmp/dask-profile-local",
            )
            client = Client(cluster)
            print(client, flush=True)

    with timed("glob ROOT files"):
        files = [f for pat in patterns for f in glob.glob(pat, recursive=True)]
        files = sorted(files)
        if args.max_files > 0:
            files = files[: args.max_files]
        if not files:
            raise RuntimeError("No ROOT files matched any pattern.")
        files_as_dict = {f: "Events" for f in files}
        print(f"files: {len(files)}", flush=True)
        print(f"sample: {files[0]}", flush=True)

    with timed("resolve branches from sample file"):
        sample_file = next(iter(files_as_dict))
        with uproot.open(sample_file)["Events"] as tree:
            available_branches = tree.keys()
        branches = branch_list(available_branches)
        for key in branches:
            print(f"{key}: {len(branches[key])}", flush=True)
            print(branches[key], flush=True)

    selected_branches = (
        branches["ev"] + branches["sv"] + branches["id"] + branches["tk"]
    )
    if args.max_tk_branches > 0:
        branches["tk"] = branches["tk"][: args.max_tk_branches]
        selected_branches = (
            branches["ev"] + branches["sv"] + branches["id"] + branches["tk"]
        )
        print(f"limited tk branches: {branches['tk']}", flush=True)

    if args.chunked_corr:
        run_chunked_corr(args, files, selected_branches, branches)
        print("\nTiming summary, slowest first:", flush=True)
        for label, elapsed, mem in sorted(
            TIMINGS, key=lambda item: item[1], reverse=True
        ):
            print(f"{elapsed:10.3f} s  {mem:10.1f} MB  {label}", flush=True)
        if client is not None:
            client.close()
        if cluster is not None:
            cluster.close()
        return

    with timed("build uproot.dask graph"):
        lazy = uproot.dask(
            files_as_dict,
            filter_name=selected_branches,
            library="ak",
            open_files=False,
        )
        print(f"dask collection fields: {lazy.fields}", flush=True)

    if args.max_events > 0:
        with timed("apply pre-compute event slice"):
            lazy = lazy[: args.max_events]

    with timed("lazy.compute"):
        lazy = lazy.compute()
        print(f"events after compute: {len(lazy)}", flush=True)

    with timed("ak.copy"):
        lazy_copy = ak.copy(lazy)

    deep_table_impl = deepTable_numba if HAS_NUMBA else deepTable_python
    for tk in branches["tk"]:
        with timed(f"deepTable {tk}"):
            lazy_copy[tk] = deep_table_impl(
                lazy_copy[tk],
                lazy_copy["SDVIdxLUT_TrackIdx"],
                lazy_copy["SDVIdxLUT_SecVtxIdx"],
                lazy_copy["nSDVSecVtx"],
            )

    with timed("broadcast event branches to sv template"):
        template = lazy_copy[branches["sv"][0]]
        broadcasted = {
            name: ak.broadcast_arrays(lazy_copy[name], template)[0]
            for name in branches["ev"]
        }

    with timed("zip and flatten event+sv table"):
        ev_sv_df = ak.zip(
            {**broadcasted, **{k: lazy_copy[k] for k in branches["sv"]}}
        )
        ev_sv_flat_df = ak.flatten(ev_sv_df)
        print(f"event-sv rows: {len(ev_sv_flat_df)}", flush=True)

    with timed("flatten track branches and zip"):
        tk_semi_flat = {
            name: ak.flatten(lazy_copy[name]) for name in branches["tk"]
        }
        tk_semi_flat_df = ak.zip(tk_semi_flat)

    with timed("zip sv and track tables"):
        zipped = ak.zip(
            {field: ev_sv_flat_df[field] for field in ev_sv_flat_df.fields}
            | {field: tk_semi_flat_df[field] for field in tk_semi_flat_df.fields}
        )

    with timed("flatten final track table"):
        zipped_flat = ak.flatten(zipped)
        print(f"final flattened rows: {len(zipped_flat)}", flush=True)

    if args.skip_corr:
        print("Skipping dataframe/correlation stages.", flush=True)
    else:
        with timed("ak.to_dataframe"):
            ddf = ak.to_dataframe(zipped_flat)
            print(f"dataframe shape: {ddf.shape}", flush=True)

        with timed("dataframe corr"):
            corr = ddf.corr()
            print(f"corr shape: {corr.shape}", flush=True)

        if not args.skip_plot:
            import seaborn as sns

            with timed("plot heatmap"):
                corr_res_scaled = corr * 100
                plt.figure(figsize=(24, 24), dpi=200)
                sns.heatmap(
                    corr_res_scaled,
                    annot=True,
                    cmap="vlag",
                    fmt=".0f",
                    annot_kws={"size": 8},
                    vmin=-100,
                    vmax=100,
                )
                plt.xticks(
                    range(len(corr_res_scaled)),
                    corr_res_scaled.columns,
                    rotation=80,
                )
                plt.tight_layout()
                plt.savefig(args.output)
                print(f"saved: {args.output}", flush=True)

    print("\nTiming summary, slowest first:", flush=True)
    for label, elapsed, mem in sorted(TIMINGS, key=lambda item: item[1], reverse=True):
        print(f"{elapsed:10.3f} s  {mem:10.1f} MB  {label}", flush=True)

    if client is not None:
        client.close()
    if cluster is not None:
        cluster.close()


if __name__ == "__main__":
    main()
