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
QUANTILES = [0.025, 0.16, 0.50, 0.84, 0.975]


def workdir_from_uniquedir(uniquedir):
    workdir = Path(uniquedir).expanduser()
    return workdir if workdir.is_absolute() else DEFAULT_BASEDIR / workdir


def number_from_label(label):
    value = float(label.replace("p", "."))
    return int(value) if value.is_integer() else value


class LimitPoint:
    def __init__(self, path):
        self.path = Path(path)
        self.name = self.path.parent.name
        self.parse_name()
        self.read_limits()

    def parse_name(self):
        match = re.match(
            r"(C1N2|stop)_M(\d+)_(\d+)_ct([0-9]+(?:p[0-9]+)?)(?:_BR([0-9]+(?:p[0-9]+)?))?$",
            self.name,
        )
        self.model = match.group(1)
        self.M = int(match.group(2))
        self.M2 = int(match.group(3))
        self.dM = self.M - self.M2
        self.ct = number_from_label(match.group(4))
        self.br = number_from_label(match.group(5)) if match.group(5) else None

    def read_limits(self):
        import ROOT

        self.limits = {}
        self.observed = None

        root_file = ROOT.TFile.Open(str(self.path))
        tree = root_file.Get("limit")

        for entry in range(tree.GetEntries()):
            tree.GetEntry(entry)
            quantile = float(tree.quantileExpected)
            value = float(tree.limit)
            if quantile < 0:
                self.observed = value
            else:
                matched = min(QUANTILES, key=lambda q: abs(q - quantile))
                self.limits[matched] = value

        root_file.Close()


class LimitCurve:
    def __init__(self, model, mass, daughter_mass):
        self.model = model
        self.M = mass
        self.M2 = daughter_mass
        self.dM = mass - daughter_mass
        self.points = []

    @property
    def name(self):
        return f"{self.model}_M{self.M}_{self.M2}"

    def add(self, point):
        self.points.append(point)

    def sorted_points(self):
        return sorted(self.points, key=lambda point: point.ct)

    def values(self, quantile):
        points = self.sorted_points()
        return [point.ct for point in points], [point.limits[quantile] for point in points]

    def plot(self, output_dir, extension, show_observed=False):
        import matplotlib.pyplot as plt

        x, y2lo = self.values(0.025)
        _, y1lo = self.values(0.16)
        _, ymed = self.values(0.50)
        _, y1hi = self.values(0.84)
        _, y2hi = self.values(0.975)

        fig, ax = plt.subplots(figsize=(8.0, 6.8))
        fig.subplots_adjust(top=0.90)

        ax.fill_between(x, y2lo, y2hi, color="#feff00", label=r"Expected $\pm 2\sigma$")
        ax.fill_between(x, y1lo, y1hi, color="#2df700", label=r"Expected $\pm 1\sigma$")
        ax.plot(x, ymed, color="black", marker="o", linewidth=1.8, label="Expected median")
        ax.axhline(1.0, color="black", linestyle="--", linewidth=1.5)

        if show_observed:
            observed_points = [
                point for point in self.sorted_points()
                if point.observed is not None
            ]
            ax.plot(
                [point.ct for point in observed_points],
                [point.observed for point in observed_points],
                color="black",
                marker="s",
                linestyle="--",
                linewidth=1.5,
                label="Observed",
            )

        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel(r"$c\tau$ [mm]", fontsize=14, loc='right')
        ax.set_ylabel(r"95% CL upper limit on signal strength $r$", fontsize=14, loc='center')
        ax.grid(True, which="both", linestyle=":", linewidth=0.3)
        ax.tick_params(axis="both", which="both", labelsize=12)

        y_min, y_max = ax.get_ylim()
        ax.set_ylim(y_min, y_max * 8.0)
        ax.text(
            0.03,
            0.97,
            rf"model: {self.model}" "\n"
            rf"$M$ = {self.M} GeV" "\n"
            rf"$\Delta M$ = {self.dM} GeV",
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
            "$273 \mathrm{fb}^{-1}$, (2017-2024)",
            transform=ax.transAxes,
            ha="right",
            va="bottom",
            fontsize=14,
            fontfamily=cms_font,
            # fontstyle="italic",
            clip_on=False,
        )

        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{self.name}.{extension}"
        fig.savefig(output_path, bbox_inches="tight")
        plt.close(fig)
        return output_path


def read_curves(limit_dir):
    curves = {}
    for path in sorted(limit_dir.glob("*/limits.root")):
        point = LimitPoint(path)
        key = (point.model, point.M, point.M2)
        if key not in curves:
            curves[key] = LimitCurve(point.model, point.M, point.M2)
        curves[key].add(point)
    return curves


def parse_args():
    parser = argparse.ArgumentParser(description="Plot expected limits from v2 limits.root files.")
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
    parser.add_argument("--observed", action="store_true")
    return parser.parse_args()


def main():
    args = parse_args()
    workdir = workdir_from_uniquedir(args.uniquedir)
    limit_dir = workdir / "limits" / args.limit_dir_name / args.mode
    output_dir = args.output_dir or workdir / "limitplots" / args.limit_dir_name / args.mode

    curves = read_curves(limit_dir)
    print(f"limit-dir: {limit_dir}")
    print(f"output-dir: {output_dir}")
    print(f"curves: {len(curves)}")

    for key in sorted(curves):
        output_path = curves[key].plot(output_dir, args.extension, args.observed)
        print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()
