#!/usr/bin/env python3

import argparse
import re
import warnings
from pathlib import Path

warnings.filterwarnings(
    "ignore",
    message="The value of the smallest subnormal for.*type is zero.",
    category=UserWarning,
)


DEFAULT_BASEDIR = Path("/scratch-cbe/users/alikaan.gueven/AN_plots/ParT_hists")
STOP_XS_FB = 7.395
STOP_MASS = 1000
STOP_DAUGHTER_MASSES = [975, 980, 985, 988]
QUANTILES = [0.025, 0.16, 0.50, 0.84, 0.975]

EXO_24_033 = {
    "dM": [25, 20, 15, 12],
    "ct": [0.2, 2, 20, 200],
    "xs": [8.499, 3.9022, 5.4943, 27.865],
}


def workdir_from_uniquedir(uniquedir):
    workdir = Path(uniquedir).expanduser()
    return workdir if workdir.is_absolute() else DEFAULT_BASEDIR / workdir


def number_from_label(label):
    value = float(label.replace("p", "."))
    return int(value) if value.is_integer() else value


class StopLimitPoint:
    def __init__(self, path):
        self.path = Path(path)
        self.name = self.path.parent.name
        self.parse_name()
        self.read_limits()

    def parse_name(self):
        match = re.match(r"stop_M(\d+)_(\d+)_ct([0-9]+(?:p[0-9]+)?)_BR1$", self.name)
        self.M = int(match.group(1))
        self.M2 = int(match.group(2))
        self.dM = self.M - self.M2
        self.ct = number_from_label(match.group(3))

    def read_limits(self):
        import ROOT

        self.limits = {}
        root_file = ROOT.TFile.Open(str(self.path))
        tree = root_file.Get("limit")

        for entry in range(tree.GetEntries()):
            tree.GetEntry(entry)
            quantile = float(tree.quantileExpected)
            if quantile > 0:
                matched = min(QUANTILES, key=lambda q: abs(q - quantile))
                self.limits[matched] = float(tree.limit)

        root_file.Close()

    def xs_limit(self, quantile):
        return self.limits[quantile]#  * STOP_XS_FB


def read_points(limit_dir):
    points = []
    for daughter_mass in STOP_DAUGHTER_MASSES:
        paths = sorted(limit_dir.glob(f"stop_M{STOP_MASS}_{daughter_mass}_ct*_BR1/limits.root"))
        point = StopLimitPoint(paths[0])
        points.append(point)
    return sorted(points, key=lambda point: point.dM)


def plot(points, output_dir, extension):
    import matplotlib.pyplot as plt

    dM = [point.dM for point in points]
    y2lo = [point.xs_limit(0.025) for point in points]
    y1lo = [point.xs_limit(0.16) for point in points]
    ymed = [point.xs_limit(0.50) for point in points]
    y1hi = [point.xs_limit(0.84) for point in points]
    y2hi = [point.xs_limit(0.975) for point in points]

    fig, ax = plt.subplots(figsize=(8.0, 6.8))
    fig.subplots_adjust(top=0.90)

    ax.fill_between(
        dM,
        y2lo,
        y2hi,
        color="#feff00",
        label=r"Expected $\pm 2\sigma$",
    )
    ax.fill_between(
        dM,
        y1lo,
        y1hi,
        color="#2df700",
        label=r"Expected $\pm 1\sigma$",
    )
    ax.plot(
        dM,
        ymed,
        color="black",
        linestyle="-",
        marker="o",
        linewidth=1.8,
        label="Expected median",
    )
    ax.plot(
        EXO_24_033["dM"],
        [xs/STOP_XS_FB for xs in EXO_24_033["xs"]],
        color="tab:blue",
        linewidth=1.8,
        linestyle="-",
        marker="*",
        markersize=12,
        label="EXO-24-033 observed\n(100$\mathrm{fb}^{-1}$)",
    )

    ax.axhline(1.0, color="black", linestyle="--", linewidth=1.4)

    ax.set_yscale("log")
    ax.set_xlabel(r"$\Delta M$ [GeV]", fontsize=14, loc="right")
    ax.set_ylabel(r"95% CL upper limit on signal strength $r$", fontsize=14, loc="center")
    ax.grid(True, which="both", linestyle=":", linewidth=0.3)
    ax.tick_params(axis="both", which="both", labelsize=12)

    y_min, y_max = ax.get_ylim()
    ax.set_ylim(y_min, y_max * 5.0)
    ax.text(
        0.03,
        0.97,
        "model: stop\n"
        rf"$M$ = {STOP_MASS} GeV" "\n"
        "BR = 1.0",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=13,
    )
    cms_font = []
    ax.legend(loc="upper right", frameon=False, fontsize=12)
    ax.text(
        0.00,
        1.00,
        "CMS",
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=22,
        fontfamily=cms_font,
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
        fontfamily=cms_font,
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
        fontfamily=cms_font,
        clip_on=False,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"stop_M{STOP_MASS}_BR1_limit_v3.{extension}"
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)
    return output_path


def parse_args():
    parser = argparse.ArgumentParser(description="Plot the stop M1000 BR=1 comparison limit.")
    parser.add_argument(
        "--uniquedir",
        required=True,
        help=(
            f"Directory name below {DEFAULT_BASEDIR}. "
            "Absolute paths are also accepted."
        ),
    )
    parser.add_argument("--mode", choices=["Asimov", "observation"], default="Asimov")
    parser.add_argument("--limit-dir-name", default="reweighted_v2")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--extension", default="pdf")
    return parser.parse_args()


def main():
    args = parse_args()
    workdir = workdir_from_uniquedir(args.uniquedir)
    limit_dir = workdir / "limits" / args.limit_dir_name / args.mode
    output_dir = args.output_dir or workdir / "limitplots" / args.limit_dir_name / args.mode

    points = read_points(limit_dir)
    output_path = plot(points, output_dir, args.extension)

    print(f"limit-dir: {limit_dir}")
    for point in points:
        print(
            f"point: {point.name} "
            f"dM={point.dM:g} ct={point.ct:g} "
            f"median_xs={point.xs_limit(0.50):.6g} fb"
        )
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()
