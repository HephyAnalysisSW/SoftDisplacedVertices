#!/usr/bin/env python3

import argparse
import csv
import re
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import ROOT

warnings.filterwarnings(
    "ignore",
    message="The value of the smallest subnormal for.*type is zero.",
    category=UserWarning,
)


DEFAULT_BASEDIR = Path("/scratch-cbe/users/alikaan.gueven/AN_plots/ParT_hists")
DEFAULT_LIMIT_DIR = (
    DEFAULT_BASEDIR
    / "AN-25-092_ML_plots_limitcalc_privateprod_260528"
    / "limits"
    / "reweighted_v2"
    / "Asimov"
)
SCRIPT_DIR = Path(__file__).resolve().parent
SAMPLES_PATH = SCRIPT_DIR.parents[2] / "Samples/python/Samples.py"
EXO_DIR = SCRIPT_DIR / "EXO-24-033"

QUANTILES = [0.025, 0.16, 0.50, 0.84, 0.975]
XS_FB_PER_PB = 1000.0


def load_theory_xsecs():
    xsecs = {}
    sample_pattern = re.compile(
        r"""Sample\(\s*["']([^"']+)["']\s*,\s*(?:xsec\s*=\s*)?([0-9.eE+-]+)"""
    )

    for name, xsec_pb in sample_pattern.findall(SAMPLES_PATH.read_text()):
        model = name.split("_M", 1)[0] if "_M" in name else None
        mass_match = re.search(r"_M(\d+)_", name) if model in {"C1N2", "stop"} else None
        if not mass_match:
            continue

        xsecs.setdefault((model, int(mass_match.group(1))), float(xsec_pb))

    return xsecs


def read_limit_points(limit_dir, theory_xsecs):
    curves = {}

    for path in sorted(limit_dir.glob("*/limits.root")):
        name = path.parent.name
        match = re.fullmatch(
            r"(C1N2|stop)_M(\d+)_(\d+)_ct([0-9]+(?:p[0-9]+)?)(?:_BR([0-9]+(?:p[0-9]+)?))?",
            name,
        )

        model = match.group(1)
        mass = int(match.group(2))
        daughter_mass = int(match.group(3))
        dM = mass - daughter_mass
        ct = float(match.group(4).replace("p", "."))
        br = float(match.group(5).replace("p", ".")) if match.group(5) else None
        key = (model, mass, br) if model == "stop" else (model, mass, dM)

        limits = {}
        observed = None
        root_file = ROOT.TFile.Open(str(path))
        tree = root_file.Get("limit")

        for entry in range(tree.GetEntries()):
            tree.GetEntry(entry)
            quantile = float(tree.quantileExpected)
            value = float(tree.limit)
            if quantile < 0:
                observed = value
            else:
                matched = min(QUANTILES, key=lambda q: abs(q - quantile))
                limits[matched] = value

        root_file.Close()

        point = {
            "name": name,
            "model": model,
            "mass": mass,
            "daughter_mass": daughter_mass,
            "dM": dM,
            "ct": ct,
            "br": br,
            "limits": limits,
            "observed": observed,
            "theory_xs_fb": theory_xsecs[(model, mass)] * XS_FB_PER_PB,
        }
        curves.setdefault(key, []).append(point)

    return curves


def main():
    parser = argparse.ArgumentParser(description="Plot reweighted AN-25-092 limits.")
    parser.add_argument("--limit-dir", type=Path, default=DEFAULT_LIMIT_DIR)
    parser.add_argument(
        "--uniquedir",
        help=f"Directory name below {DEFAULT_BASEDIR}. Absolute paths are accepted.",
    )
    parser.add_argument("--mode", choices=["Asimov", "observation"], default="Asimov")
    parser.add_argument("--limit-dir-name", default="reweighted_v2")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--extension", default="pdf")
    parser.add_argument("--model", choices=["all", "C1N2", "stop"], default="all")
    parser.add_argument("--observed", action="store_true")
    args = parser.parse_args()

    if args.uniquedir:
        workdir = Path(args.uniquedir).expanduser()
        if not workdir.is_absolute():
            workdir = DEFAULT_BASEDIR / workdir
        limit_dir = workdir / "limits" / args.limit_dir_name / args.mode
    else:
        limit_dir = args.limit_dir.expanduser()

    output_dir = args.output_dir
    if output_dir is None:
        output_dir = limit_dir.parents[2] / "limitplots" / limit_dir.parent.name / limit_dir.name

    theory_xsecs = load_theory_xsecs()
    curves = read_limit_points(limit_dir, theory_xsecs)
    exo_points = {}

    for path in sorted(EXO_DIR.glob("*.csv")):
        name = path.stem
        c1n2_match = re.fullmatch(r"EXO-24-033_C1N2_dM_(\d+)", name)
        stop_match = re.fullmatch(r"EXO-24-033_stop_BR([0-9]+(?:p[0-9]+)?)", name)
        model = "C1N2" if c1n2_match else "stop"
        exo_dM = int(c1n2_match.group(1)) if c1n2_match else None
        exo_br = float(stop_match.group(1).replace("p", ".")) if stop_match else None

        with path.open() as handle:
            rows = csv.DictReader(line for line in handle if not line.startswith("#"))
            for row in rows:
                mass = int(float(row["$m$ [GeV]"]))
                xs_limit_fb = float(row["Observed 95% CL upper limit on $\\sigma B$ [fb]"])
                r_limit = xs_limit_fb / (theory_xsecs[(model, mass)] * XS_FB_PER_PB)

                if model == "stop":
                    key = (model, mass, exo_br)
                    x_value = float(row["$\\Delta m$ [GeV]"])
                else:
                    key = (model, mass, exo_dM)
                    x_value = float(row["$c\\tau$ [mm]"])

                exo_points.setdefault(key, []).append((x_value, r_limit))

    print(f"limit-dir: {limit_dir}")
    print(f"output-dir: {output_dir}")
    print(f"samples: {SAMPLES_PATH}")

    output_dir.mkdir(parents=True, exist_ok=True)

    selected = [
        (key, points)
        for key, points in sorted(curves.items())
        if args.model == "all" or key[0] == args.model
    ]
    print(f"curves: {len(selected)}")

    for key, points in selected:
        model, mass, curve_value = key
        points = sorted(points, key=lambda point: point["dM"] if model == "stop" else point["ct"])
        x = [point["dM"] if model == "stop" else point["ct"] for point in points]

        fig, ax = plt.subplots(figsize=(8.0, 6.8))
        fig.subplots_adjust(top=0.90)

        ax.fill_between(
            x,
            [point["limits"][0.025] for point in points],
            [point["limits"][0.975] for point in points],
            color="#feff00",
            label=r"Expected $\pm 2\sigma$",
        )
        ax.fill_between(
            x,
            [point["limits"][0.16] for point in points],
            [point["limits"][0.84] for point in points],
            color="#2df700",
            label=r"Expected $\pm 1\sigma$",
        )
        ax.plot(
            x,
            [point["limits"][0.50] for point in points],
            color="black",
            linestyle="-",
            marker="o",
            linewidth=1.8,
            label="Expected median",
        )

        if args.observed:
            observed_points = [point for point in points if point["observed"] is not None]
            ax.plot(
                [point["dM"] if model == "stop" else point["ct"] for point in observed_points],
                [point["observed"] for point in observed_points],
                color="black",
                marker="s",
                linestyle="--",
                linewidth=1.5,
                label="Observed",
            )

        if key in exo_points:
            exo_x, exo_y = zip(*sorted(exo_points[key]))
            ax.plot(
                exo_x,
                exo_y,
                color="tab:blue",
                linewidth=1.8,
                linestyle="-",
                marker="*",
                markersize=12,
                label="EXO-24-033 observed\n(100$\\mathrm{fb}^{-1}$)",
            )

        ax.axhline(1.0, color="black", linestyle="--", linewidth=1.4)
        if model == "C1N2":
            ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel(r"$\Delta M$ [GeV]" if model == "stop" else r"$c\tau$ [mm]", fontsize=14, loc="right")
        ax.set_ylabel(r"95% CL upper limit on signal strength $r$", fontsize=14, loc="center")
        ax.grid(True, which="both", linestyle=":", linewidth=0.3)
        ax.tick_params(axis="both", which="both", labelsize=12)

        y_min, y_max = ax.get_ylim()
        ax.set_ylim(y_min, y_max * 5.0)

        if model == "stop":
            annotation = "model: stop\n" rf"$M$ = {mass} GeV" "\n" rf"BR = {curve_value:g}"
            output_name = f"stop_M{mass}_BR{curve_value:g}".replace(".", "p")
        else:
            annotation = "model: C1N2\n" rf"$M$ = {mass} GeV" "\n" rf"$\Delta M$ = {curve_value:g} GeV"
            output_name = f"C1N2_M{mass}_dM{curve_value:g}"

        ax.text(0.03, 0.97, annotation, transform=ax.transAxes, ha="left", va="top", fontsize=13)
        ax.legend(loc="upper right", frameon=False, fontsize=12)
        ax.text(
            0.00,
            1.00,
            "CMS",
            transform=ax.transAxes,
            ha="left",
            va="bottom",
            fontsize=22,
            fontweight="bold",
            clip_on=False,
        )
        ax.text(
            0.135,
            1.005,
            "Private work",
            transform=ax.transAxes,
            ha="left",
            va="bottom",
            fontsize=17,
            fontstyle="italic",
            clip_on=False,
        )
        ax.text(
            1.000,
            1.005,
            r"$273 \mathrm{fb}^{-1}$, (2017-2024)",
            transform=ax.transAxes,
            ha="right",
            va="bottom",
            fontsize=14,
            clip_on=False,
        )

        output_path = output_dir / f"{output_name}_rw_limit.{args.extension}"
        fig.savefig(output_path, bbox_inches="tight")
        plt.close(fig)

        medians = [point["limits"][0.50] for point in points]
        print(
            f"Saved: {output_path} "
            f"(theory_xs={points[0]['theory_xs_fb']:.6g} fb, median_r={medians})"
        )


if __name__ == "__main__":
    main()
