#!/usr/bin/env python3

import argparse
import math
import os
import re
import sys
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib-sdv")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd
import ROOT


PLOTTER = Path(__file__).resolve().parents[1]
LIMITCALC_OOP_V2 = PLOTTER / "limitcalc" / "limitcalc_oop_v2"
sys.path.insert(0, str(LIMITCALC_OOP_V2))

from datacards import (  # noqa: E402
    DEFAULT_BASEDIR,
    DEFAULT_C1N2_CTAUS,
    DEFAULT_PLANES,
    DEFAULT_STOP_BRS,
    DEFAULT_YEARS,
    Data,
    DatacardMaker,
    load_samples,
    workdir_from_uniquedir,
)


ROOT.gROOT.SetBatch(True)
plt.rcParams.update({"figure.dpi": 120, "savefig.dpi": 150})


class BackgroundData(Data):
    sample_type = "bkg"
    sample_name = "bkg"

    def path(self, year):
        return self.directory(year) / f"bkg_{year}_hist.root"


def scan_values(start, stop, step, ndigits=None):
    values = np.arange(start, stop + 0.5 * step, step)
    return np.round(values, ndigits) if ndigits is not None else values


def safe_z(value):
    return value if math.isfinite(value) else 0.0


def heatmap(ax, df, title, cbar_label, cmap, vmin=None, vmax=None):
    x = df.index.to_numpy(dtype=float)
    y = df.columns.to_numpy(dtype=float)

    dx = np.diff(x)
    dy = np.diff(y)
    x_edges = np.r_[x[0] - dx[0] / 2, x[:-1] + dx / 2, x[-1] + dx[-1] / 2]
    y_edges = np.r_[y[0] - dy[0] / 2, y[:-1] + dy / 2, y[-1] + dy[-1] / 2]

    pcm = ax.pcolormesh(
        x_edges,
        y_edges,
        np.ma.masked_invalid(df.T.to_numpy(dtype=float)),
        cmap=cmap,
        vmin=vmin,
        vmax=vmax,
        shading="flat",
    )

    x_ticks = x[np.unique(np.round(np.linspace(0, len(x) - 1, 6)).astype(int))]
    y_ticks = y[np.unique(np.round(np.linspace(0, len(y) - 1, 6)).astype(int))]

    ax.set_xticks(x_ticks)
    ax.set_yticks(y_ticks)
    ax.set_xticklabels([f"{v:g}" for v in x_ticks], rotation=45, ha="right")
    ax.yaxis.set_major_formatter(mtick.FormatStrFormatter("%.5f"))
    ax.set_xlabel("MET cut")
    ax.set_ylabel("ML cut")
    ax.set_title(title)

    cbar = ax.figure.colorbar(pcm, ax=ax, shrink=0.85)
    cbar.ax.set_ylabel(cbar_label)


def empty_table(x_edges, y_edges):
    return pd.DataFrame(index=x_edges, columns=y_edges, dtype=float)


def sum_region(yields, years, plane, region):
    values = [yields[year][plane][region] for year in years]
    value = sum(item["yield"] for item in values)
    error = math.sqrt(sum(item["error"] ** 2 for item in values))
    return value, error


def predicted_a(b, b_err, c, c_err, d, d_err):
    if d <= 0:
        return float("nan"), float("nan")

    pred = b * c / d
    rel_unc2 = 0.0
    for value, error in ((b, b_err), (c, c_err), (d, d_err)):
        if value > 0:
            rel_unc2 += (error / value) ** 2
    return pred, abs(pred) * math.sqrt(rel_unc2)


def background_scan(data, x_edges, y_edges, xlo, ylo):
    return {
        (xcut, ycut): data.get_yields(xcut, xlo, ycut, ylo)
        for xcut in x_edges
        for ycut in y_edges
    }


def data_plane_tables(background, years, x_edges, y_edges):
    tables = {}

    for xcut in x_edges:
        for ycut in y_edges:
            yields = background[(xcut, ycut)]

            for plane in DEFAULT_PLANES:
                a, a_err = sum_region(yields, years, plane, "A")
                b, b_err = sum_region(yields, years, plane, "B")
                c, c_err = sum_region(yields, years, plane, "C")
                d, d_err = sum_region(yields, years, plane, "D")
                a_pred, a_pred_err = predicted_a(b, b_err, c, c_err, d, d_err)
                delta_a = a - a_pred
                delta_a_err = math.sqrt(a_err ** 2 + a_pred_err ** 2)

                plane_tables = tables.setdefault(
                    plane,
                    {
                        name: empty_table(x_edges, y_edges)
                        for name in [
                            "bkg_NA",
                            "A_pred",
                            "A_pred_unc",
                            "delta_A",
                            "delta_A_unc",
                            "closure",
                        ]
                    },
                )
                plane_tables["bkg_NA"].loc[xcut, ycut] = a
                plane_tables["A_pred"].loc[xcut, ycut] = a_pred
                plane_tables["A_pred_unc"].loc[xcut, ycut] = a_pred_err
                plane_tables["delta_A"].loc[xcut, ycut] = delta_a
                plane_tables["delta_A_unc"].loc[xcut, ycut] = delta_a_err
                plane_tables["closure"].loc[xcut, ycut] = (
                    (a_pred - a) / a if a > 0 else float("nan")
                )

    return {plane: tables[plane] for plane in DEFAULT_PLANES}


def plot_closure(closure_tables, output_dir):
    variants = {
        "closure": ("", lambda table: table["closure"]),
        "closure_plus1sigma": (
            " +1$\\sigma$",
            lambda table: (
                table["A_pred"] + table["A_pred_unc"] - table["bkg_NA"]
            ) / table["bkg_NA"],
        ),
        "closure_minus1sigma": (
            " -1$\\sigma$",
            lambda table: (
                table["A_pred"] - table["A_pred_unc"] - table["bkg_NA"]
            ) / table["bkg_NA"],
        ),
    }

    for tag, (label, expr) in variants.items():
        fig, axes = plt.subplots(3, 1, figsize=(5, 12), constrained_layout=True)

        for ax, plane in zip(axes, DEFAULT_PLANES):
            heatmap(
                ax,
                expr(closure_tables[plane]),
                title=f"{plane} closure{label}",
                cbar_label=r"$(A_{pred} - A) / A$",
                cmap="RdBu",
                vmin=-1.0,
                vmax=1.0,
            )

        fig.savefig(output_dir / f"multiplane_{tag}.pdf")
        plt.close(fig)


def scan_significance(signal, background, years, x_edges, y_edges, xlo, ylo):
    combined_z = empty_table(x_edges, y_edges)

    for xcut in x_edges:
        for ycut in y_edges:
            data_yields = background[(xcut, ycut)]
            signal_yields = signal.get_yields(xcut, xlo, ycut, ylo)
            z2 = 0.0

            for year in years:
                for plane in DEFAULT_PLANES:
                    b = data_yields[year][plane]["B"]
                    c = data_yields[year][plane]["C"]
                    d = data_yields[year][plane]["D"]
                    bkg, bkg_err = predicted_a(
                        b["yield"],
                        b["error"],
                        c["yield"],
                        c["error"],
                        d["yield"],
                        d["error"],
                    )
                    if not math.isfinite(bkg):
                        continue

                    sig = signal_yields[year][plane]["A"]["yield"]
                    unc = math.sqrt((0.20 * bkg) ** 2 + bkg_err ** 2)
                    eps = 2e-1
                    z = safe_z(ROOT.RooStats.AsimovSignificance(sig, max(eps, bkg), max(eps, unc)))
                    z2 += z ** 2

            combined_z.loc[xcut, ycut] = math.sqrt(z2)

    return combined_z


def plot_significance(target_name, signal, background, years, x_edges, y_edges, xlo, ylo, output_dir):
    combined_z = scan_significance(signal, background, years, x_edges, y_edges, xlo, ylo)
    vmax = np.nanmax(combined_z.to_numpy(dtype=float))

    fig, ax = plt.subplots(figsize=(7.5, 5.5), constrained_layout=True)
    title = (
        f"model: {signal.model}, $M$={signal.M} GeV, "
        f"$\\Delta M$={signal.dM} GeV, $c\\tau$={signal.target_ct:g} mm"
    )
    if signal.model == "stop":
        title += f", BR={signal.target_br:g}"

    heatmap(
        ax,
        combined_z,
        title=title,
        cbar_label=r"Combined Asimov significance",
        cmap="Blues_r",
        vmin=0.0,
        vmax=vmax,
    )

    fig.savefig(output_dir / f"{target_name}_significance.pdf")
    plt.close(fig)

    best_met, best_ml = combined_z.stack().idxmax()
    best_z = combined_z.loc[best_met, best_ml]
    print(f"{target_name}: best Z={best_z:.3f}, MET={best_met:g}, ML={best_ml:.5f}")
    return {
        "target": target_name,
        "source": signal.sample_name,
        "best_z": best_z,
        "best_met": best_met,
        "best_ml": best_ml,
    }


def selected_targets(args, signals, data):
    maker = DatacardMaker(
        signals,
        data,
        Path("/tmp/unused_abcd_scan_v2"),
        args.x_min,
        args.xlo,
        args.y_min,
        args.ylo,
        args.mode,
        args.stop_br,
        args.c1n2_ctau,
    )

    targets = []
    selected = set(args.target or [])
    for signal, target_ct, target_br, datacard_name in maker.targets():
        if selected and not target_selected(selected, signal, target_br, datacard_name):
            continue
        targets.append((signal, target_ct, target_br, datacard_name))
    if selected and not targets:
        print("No target matched. Available matching examples:")
        for _, _, _, datacard_name in list(maker.targets())[:20]:
            print(f"  {datacard_name}")
    return targets


def target_selected(selected, signal, target_br, datacard_name):
    if datacard_name in selected or signal.sample_name in selected:
        return True

    for target in selected:
        match = re.match(
            r"stop_M(?P<mass>\d+)_(?P<daughter>\d+)_ct[0-9]+(?:p[0-9]+)?_BR(?P<br>[0-9]+(?:p[0-9]+)?)$",
            target,
        )
        if not match:
            continue
        br = float(match.group("br").replace("p", "."))
        if (
            signal.model == "stop"
            and signal.M == int(match.group("mass"))
            and signal.M2 == int(match.group("daughter"))
            and math.isclose(target_br, br)
        ):
            return True

    return False


def parse_args():
    parser = argparse.ArgumentParser(
        description="Scan ABCD cuts using the limitcalc_oop_v2 sample and reweighting machinery."
    )
    parser.add_argument(
        "--uniquedir",
        required=True,
        help=(
            f"Directory name below {DEFAULT_BASEDIR}. "
            "Absolute paths are also accepted."
        ),
    )
    parser.add_argument("--mode", choices=["Asimov", "observation"], default="Asimov")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument(
        "--background-source",
        choices=["data", "bkg"],
        default="data",
        help="Use data_*_hist.root or bkg_*_hist.root for ABCD background yields.",
    )
    parser.add_argument("--years", nargs="+", default=DEFAULT_YEARS)
    parser.add_argument("--xlo", type=float, default=250.0)
    parser.add_argument("--ylo", type=float, default=0.80)
    parser.add_argument("--x-min", type=float, default=300.0)
    parser.add_argument("--x-max", type=float, default=700.0)
    parser.add_argument("--x-step", type=float, default=50.0)
    parser.add_argument("--y-min", type=float, default=0.9900)
    parser.add_argument("--y-max", type=float, default=0.9998)
    parser.add_argument("--y-step", type=float, default=0.0002)
    parser.add_argument("--target", nargs="+", help="Optional datacard target names to scan.")
    parser.add_argument("--stop-br", nargs="+", type=float, default=DEFAULT_STOP_BRS)
    parser.add_argument("--c1n2-ctau", nargs="+", type=float, default=DEFAULT_C1N2_CTAUS)
    parser.add_argument("--skip-closure", action="store_true")
    parser.add_argument("--skip-significance", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    workdir = workdir_from_uniquedir(args.uniquedir)
    output_dir = args.output_dir or PLOTTER / "ABCD_optimisation" / "plots_v2"
    output_dir.mkdir(parents=True, exist_ok=True)

    x_edges = scan_values(args.x_min, args.x_max, args.x_step)
    y_edges = scan_values(args.y_min, args.y_max, args.y_step, ndigits=5)
    signals, data = load_samples(workdir, DEFAULT_YEARS)
    background_data = BackgroundData(workdir, DEFAULT_YEARS) if args.background_source == "bkg" else data

    print(f"WORKDIR: {workdir}")
    print(f"output-dir: {output_dir}")
    print(f"background-source: {args.background_source}")
    print(f"years: {' '.join(args.years)}")
    print(f"x cuts: {len(x_edges)}, y cuts: {len(y_edges)}")

    background = None
    if not (args.skip_closure and args.skip_significance):
        background = background_scan(background_data, x_edges, y_edges, args.xlo, args.ylo)

    if not args.skip_closure:
        closure_tables = data_plane_tables(background, args.years, x_edges, y_edges)
        plot_closure(closure_tables, output_dir)

    rows = []
    if not args.skip_significance:
        targets = selected_targets(args, signals, background_data)
        print(f"targets: {len(targets)}")
        for signal, target_ct, target_br, datacard_name in targets:
            signal.reweight_to(target_ct, target_br)
            signal.datacard_name = datacard_name
            rows.append(
                plot_significance(
                    datacard_name,
                    signal,
                    background,
                    args.years,
                    x_edges,
                    y_edges,
                    args.xlo,
                    args.ylo,
                    output_dir,
                )
            )

    if rows:
        pd.DataFrame(rows).to_csv(output_dir / "significance_best_points.csv", index=False)


if __name__ == "__main__":
    main()
