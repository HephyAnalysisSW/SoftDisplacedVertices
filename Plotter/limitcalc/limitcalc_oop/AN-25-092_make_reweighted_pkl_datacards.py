#!/usr/bin/env python3
# Create all-year signal-sample datacards from reweighted signal pkl files.
# Run directly on the login node inside cmssw-el9. This script does not submit jobs.
# The observations are built from data by default; Asimov mode keeps region A blinded.
#
# Example:
# python3 AN-25-092_make_reweighted_pkl_datacards.py \
#   --uniquedir AN-25-092_ML_plots_limitcalc_merge_w_Ang_v3 \
#   --xcut 500 --ycut 0.999 \
#   --output-dir /tmp/reweighted_cards

import argparse
from collections import defaultdict
import math
from pathlib import Path
import pickle as pkl
import re

import numpy as np

from datacards import DEFAULT_SCRATCH_BASE, DatacardGenerator, DatacardInputs, RootFile, RunOptions
import utils


DEFAULT_STOP_BRS = (0.1, 0.5, 1.0)
DEFAULT_STOP_ORIGIN_BR = 0.5
DEFAULT_C1N2_CTAUS = (0.2, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 50.0, 100.0, 200.0)
DEFAULT_PLANES = ("GT1", "GT2", "GT3")
ALLOWED_STOP_SOURCE_CTAUS_BY_DM = {
    12: (20.0, 200.0),
    15: (2.0, 20.0),
    20: (0.2, 2.0),
    25: (0.2,),
}
ALLOWED_C1N2_SOURCE_CTAUS = (0.2, 2.0, 20.0, 200.0)


# Flow:
# 1. Read merged signal pickles from sig_<year> directories.
# 2. For each mass point, choose the source ctau from the allowed ones.
# 3. Reweight signal events to target ctau/BR values.
# 4. Pass reweighted yields to the common datacard writer.


def source_sample_name(path):
    """Return the physics sample name stored in a merged pickle filename."""
    # Example: stopML_M1000_980_ct2_2018_hist.pkl -> stopML_M1000_980_ct2
    stem = re.sub(r"_hist\d*$", "", path.stem)
    parts = stem.split("_")
    if re.fullmatch(r"20\d{2}(?:Pre|Post)?", parts[-1]):
        return "_".join(parts[:-1])
    return stem


class PickleSignalIndex:
    """Find source pickle files and map them to target reweighted samples."""

    def __init__(self, uniquedir, datacard_inputs):
        """Index all signal pickles under sig_<year> directories."""
        self.uniquedir = Path(uniquedir).expanduser()
        self.datacard_inputs = datacard_inputs
        self.signal_files_by_point = defaultdict(lambda: defaultdict(dict))

        for year in datacard_inputs.years:
            signal_dir = self.uniquedir / f"sig_{year}"
            signal_paths = sorted(signal_dir.glob("*_hist.pkl"))
            if not signal_paths:
                raise FileNotFoundError(
                    f"No merged signal pickle files found in {signal_dir}. "
                    "Run hadd first and provide files ending in '_hist.pkl'."
                )

            for path in signal_paths:
                source_name = source_sample_name(path)
                signal_info = utils.parse_signal_name(source_name)
                signal_point = (signal_info.model, signal_info.M, signal_info.M2)
                self.signal_files_by_point[signal_point][signal_info.ct][year] = (source_name, path)

    def reweighting_plans(self, stop_brs, c1n2_ctaus):
        """Return one source-to-target reweighting plan per datacard."""
        reweighting_plans = []
        for (model, mass, daughter_mass), files_by_ctau in sorted(
            self.signal_files_by_point.items()
        ):
            available_ctaus = sorted(files_by_ctau)
            mass_gap = mass - daughter_mass

            if model == "stop":
                allowed_ctaus = ALLOWED_STOP_SOURCE_CTAUS_BY_DM.get(mass_gap)
                if allowed_ctaus is None:
                    raise ValueError(f"No allowed stop source ctaus for dM={mass_gap}")

                targets = [
                    (utils.get_stop_ctau_for_br(mass, mass_gap, stop_br), stop_br)
                    for stop_br in stop_brs
                ]
            elif model == "C1N2":
                allowed_ctaus = ALLOWED_C1N2_SOURCE_CTAUS
                targets = [(ctau, None) for ctau in c1n2_ctaus]
            else:
                raise ValueError(f"Unsupported signal model: {model}")

            source_ctaus = []
            for ctau in allowed_ctaus:
                if ctau in available_ctaus:
                    source_ctaus.append(ctau)
                else:
                    raise FileNotFoundError(f'ctau={ctau} sample is this not available. Why?')

            for target_ctau, target_br in targets:
                origin_ctau = utils.choose_source_ctau(source_ctaus, target_ctau)
                source_files_by_year = files_by_ctau[origin_ctau]
                missing_years = [
                    year
                    for year in self.datacard_inputs.years
                    if year not in source_files_by_year
                ]
                if missing_years:
                    available_years = ", ".join(sorted(source_files_by_year))
                    raise FileNotFoundError(
                        f"Missing signal pkl files for years {missing_years}. "
                        f"Available years: {available_years}"
                    )

                first_year = self.datacard_inputs.years[0]
                source_name = source_files_by_year[first_year][0]
                source_paths = {}
                for year in self.datacard_inputs.years:
                    year_source_name, path = source_files_by_year[year]
                    if year_source_name != source_name:
                        raise ValueError(
                            f"Mixed source names for {year}: "
                            f"{year_source_name} != {source_name}"
                        )
                    source_paths[year] = path

                target_ctau_label = f"{target_ctau:g}".replace(".", "p")
                target_name = f"{model}_M{mass}_{daughter_mass}_ct{target_ctau_label}"
                if model == "stop":
                    target_br_label = f"{target_br:g}".replace(".", "p")
                    target_name = f"{target_name}_BR{target_br_label}"

                reweighting_plans.append(
                    {
                        "source_name": source_name,
                        "source_paths": source_paths,
                        "origin_ctau": origin_ctau,
                        "target_name": target_name,
                        "target_ctau": target_ctau,
                        "target_br": target_br,
                    }
                )

        return reweighting_plans


class SignalReweighter:
    """Load one merged source pickle and compute reweighted ABCD signal yields."""

    def __init__(self, file_path, origin_ctau):
        """Read the merged pickle and store the generated ctau origin."""
        self.file_path = Path(file_path)
        with open(self.file_path, "rb") as f:
            self.events_by_plane = pkl.load(f)

        sample_info = utils.parse_signal_name(source_sample_name(self.file_path))
        self.model = sample_info.model
        self.origin_ctau = origin_ctau
        self.origin_br = DEFAULT_STOP_ORIGIN_BR

    def require_fields(self, plane, fields):
        """Fail early if a pickle plane misses columns required downstream."""
        if plane not in self.events_by_plane:
            raise KeyError(f"{self.file_path} does not contain plane '{plane}'.")

        missing = [field for field in fields if field not in self.events_by_plane[plane]]
        if missing:
            available = ", ".join(sorted(self.events_by_plane[plane])) or "none"
            raise KeyError(
                f"{self.file_path} plane '{plane}' is missing required pkl "
                f"columns: {', '.join(missing)}. "
                f"Available columns: {available}."
            )

    def region_sums(self, plane, options, target_br, target_ctau):
        """Apply ABCD cuts and return weighted yields and gmN-style errors."""
        self.require_fields(plane, ["evt_weight", "MET_pt_corr", "leadingvtx_MLscore"])
        events = self.events_by_plane[plane]

        if self.model == "stop":
            if target_br is None:
                target_br = self.origin_br

            self.require_fields(plane, ["LLP_ctau0", "LLP_ctau1", "LLP_decaymode0", "LLP_decaymode1"])
            ctau_weight0 = utils.get_ctau_weight(events["LLP_ctau0"], self.origin_ctau, target_ctau)
            ctau_weight1 = utils.get_ctau_weight(events["LLP_ctau1"], self.origin_ctau, target_ctau)
            ctau_weight = np.clip(ctau_weight0 * ctau_weight1, a_min=0, a_max=100)
            br_weight0 = utils.get_stop_decay_mode_br_weight(
                events["LLP_decaymode0"],
                origin=self.origin_br,
                target=target_br,
            )
            br_weight1 = utils.get_stop_decay_mode_br_weight(
                events["LLP_decaymode1"],
                origin=self.origin_br,
                target=target_br,
            )
            reweight = ctau_weight * br_weight0 * br_weight1
        elif self.model == "C1N2":
            self.require_fields(plane, ["LLP_ctau0"])
            ctau_weight = utils.get_ctau_weight(events["LLP_ctau0"], self.origin_ctau, target_ctau)
            reweight = np.clip(ctau_weight, a_min=0, a_max=100)
        else:
            raise ValueError(f"Unsupported model: {self.model}")

        met = events["MET_pt_corr"]
        ml_score = events["leadingvtx_MLscore"]
        event_weight = events["evt_weight"] * reweight

        # Regions in MET/ML space:
        #   B | A
        #   D | C
        masks = {
            "A": (met >= options.xcut) & (ml_score >= options.ycut),
            "B": (met < options.xcut) & (met >= options.xlo) & (ml_score >= options.ycut),
            "C": (met >= options.xcut) & (ml_score < options.ycut) & (ml_score >= options.ylo),
            "D": (
                (met >= options.xlo)
                & (met < options.xcut)
                & (ml_score < options.ycut)
                & (ml_score >= options.ylo)
            ),
        }

        values = {}
        errors = {}
        for region, mask in masks.items():
            selected_weight = event_weight[mask]
            nonzero_events = int(np.sum(reweight[mask] != 0))
            values[region] = float(np.sum(selected_weight))
            errors[region] = values[region] / math.sqrt(nonzero_events) if nonzero_events > 0 else 0.0
        return values, errors


class ReweightedPickleDatacardGenerator(DatacardGenerator):
    """Datacard generator that replaces ROOT signal histograms with pickles."""

    def __init__(self, datacard_inputs, options, reweighting_plans):
        """Store reweighting plans and initialise the shared datacard writer."""
        super().__init__(datacard_inputs, options)
        self.reweighting_plans_by_name = {plan["target_name"]: plan for plan in reweighting_plans}
        self.current_reweighting_plan = None

    def discover_samples(self):
        """Return output sample names built from reweighting plans."""
        return sorted(self.reweighting_plans_by_name)

    def generate_sample(self, sample_name):
        """Set the active reweighting plan while the base writer builds a card."""
        self.current_reweighting_plan = self.reweighting_plans_by_name[sample_name]
        try:
            return super().generate_sample(sample_name)
        finally:
            self.current_reweighting_plan = None

    def fill_year(self, year, category_id, observations, rates, signal_mc_stats):
        """Fill all categories for one year using data ROOT and signal pickle."""
        categories = []
        data_file = RootFile(self.datacard_inputs.data_path(self.histdir, year), "data")
        data_file.open()
        signal = SignalReweighter(
            self.current_reweighting_plan["source_paths"][year],
            self.current_reweighting_plan["origin_ctau"],
        )

        try:
            for plane in self.datacard_inputs.planes:
                tables = self.read_plane_tables({"data": data_file}, plane)
                signal_values, signal_errors = signal.region_sums(
                    plane,
                    self.options,
                    self.current_reweighting_plan["target_br"],
                    self.current_reweighting_plan["target_ctau"],
                )
                tables["sig"] = {"values": signal_values, "errors": signal_errors}

                for region in self.datacard_inputs.regions:
                    bin_name = self.datacard_inputs.bin_name(year, plane, region)
                    categories.append((category_id, bin_name))
                    category_id += 1
                    self.fill_bin(bin_name, region, tables, observations, rates, signal_mc_stats)
        finally:
            data_file.close()

        return categories, category_id


def parse_args():
    """Parse CLI options for input discovery, cuts, targets, and dry run."""
    parser = argparse.ArgumentParser(
        description="Create CombineHarvester ABCD datacards from reweighted signal pkl files."
    )

    parser.add_argument(
        "--uniquedir",
        required=True,
        help=f"Directory name below {DEFAULT_SCRATCH_BASE}. Absolute paths are also accepted.",
    )

    parser.add_argument("--xcut", type=float, default=500.0, help="MET threshold. Default: 500.")
    parser.add_argument("--xlo", type=float, default=250.0, help="Lower MET threshold. Default: 250.")
    parser.add_argument("--ycut", type=float, default=0.999, help="ML score threshold. Default: 0.999.")
    parser.add_argument("--ylo", type=float, default=0.80, help="Lower ML score threshold. Default: 0.80.")

    parser.add_argument("--mode", choices=["Asimov", "observation"], default="Asimov", help="Datacard mode.")
    parser.add_argument("--output-dir", type=Path, default=None, help="Exact datacard output directory.")
    parser.add_argument("--datacard-dir-name", default="reweighted", help="Directory below <uniquedir>/datacards.")
    parser.add_argument("--dryrun", action="store_true", help="Print resolved inputs and outputs without writing.")

    parser.add_argument("--planes", nargs="+", default=list(DEFAULT_PLANES), help="Planes to include in datacards.")
    parser.add_argument(
        "--stop-br",
        nargs="+",
        type=float,
        default=list(DEFAULT_STOP_BRS),
        help="Stop target BR values.",
    )
    parser.add_argument(
        "--c1n2-ctau",
        nargs="+",
        type=float,
        default=list(DEFAULT_C1N2_CTAUS),
        help="C1N2 target ctau values in mm.",
    )

    return parser.parse_args()


def main():
    """Build reweighting plans, then either print them or write datacards."""
    args = parse_args()
    uniquedir = Path(args.uniquedir).expanduser()
    if not uniquedir.is_absolute():
        uniquedir = DEFAULT_SCRATCH_BASE / uniquedir

    datacard_inputs = DatacardInputs()
    datacard_inputs.planes = tuple(args.planes)
    options = RunOptions(
        xcut=args.xcut,
        xlo=args.xlo,
        ycut=args.ycut,
        ylo=args.ylo,
        histdir=uniquedir,
        output_dir=args.output_dir,
        datacard_dir_name=args.datacard_dir_name,
        mode=args.mode,
        use_data=True,
    )

    reweighting_plans = PickleSignalIndex(uniquedir, datacard_inputs).reweighting_plans(
        args.stop_br,
        args.c1n2_ctau,
    )

    if args.dryrun:
        print(f"uniquedir: {options.histdir}")
        print(f"output-dir: {options.datacard_output_dir()}")
        print(f"planes: {' '.join(datacard_inputs.planes)}")
        print(f"years: {' '.join(datacard_inputs.years)}")
        print(f"stop origin BR: {DEFAULT_STOP_ORIGIN_BR:g}")
        print(f"target samples: {len(reweighting_plans)}")

        for year in datacard_inputs.years:
            data_path = datacard_inputs.data_path(options.histdir, year)
            status = "ok" if data_path.exists() else "missing"
            relative_data_path = data_path.relative_to(options.histdir)
            print(f"data ROOT {year}: {relative_data_path} [{status}]")

        for reweighting_plan in reweighting_plans:
            print(
                f"datacard: {reweighting_plan['target_name']}.txt  "
                f"source={reweighting_plan['source_name']} "
                f"origin_ctau={reweighting_plan['origin_ctau']:g} "
                f"target_ctau={reweighting_plan['target_ctau']:g}"
            )
        return

    ReweightedPickleDatacardGenerator(datacard_inputs, options, reweighting_plans).generate_all()


if __name__ == "__main__":
    main()
