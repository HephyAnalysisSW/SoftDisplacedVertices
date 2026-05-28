#!/usr/bin/env python3

import argparse
from ctypes import c_double
import math
from pathlib import Path
import pickle as pkl
import re

import numpy as np
import ROOT
import yaml


DEFAULT_BASEDIR = Path("/scratch-cbe/users/alikaan.gueven/AN_plots/ParT_hists")
DEFAULT_YEARS = ["2017", "2018", "2022Pre", "2022Post", "2023Pre", "2023Post", "2024"]
DEFAULT_PLANES = ["GT1", "GT2", "GT3"]
DEFAULT_REGIONS = ["A", "B", "C", "D"]
DEFAULT_STOP_BR = 0.5
DEFAULT_STOP_BRS = [0.1, 0.5, 1.0]
DEFAULT_C1N2_CTAUS = [0.2, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 50.0, 100.0, 200.0]
ALLOWED_STOP_SOURCE_CTAUS_BY_DM = {
    12: [20.0, 200.0],
    15: [2.0, 20.0],
    20: [0.2, 2.0],
    25: [0.2],
}
ALLOWED_C1N2_SOURCE_CTAUS = [0.2, 2.0, 20.0, 200.0]
HIST_NAME = "MET_pt_corr_vs_leadingvtx_MLscore"
SYSTEMATICS_PATH = Path(__file__).with_name("systematics_sig.yaml")


def ct_label_to_number(label):
    value = float(label.replace("p", "."))
    return int(value) if value.is_integer() else value


def workdir_from_uniquedir(uniquedir):
    workdir = Path(uniquedir).expanduser()
    return workdir if workdir.is_absolute() else DEFAULT_BASEDIR / workdir


def sample_name_from_hist_path(path):
    return path.stem.removesuffix("_hist").rsplit("_", 1)[0]


def model_from_sample_name(sample_name):
    return "C1N2" if sample_name.startswith("C1N2") else "stop"


def number_label(value):
    return f"{value:g}".replace(".", "p")


def stop_4body_width(mass, dm):
    return 9 * 28 * 1.98e-14 * (dm / 30) ** 8 * (400 / mass)


def stop_ctau_for_br(mass, dm, br):
    return 1.973269788e-13 / (stop_4body_width(mass, dm) / br)


def choose_source_ctau(source_ctaus, target_ctau):
    source_ctaus = sorted(source_ctaus)
    for source_ctau in source_ctaus:
        if np.isclose(source_ctau, target_ctau):
            return source_ctau

    index = np.searchsorted(source_ctaus, target_ctau, side="right")
    if index == 0:
        return source_ctaus[index]
    if index >= len(source_ctaus):
        return source_ctaus[index - 1]
    return source_ctaus[index]


class Sample:
    sample_type = None

    def __init__(self, workdir, years):
        self.workdir = Path(workdir)
        self.years = years
        self.values = {}

    def directory(self, year):
        return self.workdir / f"{self.sample_type}_{year}"


class Signal(Sample):
    sample_type = "sig"

    def __init__(self, sample_name, workdir, paths):
        super().__init__(workdir, DEFAULT_YEARS)
        self.sample_name = sample_name
        self.paths = paths
        self.parse_name()
        self.load_values()

    def parse_name(self):
        match = re.match(
            r"(.+)_M(\d+)_(\d+)_ct([0-9]+(?:p[0-9]+)?)$",
            self.sample_name,
        )
        self.model = model_from_sample_name(match.group(1))
        self.M = int(match.group(2))
        self.M2 = int(match.group(3))
        self.dM = self.M - self.M2
        self.ct = ct_label_to_number(match.group(4))
        self.target_ct = self.ct
        self.target_br = DEFAULT_STOP_BR

    def path(self, year):
        return self.paths[year]

    def load_values(self):
        for year in self.years:
            with open(self.path(year), "rb") as f:
                self.values[year] = pkl.load(f)

    def reweight_to(self, target_ct, target_br=DEFAULT_STOP_BR):
        self.target_ct = target_ct
        self.target_br = target_br
        return self

    def get_yields(self, xcut, xlo, ycut, ylo):
        yields = {}
        for year, planes in self.values.items():
            yields[year] = {}
            for plane in DEFAULT_PLANES:
                events = planes[plane]
                met = events["MET_pt_corr"]
                ml = events["leadingvtx_MLscore"]
                reweight = self.reweight(events)
                weights = events["evt_weight"] * reweight
                yields[year][plane] = self.weighted_abcd_yields(
                    met,
                    ml,
                    weights,
                    reweight,
                    xcut,
                    xlo,
                    ycut,
                    ylo,
                )
        return yields

    def reweight(self, events):
        if self.model == "stop":
            return self.stop_reweight(events)
        return self.c1n2_reweight(events)

    def stop_reweight(self, events):
        ctau_weight0 = self.ctau_weight(events["LLP_ctau0"])
        ctau_weight1 = self.ctau_weight(events["LLP_ctau1"])
        ctau_weight = np.clip(ctau_weight0 * ctau_weight1, a_min=0, a_max=100)
        br_weight0 = self.stop_br_weight(events["LLP_decaymode0"])
        br_weight1 = self.stop_br_weight(events["LLP_decaymode1"])
        return ctau_weight * br_weight0 * br_weight1

    def c1n2_reweight(self, events):
        ctau_weight = self.ctau_weight(events["LLP_ctau0"])
        return np.clip(ctau_weight, a_min=0, a_max=100)

    def ctau_weight(self, ct):
        clipped_ct = np.clip(ct, a_min=0, a_max=self.ct)
        return (self.ct / self.target_ct) * np.exp(
            clipped_ct * 10 * ((1 / self.ct) - (1 / self.target_ct))
        )

    def stop_br_weight(self, decaymode):
        weight_4body = self.target_br / DEFAULT_STOP_BR
        weight_2body = (1 - self.target_br) / (1 - DEFAULT_STOP_BR)
        return weight_4body * (decaymode == 1) + weight_2body * (decaymode == 2)

    def weighted_abcd_yields(self, met, ml, weights, reweight, xcut, xlo, ycut, ylo):
        masks = {
            "A": (met >= xcut) & (ml >= ycut),
            "B": (met < xcut) & (met >= xlo) & (ml >= ycut),
            "C": (met >= xcut) & (ml < ycut) & (ml >= ylo),
            "D": (met < xcut) & (met >= xlo) & (ml < ycut) & (ml >= ylo),
        }
        return {
            region: self.weighted_yield(weights, reweight, mask)
            for region, mask in masks.items()
        }

    def weighted_yield(self, weights, reweight, mask):
        value = float(np.sum(weights[mask]))
        n_events = int(np.sum(reweight[mask] != 0))
        error = value / math.sqrt(n_events) if n_events > 0 else 0.0
        return {"yield": value, "error": error}


class Data(Sample):
    sample_type = "data"

    def __init__(self, workdir, years):
        super().__init__(workdir, years)
        self.sample_name = "data"
        self.hist_name = HIST_NAME
        self.load_values()

    def path(self, year):
        return self.directory(year) / f"data_{year}_hist.root"

    def load_values(self):
        for year in self.years:
            self.values[year] = ROOT.TFile.Open(str(self.path(year)))

    def hist(self, year, plane):
        return self.values[year].Get(f"{plane}_evt/{self.hist_name}")

    def get_yields(self, xcut, xlo, ycut, ylo):
        yields = {}
        for year in self.years:
            yields[year] = {}
            for plane in DEFAULT_PLANES:
                yields[year][plane] = self.hist_abcd_yields(
                    self.hist(year, plane),
                    xcut,
                    xlo,
                    ycut,
                    ylo,
                )
        return yields

    def hist_abcd_yields(self, hist, xcut, xlo, ycut, ylo):
        xbin = hist.GetXaxis().FindBin(xcut)
        xlo_bin = hist.GetXaxis().FindBin(xlo)
        ybin = hist.GetYaxis().FindBin(ycut)
        ylo_bin = hist.GetYaxis().FindBin(ylo)
        last_x_bin = hist.GetNbinsX() + 1
        last_y_bin = hist.GetNbinsY() + 1
        regions = {
            "A": (xbin, last_x_bin, ybin, last_y_bin),
            "B": (xlo_bin, xbin - 1, ybin, last_y_bin),
            "C": (xbin, last_x_bin, ylo_bin, ybin - 1),
            "D": (xlo_bin, xbin - 1, ylo_bin, ybin - 1),
        }
        return {
            region: self.hist_yield(hist, bins)
            for region, bins in regions.items()
        }

    def hist_yield(self, hist, bins):
        bx1, bx2, by1, by2 = bins
        error = c_double(0.0)
        value = hist.IntegralAndError(bx1, bx2, by1, by2, error)
        return {"yield": value, "error": error.value}


def signal_paths(workdir, years):
    paths = {}
    for year in years:
        for path in sorted((workdir / f"sig_{year}").glob("*_hist.pkl")):
            sample_name = sample_name_from_hist_path(path)
            paths.setdefault(sample_name, {})
            if year in paths[sample_name]:
                raise ValueError(f"Multiple files for {sample_name} in sig_{year}")
            paths[sample_name][year] = path
    return paths


def load_samples(workdir, years):
    signals = [
        Signal(sample_name, workdir, paths)
        for sample_name, paths in sorted(signal_paths(workdir, years).items())
    ]
    data = Data(workdir, years)
    return signals, data


class Datacard:
    def __init__(self, signal, data, output_dir, xcut, xlo, ycut, ylo, mode):
        self.signal = signal
        self.data = data
        self.output_dir = Path(output_dir)
        self.xcut = xcut
        self.xlo = xlo
        self.ycut = ycut
        self.ylo = ylo
        self.mode = mode
        self.signal_yields = signal.get_yields(xcut, xlo, ycut, ylo)
        self.data_yields = data.get_yields(xcut, xlo, ycut, ylo)
        self.systematics = yaml.safe_load(SYSTEMATICS_PATH.read_text(encoding="utf-8"))

    def bin_name(self, year, plane, region):
        return f"y{year}_{plane}_{region}"

    def bins(self):
        return [
            self.bin_name(year, plane, region)
            for year in self.signal.years
            for plane in DEFAULT_PLANES
            for region in DEFAULT_REGIONS
        ]

    def observation(self, bin_name):
        year, plane, region = self.parts(bin_name)
        if self.mode == "Asimov" and region == "A":
            values = self.data_yields[year][plane]
            return values["B"]["yield"] * values["C"]["yield"] / values["D"]["yield"]
        return self.data_yields[year][plane][region]["yield"]

    def signal_rate(self, bin_name):
        year, plane, region = self.parts(bin_name)
        return self.signal_yields[year][plane][region]["yield"]

    def signal_error(self, bin_name):
        year, plane, region = self.parts(bin_name)
        return self.signal_yields[year][plane][region]["error"]

    def parts(self, bin_name):
        year, plane, region = bin_name.removeprefix("y").split("_")
        return year, plane, region

    def write(self):
        import CombineHarvester.CombineTools.ch as ch

        self.output_dir.mkdir(parents=True, exist_ok=True)
        path = self.output_dir / f"{self.signal.datacard_name}.txt"
        root_path = self.output_dir / f".{self.signal.datacard_name}.root"

        cb = self.combine_harvester(ch)
        cb.WriteDatacard(str(path), str(root_path))
        if root_path.exists():
            root_path.unlink()

        self.postprocess(path)
        print(f"Wrote datacard: {path}")
        return path

    def combine_harvester(self, ch):
        cb = ch.CombineHarvester()
        category_id = 1

        for year in self.signal.years:
            categories = []
            for plane in DEFAULT_PLANES:
                for region in DEFAULT_REGIONS:
                    categories.append((category_id, self.bin_name(year, plane, region)))
                    category_id += 1

            cb.AddObservations(["mass"], ["AN-25-092"], [year], ["channel"], categories)
            cb.AddProcesses(["mass"], ["AN-25-092"], [year], ["channel"], ["sig"], categories, True)
            cb.AddProcesses(["mass"], ["AN-25-092"], [year], ["channel"], ["bkg"], categories, False)

        cb.ForEachObs(lambda obs: obs.set_rate(self.observation(obs.bin())))
        cb.ForEachProc(lambda proc: proc.set_rate(self.process_rate(proc.bin(), proc.process())))
        self.add_signal_systematics(cb, ch)
        return cb

    def process_rate(self, bin_name, process):
        if process == "sig":
            return self.signal_rate(bin_name)
        return 1.0

    def add_signal_systematics(self, cb, ch):
        for name, systematic in self.systematics.items():
            syst_map = ch.SystMap("era", "bin")
            for year, value in systematic["values"].items():
                if isinstance(value, dict):
                    for region, region_value in value.items():
                        bins = [
                            self.bin_name(year, plane, region)
                            for plane in DEFAULT_PLANES
                        ]
                        syst_map = syst_map([year], bins, region_value)
                else:
                    bins = [
                        self.bin_name(year, plane, region)
                        for plane in DEFAULT_PLANES
                        for region in DEFAULT_REGIONS
                    ]
                    syst_map = syst_map([year], bins, value)
            cb.cp().signals().AddSyst(cb, name, systematic["type"], syst_map)

    def postprocess(self, path):
        lines = self.header_lines() + path.read_text(encoding="utf-8").splitlines()
        columns = self.process_columns(lines)
        lines.append("")
        lines.extend(self.signal_stat_lines(columns))
        lines.append("")
        lines.extend(self.rate_param_lines(self.bins()))
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def header_lines(self):
        lines = [
            f"# Signal sample: {self.signal.sample_name}",
            f"# Target ctau: {self.signal.target_ct:g} mm",
        ]
        if self.signal.model == "stop":
            lines.append(f"# Target BR: {self.signal.target_br:g}")
        lines.append(
            f"# Cuts:" + "\n"
            f"# A: MET >= {self.xcut:g}, ML >= {self.ycut:g} " + "\n"
            f"# B: {self.xlo:g} <= MET < {self.xcut:g}, ML >= {self.ycut:g} " + "\n"
            f"# C: MET >= {self.xcut:g}, {self.ylo:g} <= ML < {self.ycut:g} " + "\n"
            f"# D: {self.xlo:g} <= MET < {self.xcut:g}, {self.ylo:g} <= ML < {self.ycut:g}"
        )
        return lines

    def process_columns(self, lines):
        for idx, line in enumerate(lines[:-2]):
            fields = line.split()
            next_fields = lines[idx + 1].split()
            next_next_fields = lines[idx + 2].split()
            if (
                fields
                and next_fields
                and next_next_fields
                and fields[0] == "bin"
                and next_fields[0] == "process"
                and next_next_fields[0] == "process"
            ):
                return list(zip(fields[1:], next_fields[1:]))

    def signal_stat_lines(self, columns):
        lines = []
        for bin_name in self.bins():
            value = self.signal_rate(bin_name)
            error = self.signal_error(bin_name)
            if value <= 0 or error <= 0:
                continue
            events = int(round((value / error) ** 2))
            if events <= 0:
                continue
            alpha = value / events
            nuisance = f"stat_sig_{bin_name}"
            values = [
                f"{alpha:.6g}" if column_bin == bin_name and process == "sig" else "-"
                for column_bin, process in columns
            ]
            lines.append(
                f"{nuisance:<35} {'gmN':<7} {events:<8}"
                + "".join(f"{v:<18}" for v in values)
            )
        return lines

    def rate_param_lines(self, bins):
        lines = []
        for bin_name in bins:
            observation = self.observation(bin_name)
            nuisance = f"rate_{bin_name}"
            if bin_name.endswith("_A"):
                prefix = bin_name[:-1]
                value = f"(@0*@1/@2) rate_{prefix}B,rate_{prefix}C,rate_{prefix}D"
            else:
                value = f"{max(1e-6, observation):.6g}"
                value = f"{value:<10} {self.rate_param_range(observation)}"
            lines.append(f"{nuisance:<20} rateParam   {bin_name:<18} bkg   {value}")
        return lines

    def rate_param_range(self, n):
        sigma = math.sqrt(max(n, 0.0))
        low = max(1e-6, round(n - 50.0 * sigma, 0))
        high = round(100 + n + 50.0 * sigma, 0)
        return f"[{low:.6g},{high:.6g}]"


class DatacardMaker:
    def __init__(
        self,
        signals,
        data,
        output_dir,
        xcut,
        xlo,
        ycut,
        ylo,
        mode,
        stop_brs,
        c1n2_ctaus,
    ):
        self.signals = signals
        self.data = data
        self.output_dir = output_dir
        self.xcut = xcut
        self.xlo = xlo
        self.ycut = ycut
        self.ylo = ylo
        self.mode = mode
        self.stop_brs = stop_brs
        self.c1n2_ctaus = c1n2_ctaus

    def write(self):
        paths = []
        for signal, target_ct, target_br, datacard_name in self.targets():
            signal.reweight_to(target_ct, target_br)
            signal.datacard_name = datacard_name
            paths.append(
                Datacard(
                    signal,
                    self.data,
                    self.output_dir,
                    self.xcut,
                    self.xlo,
                    self.ycut,
                    self.ylo,
                    self.mode,
                ).write()
            )
        return paths

    def dryrun(self):
        targets = list(self.targets())
        print(f"output-dir: {self.output_dir}")
        print(f"planes: {' '.join(DEFAULT_PLANES)}")
        print(f"years: {' '.join(DEFAULT_YEARS)}")
        print(f"stop origin BR: {DEFAULT_STOP_BR:g}")
        print(f"target samples: {len(targets)}")
        for year in DEFAULT_YEARS:
            data_path = self.data.path(year)
            status = "ok" if data_path.exists() else "missing"
            print(f"data ROOT {year}: {data_path.relative_to(self.data.workdir)} [{status}]")
        for signal, target_ct, target_br, datacard_name in targets:
            print(
                f"datacard: {datacard_name}.txt  "
                f"source={signal.sample_name} "
                f"origin_ctau={signal.ct:g} "
                f"target_ctau={target_ct:g}"
            )

    def targets(self):
        for (model, mass, daughter_mass), signals_by_ct in self.signal_groups().items():
            if model == "stop":
                yield from self.stop_targets(mass, daughter_mass, signals_by_ct)
            if model == "C1N2":
                yield from self.c1n2_targets(mass, daughter_mass, signals_by_ct)

    def signal_groups(self):
        groups = {}
        for signal in self.signals:
            key = (signal.model, signal.M, signal.M2)
            groups.setdefault(key, {})[signal.ct] = signal
        return groups

    def stop_targets(self, mass, daughter_mass, signals_by_ct):
        dm = mass - daughter_mass
        for br in self.stop_brs:
            target_ct = stop_ctau_for_br(mass, dm, br)
            source_ct = choose_source_ctau(ALLOWED_STOP_SOURCE_CTAUS_BY_DM[dm], target_ct)
            datacard_name = (
                f"stop_M{mass}_{daughter_mass}_ct{number_label(target_ct)}"
                f"_BR{number_label(br)}"
            )
            yield signals_by_ct[source_ct], target_ct, br, datacard_name

    def c1n2_targets(self, mass, daughter_mass, signals_by_ct):
        for target_ct in self.c1n2_ctaus:
            source_ct = choose_source_ctau(signals_by_ct, target_ct)
            datacard_name = f"C1N2_M{mass}_{daughter_mass}_ct{number_label(target_ct)}"
            yield signals_by_ct[source_ct], target_ct, DEFAULT_STOP_BR, datacard_name


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--uniquedir",
        required=True,
        help=(
            f"Directory name below {DEFAULT_BASEDIR}. "
            "Absolute paths are also accepted."
        ),
    )
    parser.add_argument("--xcut", type=float, default=500.0)
    parser.add_argument("--xlo", type=float, default=250.0)
    parser.add_argument("--ycut", type=float, default=0.999)
    parser.add_argument("--ylo", type=float, default=0.80)
    parser.add_argument("--mode", choices=["Asimov", "observation"], default="Asimov")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--datacard-dir-name", default="reweighted_v2")
    parser.add_argument("--dryrun", action="store_true")
    parser.add_argument("--stop-br", nargs="+", type=float, default=DEFAULT_STOP_BRS)
    parser.add_argument("--c1n2-ctau", nargs="+", type=float, default=DEFAULT_C1N2_CTAUS)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    WORKDIR = workdir_from_uniquedir(args.uniquedir)
    output_dir = args.output_dir or WORKDIR / "datacards" / args.datacard_dir_name / args.mode

    signals, data = load_samples(WORKDIR, DEFAULT_YEARS)
    maker = DatacardMaker(
        signals,
        data,
        output_dir,
        args.xcut,
        args.xlo,
        args.ycut,
        args.ylo,
        args.mode,
        args.stop_br,
        args.c1n2_ctau,
    )
    if args.dryrun:
        maker.dryrun()
    else:
        maker.write()

    print(f"WORKDIR: {WORKDIR}")
    print(f"Signals: {len(signals)}")
    print(f"Data years: {', '.join(data.values)}")
