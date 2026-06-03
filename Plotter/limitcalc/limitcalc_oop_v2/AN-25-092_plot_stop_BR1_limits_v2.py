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

OTHER_ANALYSIS = {
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
        return self.limits[quantile] * STOP_XS_FB


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

    plt.figure(figsize=(7.0, 5.6))
    plt.plot(
        dM,
        [point.xs_limit(0.16) for point in points],
        color="blue",
        linestyle="--",
        linewidth=1,
        label=r"median exp. $-1 \sigma$",
    )
    plt.plot(
        dM,
        [point.xs_limit(0.50) for point in points],
        color="blue",
        linestyle="-",
        linewidth=2,
        marker="o",
        label="median exp.",
    )
    plt.plot(
        dM,
        [point.xs_limit(0.84) for point in points],
        color="blue",
        linestyle="--",
        linewidth=1,
        label=r"median exp. $+1 \sigma$",
    )
    plt.plot(
        OTHER_ANALYSIS["dM"],
        OTHER_ANALYSIS["xs"],
        color="black",
        linewidth=1,
        linestyle="-",
        marker="o",
        label="EXO-24-033 obs., BR=1",
    )

    # plt.xscale("log")
    plt.yscale("log")
    plt.xlabel("$\Delta M$ [GeV]", fontsize=14)
    plt.ylabel(r"95% CL upper limit on cross-section $\sigma$ [fb]", fontsize=14)
    plt.title(r"stop $M = 1000$ GeV, BR = 1")
    plt.grid(True, which="both", linestyle=":")
    plt.tick_params(axis="both", which="both", labelsize=14)
    plt.legend()
    plt.tight_layout()

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"stop_M{STOP_MASS}_BR1_limit.{extension}"
    plt.savefig(output_path)
    plt.close()
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
