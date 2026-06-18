import warnings

warnings.filterwarnings(
    "ignore",
    message="The value of the smallest subnormal for.*type is zero.",
    category=UserWarning,
)

import ROOT
from pathlib import Path
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
# import math
import re
import utils


QUANTILES = [0.025, 0.16, 0.50, 0.84, 0.975]


class LimitScanPoint:
    def __init__(self, file_path):
        self.file_path = Path(file_path)

        self.name = self.file_path.parent.name
        self.fit_type  = self.file_path.parents[1].name     # Asimov/observation
        self.scan_name = self.file_path.parents[3].name     # MET700_ML0p999
        self.MET, self.ML = self.parse_scan_name()

        sample_info = utils.parse_signal_name(self.name)

        self.model = sample_info.model
        self.M     = sample_info.M
        self.dM    = sample_info.dM
        self.ct    = sample_info.ct

        self.limits = {}
        self.read_limits()

    def parse_scan_name(self):
        # Example: MET700_ML0p999
        m = re.search(r"MET(\d+)_ML([0-9]+p[0-9]+)", self.scan_name)
        if not m: 
            return float("nan"), float("nan")
        else:
            met = int(m.group(1))
            ml_score = float(m.group(2).replace("p", "."))
            return met, ml_score

    def read_limits(self):
        values = [float("nan")] * len(QUANTILES)

        try:
            file = ROOT.TFile.Open(str(self.file_path))
            tree = file.Get("limit")

            n_entries = min(tree.GetEntries(), len(QUANTILES))

            for i in range(n_entries):
                tree.GetEntry(i)
                values[i] = float(tree.limit)

            file.Close()

        except Exception:
            values = [float("nan")] * len(QUANTILES)

        self.limits = dict(zip(QUANTILES, values))

    def get_limit(self, quantileExpected=0.50):
        return self.limits.get(quantileExpected, float("nan"))
    

class SignalSample:
    def __init__(self, name):
        self.name = name

        sample_info = utils.parse_signal_name(name)

        self.model = sample_info.model
        self.M = sample_info.M
        self.dM = sample_info.dM
        self.ct = sample_info.ct

        self.scan_points = {}

    def add_scan_point(self, scan_point):
        self.scan_points[scan_point.scan_name] = scan_point

    def get_limit(self, scan_name, quantileExpected=0.50):
        scan_point = self.scan_points.get(scan_name)

        if scan_point is None:
            return float("nan")

        return scan_point.get_limit(quantileExpected)
    
    def make_dataframe(self, quantileExpected=0.50):
        rows = []

        for scan_name, scan_point in self.scan_points.items():
            rows.append({
                "scan_name": scan_name,
                "MET": scan_point.MET,
                "ML": scan_point.ML,
                "limit": scan_point.get_limit(quantileExpected),
            })

        return pd.DataFrame(rows)

    def make_table(self, quantileExpected=0.50):
        df = self.make_dataframe(quantileExpected)

        table = df.pivot_table(
            index="ML",
            columns="MET",
            values="limit",
            aggfunc="first",
        )

        table = table.sort_index(ascending=False)
        table = table.sort_index(axis=1)

        return table
    
    def get_default_plot_dir(self):
        first_scan_point = next(iter(self.scan_points.values()))
        abcdscan_dir = first_scan_point.file_path.parents[4]
        return abcdscan_dir / "AN-25-092_scanplots"

    def plot_scan(self, quantileExpected=0.50, output_dir=None, extension="png"):
        table = self.make_table(quantileExpected)

        fig = plt.figure(figsize=(8,8))

        gs = fig.add_gridspec(
            2, 2,
            height_ratios=[1, 5],
            width_ratios=[25, 1],
            hspace=0.15,
            wspace=0.08,
        )

        ax_info = fig.add_subplot(gs[0, 0])
        ax = fig.add_subplot(gs[1, 0])
        cax = fig.add_subplot(gs[1, 1])

        # Upper pad with bounding box
        ax_info.set_xticks([])
        ax_info.set_yticks([])
        ax_info.set_xlim(0, 1)
        ax_info.set_ylim(0, 1)

        for spine in ax_info.spines.values():
            spine.set_visible(True)
            spine.set_linewidth(1.0)

        info_text = (
            rf"{self.model}    "
            rf"$M$ = {self.M} GeV    "
            rf"$\Delta M$ = {self.dM} GeV    "
            rf"$c\tau$ = {self.ct:g} mm"
        )

        ax_info.text(
            0.5, 0.5, info_text,
            transform=ax_info.transAxes,
            ha="center",
            va="center",
            fontsize=12,
        )

        # Lower pad
        hm = sns.heatmap(
            table,
            annot=False,
            ax=ax,
            cbar_ax=cax,
            # cmap="rocket_r",
            cmap="Blues_r",
            cbar_kws={"label": r"signal strength ($r$)"},
            vmin=0,
            vmax=3,
        )

        ax.set_xlabel(r"MET ($\mathrm{GeV}$)", fontsize=14)
        ax.set_ylabel("ML score", fontsize=14)
        ax.tick_params(axis="both", labelsize=12)

        # No bounding box around lower heatmap
        for spine in ax.spines.values():
            spine.set_visible(False)

        # Colour bar styling
        cbar = hm.collections[0].colorbar
        cbar.ax.tick_params(labelsize=12)
        cbar.set_label(r"signal strength ($r$)", fontsize=14)
        cbar.outline.set_visible(True)
        cbar.outline.set_linewidth(1.0)

        fig.tight_layout()

        if output_dir is None:
            output_dir = self.get_default_plot_dir()

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        q_label = str(quantileExpected).replace(".", "p")
        output_path = output_dir / f"{self.name}_q{q_label}.{extension}"

        fig.savefig(output_path, bbox_inches="tight")
        plt.close(fig)

        return output_path
    
def main():
    abcdscan_dir = Path(
        "/scratch-cbe/users/alikaan.gueven/AN_plots/ParT_hists/"
        "AN-25-092_ML_plots_limitcalc_merge_w_Ang_v3/ABCDscan"
    )

    limit_files = sorted(abcdscan_dir.glob("*/limits/Asimov/*/limits.root"))

    samples = {}

    for file_path in limit_files:
        scan_point = LimitScanPoint(file_path)

        if scan_point.name not in samples:
            samples[scan_point.name] = SignalSample(scan_point.name)

        samples[scan_point.name].add_scan_point(scan_point)

    for sample in samples.values():
        output_path = sample.plot_scan(quantileExpected=0.50)
        print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()