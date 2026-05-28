#!/usr/bin/env python3
# Create all-year signal-sample datacards from reweighted signal pkl files.
# Run directly on the login node inside cmssw-el9. This script does not submit jobs.
# The observations are built from data by default; Asimov mode keeps region A blinded.
#
# Example:
# python3 AN-25-092_make_reweighted_pkl_datacards.py \
#   --histdir /scratch-cbe/users/alikaan.gueven/AN_plots/ParT_hists/AN-25-092_ML_plots_limitcalc_merge_w_Ang_v3 \
#   --signal-pkl-dir /scratch-cbe/users/alikaan.gueven/AN_plots/ParT_hists/AN-25-092_ML_plots_limitcalc_merge_w_Ang_v3_centralprod \
#   --xcut 350 --ycut 0.999 \
#   --output-dir /tmp/reweighted_cards

import argparse
from collections import defaultdict
import math
from pathlib import Path
import pickle as pkl
import re

from datacards import AnalysisConfig, DatacardGenerator, DEFAULT_HISTDIR, RootFile, RunOptions


DEFAULT_STOP_BRS = (0.1, 0.5, 1.0)
DEFAULT_STOP_ORIGIN_BR = 0.5
DEFAULT_C1N2_CTAUS = (0.2, 0.5, 1.0, 2.0, 5.0, 10.0, 50.0, 100.0, 200.0)
DEFAULT_PLANES = ("GT0", "GT1", "GT2", "GT3")


def token(value):
    return f"{value:g}".replace("-", "m").replace(".", "p")


def source_sample_name(path):
    stem = re.sub(r"_hist\d*$", "", path.stem)
    parts = stem.split("_")
    return "_".join(parts[:-1]) if parts[-1].isdigit() and len(parts[-1]) == 4 else stem


def target_sample_name(source_name, target_ctau, target_br=None):
    import utils

    info = utils.parse_signal_name(source_name)
    name = f"{info.model}_M{info.M}_{info.M2}_ct{token(target_ctau)}"
    return f"{name}_BR{token(target_br)}" if info.model == "stop" and target_br is not None else name


class PklSignalIndex:
    def __init__(self, histdir, analysis):
        self.histdir = Path(histdir).expanduser()
        self.analysis = analysis
        self.by_point = defaultdict(lambda: defaultdict(dict))

        import utils

        for year in analysis.years:
            signal_year = analysis.signal_file_year_by_year[year]
            for path in sorted((self.histdir / f"sig_{year}").glob(f"*_{signal_year}_hist*.pkl")):
                name = source_sample_name(path)
                info = utils.parse_signal_name(name)
                self.by_point[(info.model, info.M, info.M2)][info.ct][year] = (name, path)

    def target_specs(self, stop_brs, c1n2_ctaus):
        import utils

        specs = []
        for (model, mass, m2), entries_by_ctau in sorted(self.by_point.items()):
            origin_ctaus = sorted(entries_by_ctau)
            targets = []

            if model == "stop":
                dm = mass - m2
                targets = [
                    (utils.get_stop_ctau_for_br(mass, dm, br), br)
                    for br in stop_brs
                ]
            elif model == "C1N2":
                targets = [(ctau, None) for ctau in c1n2_ctaus]
            else:
                raise ValueError(f"Unsupported signal model: {model}")

            for target_ctau, target_br in targets:
                origin_ctau = next((ct for ct in origin_ctaus if ct >= target_ctau), origin_ctaus[-1])
                source_name, source_paths = self.source_for_all_years(entries_by_ctau[origin_ctau])
                specs.append(
                    {
                        "source_name": source_name,
                        "source_paths": source_paths,
                        "origin_ctau": origin_ctau,
                        "target_name": target_sample_name(source_name, target_ctau, target_br),
                        "target_ctau": target_ctau,
                        "target_br": target_br,
                    }
                )

        return specs

    def source_for_all_years(self, entries_by_year):
        missing = [year for year in self.analysis.years if year not in entries_by_year]
        if missing:
            available = ", ".join(sorted(entries_by_year))
            raise FileNotFoundError(
                f"Missing signal pkl files for years {missing}. Available years: {available}"
            )

        first_year = self.analysis.years[0]
        return entries_by_year[first_year][0], {
            year: entries_by_year[year][1]
            for year in self.analysis.years
        }


class SignalReweighter:
    def __init__(self, file_path, origin_ctau, origin_br=DEFAULT_STOP_ORIGIN_BR):
        import utils

        self.file_path = Path(file_path)
        with open(self.file_path, "rb") as f:
            self.d = pkl.load(f)

        sample_info = utils.parse_signal_name(source_sample_name(self.file_path))
        self.model = sample_info.model
        self.M = sample_info.M
        self.dM = sample_info.dM
        self.ct = origin_ctau
        self.origin_br = origin_br

    def require_fields(self, plane, fields):
        if plane not in self.d:
            raise KeyError(f"{self.file_path} does not contain plane '{plane}'.")

        missing = [field for field in fields if field not in self.d[plane]]
        if missing:
            available = ", ".join(sorted(self.d[plane])) or "none"
            raise KeyError(
                f"{self.file_path} plane '{plane}' is missing required pkl columns: {', '.join(missing)}. "
                f"Available columns: {available}."
            )

    def ctau_br_weight(self, plane, target_br, target_ctau):
        import utils

        if self.model == "stop":
            if target_br is None:
                target_br = self.origin_br

            self.require_fields(plane, ["LLP_ctau0", "LLP_ctau1", "LLP_decaymode0", "LLP_decaymode1"])
            w_ct0 = utils.get_ctau_weight(self.d[plane]["LLP_ctau0"], self.ct, target_ctau)
            w_ct1 = utils.get_ctau_weight(self.d[plane]["LLP_ctau1"], self.ct, target_ctau)
            if self.origin_br == 1.0:
                # Private stop samples can be generated with BR(stop->bffChi0)=1.
                # Events in mode 2 have zero support in that generated sample.
                w_br0 = target_br * (self.d[plane]["LLP_decaymode0"] == 1)
                w_br1 = target_br * (self.d[plane]["LLP_decaymode1"] == 1)
            else:
                w_br0 = utils.get_stop_decay_mode_br_weight(
                    self.d[plane]["LLP_decaymode0"],
                    origin=self.origin_br,
                    target=target_br,
                )
                w_br1 = utils.get_stop_decay_mode_br_weight(
                    self.d[plane]["LLP_decaymode1"],
                    origin=self.origin_br,
                    target=target_br,
                )
            return w_ct0 * w_ct1 * w_br0 * w_br1

        if self.model == "C1N2":
            self.require_fields(plane, ["LLP_ctau0"])
            return utils.get_ctau_weight(self.d[plane]["LLP_ctau0"], self.ct, target_ctau)

        raise ValueError(f"Unsupported model: {self.model}")

    def region_sums(self, plane, options, target_br, target_ctau):
        import numpy as np

        """
        Regions
        -------
        ML
        ^
        |  B  |  A
        | --- | ---
        |  D  |  C
        |-----------> MET
        """
        self.require_fields(plane, ["evt_weight", "MET_pt_corr", "leadingvtx_MLscore"])

        met = self.d[plane]["MET_pt_corr"]
        ml = self.d[plane]["leadingvtx_MLscore"]
        weight = self.d[plane]["evt_weight"] * self.ctau_br_weight(plane, target_br, target_ctau)
        masks = {
            "A": (met >= options.xcut) & (ml >= options.ycut),
            "B": (met < options.xcut) & (met >= options.xlo) & (ml >= options.ycut),
            "C": (met >= options.xcut) & (ml < options.ycut) & (ml >= options.ylo),
            "D": (met >= options.xlo) & (met < options.xcut) & (ml < options.ycut) & (ml >= options.ylo),
        }

        values = {}
        errors = {}
        for region, mask in masks.items():
            selected = weight[mask]
            values[region] = float(np.sum(selected))
            errors[region] = float(math.sqrt(np.sum(selected * selected)))
        return values, errors


class ReweightedPklDatacardGenerator(DatacardGenerator):
    def __init__(self, analysis, options, specs):
        super().__init__(analysis, options)
        self.specs_by_name = {spec["target_name"]: spec for spec in specs}
        self.current_spec = None

    def discover_samples(self):
        return sorted(self.specs_by_name)

    def generate_sample(self, sample_name):
        self.current_spec = self.specs_by_name[sample_name]
        try:
            return super().generate_sample(sample_name)
        finally:
            self.current_spec = None

    def fill_year(self, sample_name, year, category_id, observations, rates, signal_mc_stats):
        categories = []
        data_file = RootFile(self.analysis.data_path(self.histdir, year), "data")
        data_file.open()
        signal = SignalReweighter(self.current_spec["source_paths"][year], self.current_spec["origin_ctau"])

        try:
            for plane in self.analysis.planes:
                tables = self.read_plane_tables({"data": data_file}, plane)
                sig_values, sig_errors = signal.region_sums(
                    plane,
                    self.options,
                    self.current_spec["target_br"],
                    self.current_spec["target_ctau"],
                )
                tables["sig"] = {"values": sig_values, "errors": sig_errors}

                for region in self.analysis.regions:
                    bin_name = self.analysis.bin_name(year, plane, region)
                    categories.append((category_id, bin_name))
                    category_id += 1
                    self.fill_bin(bin_name, region, tables, observations, rates, signal_mc_stats)
        finally:
            data_file.close()

        return categories, category_id


def parse_args():
    parser = argparse.ArgumentParser(
        description="Create CombineHarvester ABCD datacards from reweighted signal pkl files."
    )
    parser.add_argument("--xcut", type=float, default=350.0, help="MET threshold. Default: 350.")
    parser.add_argument("--xlo", type=float, default=250.0, help="Lower MET threshold. Default: 250.")
    parser.add_argument("--ycut", type=float, default=0.999, help="ML score threshold. Default: 0.999.")
    parser.add_argument("--ylo", type=float, default=0.80, help="Lower ML score threshold. Default: 0.80.")
    parser.add_argument("--histdir", type=Path, default=DEFAULT_HISTDIR, help="Plotter unique directory.")
    parser.add_argument(
        "--signal-pkl-dir",
        type=Path,
        default=None,
        help="Directory containing sig_<year> pkl files. Default: --histdir.",
    )
    parser.add_argument("--datacard-dir-name", default="reweighted", help="Directory below <histdir>/datacards.")
    parser.add_argument("--output-dir", type=Path, default=None, help="Exact datacard output directory.")
    parser.add_argument("--mode", choices=["Asimov", "observation"], default="Asimov", help="Datacard mode.")
    parser.add_argument("--planes", nargs="+", default=list(DEFAULT_PLANES), help="Planes to include in datacards.")
    parser.add_argument("--stop-br", nargs="+", type=float, default=list(DEFAULT_STOP_BRS), help="Stop target BR values.")
    parser.add_argument(
        "--c1n2-ctau",
        nargs="+",
        type=float,
        default=list(DEFAULT_C1N2_CTAUS),
        help="C1N2 target ctau values in mm.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    analysis = AnalysisConfig()
    analysis.planes = tuple(args.planes)
    options = RunOptions(
        xcut=args.xcut,
        xlo=args.xlo,
        ycut=args.ycut,
        ylo=args.ylo,
        histdir=args.histdir,
        output_dir=args.output_dir,
        datacard_dir_name=args.datacard_dir_name,
        mode=args.mode,
        use_data=True,
    )

    signal_pkl_dir = args.signal_pkl_dir or args.histdir
    specs = PklSignalIndex(signal_pkl_dir, analysis).target_specs(args.stop_br, args.c1n2_ctau)
    ReweightedPklDatacardGenerator(analysis, options, specs).generate_all()


if __name__ == "__main__":
    main()
