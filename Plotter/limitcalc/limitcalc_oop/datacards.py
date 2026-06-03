from ctypes import c_double
import getpass
from pathlib import Path
import math


DEFAULT_YEARS = (
    "2017",
    "2018",
    "2022Pre",
    "2022Post",
    "2023Pre",
    "2023Post",
    "2024",
)
DEFAULT_PLANES = ("GT1", "GT2", "GT3")
DEFAULT_REGIONS = ("A", "B", "C", "D")
DEFAULT_SCRATCH_BASE = Path(f"/scratch-cbe/users/{getpass.getuser()}/AN_plots/ParT_hists")
DEFAULT_HISTDIR = DEFAULT_SCRATCH_BASE / "AN-25-092_ML_plots_limitcalc_merge_w_Ang_v3"
SYSTEMATICS_PATH = Path(__file__).with_name("systematics_sig.yaml")


class DatacardInputs:
    def __init__(self):
        # Keep the analysis naming rules in one place. Most bugs in these
        # scripts come from mismatched file, directory, or bin names.
        self.years = DEFAULT_YEARS
        self.planes = DEFAULT_PLANES
        self.regions = DEFAULT_REGIONS
        self.systematics_path = SYSTEMATICS_PATH

    def background_file_name(self, year):
        return f"bkg_{year}_hist.root"

    def data_file_name(self, year):
        return f"data_{year}_hist.root"

    def plane_hist_name(self, plane):
        return f"{plane}_evt/MET_pt_corr_vs_leadingvtx_MLscore"

    def signal_sample_name(self, path):
        stem = path.name.removesuffix(".root").removesuffix("_hist")
        parts = stem.split("_")
        return "_".join(parts[:-1]) if parts[-1] in self.years else stem

    def signal_path(self, histdir, sample_name, year):
        sig_dir = histdir / f"sig_{year}"
        matches = sorted(sig_dir.glob(f"{sample_name}_*_hist.root"))
        if len(matches) == 1:
            return matches[0]
        if matches:
            raise ValueError(f"Multiple signal files match {sample_name} in {sig_dir}: {matches}")
        return sig_dir / f"{sample_name}_hist.root"

    def background_path(self, histdir, year):
        return histdir / f"bkg_{year}" / self.background_file_name(year)

    def data_path(self, histdir, year):
        return histdir / f"data_{year}" / self.data_file_name(year)

    def bin_name(self, year, plane, region):
        return f"y{year}_{plane}_{region}"


class RunOptions:
    def __init__(
        self,
        xcut=350.0,
        xlo=250.0,
        ycut=0.999,
        ylo=0.80,
        histdir=DEFAULT_HISTDIR,
        output_dir=None,
        datacard_dir_name="test",
        mode="Asimov",
        use_data=False,
    ):
        self.xcut = xcut
        self.xlo = xlo
        self.ycut = ycut
        self.ylo = ylo
        self.histdir = histdir.expanduser()
        self.output_dir = output_dir.expanduser() if output_dir else None
        self.datacard_dir_name = datacard_dir_name
        self.mode = mode
        self.use_data = use_data

    def observation_source(self):
        if self.use_data:
            return "data"
        return "bkg"

    def datacard_output_dir(self):
        if self.output_dir:
            return self.output_dir
        return self.histdir / "datacards" / self.datacard_dir_name / self.mode


class RootFile:
    def __init__(self, path, label):
        self.path = path
        self.label = label
        self.file = None

    def open(self):
        import ROOT

        # ROOT returns a zombie file instead of raising for some open failures.
        self.file = ROOT.TFile.Open(str(self.path))
        if not self.file or self.file.IsZombie():
            raise FileNotFoundError(f"Could not open {self.label} ROOT file: {self.path}")

    def close(self):
        if self.file:
            self.file.Close()
            self.file = None

    def get_hist(self, hist_name):
        hist = self.file.Get(hist_name)
        if not hist:
            raise KeyError(f"Missing histogram '{hist_name}' in {self.path}")
        return hist


class RegionIntegrator:
    def __init__(self, datacard_inputs, options):
        self.datacard_inputs = datacard_inputs
        self.options = options

    def integrate(self, hist, hist_name):
        # A is the signal region. B, C, and D are the control regions used for
        # the ABCD transfer factor B*C/D.
        xbin = hist.GetXaxis().FindBin(self.options.xcut)
        xlo_bin = hist.GetXaxis().FindBin(self.options.xlo)
        if xlo_bin >= xbin:
            raise ValueError(
                f"--xlo must be smaller than --xcut for {hist_name}: "
                f"xlo={self.options.xlo}, xcut={self.options.xcut}"
            )

        ybin = hist.GetYaxis().FindBin(self.options.ycut)
        ylo_bin = hist.GetYaxis().FindBin(self.options.ylo)
        if ylo_bin >= ybin:
            raise ValueError(
                f"--ylo must be smaller than --ycut for {hist_name}: "
                f"ylo={self.options.ylo}, ycut={self.options.ycut}"
            )

        last_x_bin = hist.GetNbinsX() + 1
        last_y_bin = hist.GetNbinsY() + 1
        ranges = {
            "A": (xbin, last_x_bin, ybin, last_y_bin),
            "B": (xlo_bin, xbin - 1, ybin, last_y_bin),
            "C": (xbin, last_x_bin, ylo_bin, ybin - 1),
            "D": (xlo_bin, xbin - 1, ylo_bin, ybin - 1),
        }

        values = {}
        errors = {}
        for region in self.datacard_inputs.regions:
            bx1, bx2, by1, by2 = ranges[region]
            err = c_double(0.0)
            values[region] = hist.IntegralAndError(bx1, bx2, by1, by2, err)
            errors[region] = err.value
        return values, errors


class DatacardGenerator:
    def __init__(self, datacard_inputs, options):
        self.datacard_inputs = datacard_inputs
        self.options = options
        self.histdir = options.histdir
        self.outdir = options.datacard_output_dir()
        self.systematics = self.load_systematics()
        self.integrator = RegionIntegrator(datacard_inputs, options)
        self.current_sample_name = None

    def load_systematics(self):
        import yaml

        return yaml.safe_load(self.datacard_inputs.systematics_path.read_text(encoding="utf-8"))

    def discover_samples(self):
        sample_names = set()
        for year in self.datacard_inputs.years:
            sig_dir = self.histdir / f"sig_{year}"
            for path in sorted(sig_dir.glob("*_hist.root")):
                sample_names.add(self.datacard_inputs.signal_sample_name(path))
        return sorted(sample_names)

    def generate_all(self):
        self.outdir.mkdir(parents=True, exist_ok=True)
        written = []
        for sample_name in self.discover_samples():
            written.append(self.generate_sample(sample_name))
        return written

    def generate_sample(self, sample_name):
        import CombineHarvester.CombineTools.ch as ch

        self.current_sample_name = sample_name
        try:
            # One CombineHarvester object collects all years, planes, and ABCD
            # bins for this signal sample.
            cb = ch.CombineHarvester()
            observations = {}
            rates = {}
            signal_mc_stats = {}
            category_id = 1

            for year in self.datacard_inputs.years:
                categories, category_id = self.fill_year(
                    year,
                    category_id,
                    observations,
                    rates,
                    signal_mc_stats,
                )
                cb.AddObservations(["mass"], ["AN-25-092"], [year], ["channel"], categories)
                cb.AddProcesses(["mass"], ["AN-25-092"], [year], ["channel"], ["sig"], categories, True)
                cb.AddProcesses(["mass"], ["AN-25-092"], [year], ["channel"], ["bkg"], categories, False)

            cb.ForEachObs(lambda obs: obs.set_rate(observations[obs.bin()]))
            cb.ForEachProc(lambda proc: proc.set_rate(rates[(proc.bin(), proc.process())]))
            self.add_signal_systematics(cb, ch)

            outfile = self.outdir / f"{sample_name}.txt"
            self.write_datacard(cb, outfile, sample_name)
            self.postprocess_datacard(outfile, observations, signal_mc_stats)
            print(f"Wrote all-year datacard to: {outfile}")
            return outfile
        finally:
            self.current_sample_name = None

    def fill_year(self, year, category_id, observations, rates, signal_mc_stats):
        categories = []
        root_files = self.open_root_files(self.current_sample_name, year)

        try:
            for plane in self.datacard_inputs.planes:
                tables = self.read_plane_tables(root_files, plane)
                for region in self.datacard_inputs.regions:
                    bin_name = self.datacard_inputs.bin_name(year, plane, region)
                    categories.append((category_id, bin_name))
                    category_id += 1
                    self.fill_bin(bin_name, region, tables, observations, rates, signal_mc_stats)
        finally:
            self.close_root_files(root_files)

        return categories, category_id

    def open_root_files(self, sample_name, year):
        root_files = {
            "sig": RootFile(self.datacard_inputs.signal_path(self.histdir, sample_name, year), "signal"),
            "bkg": RootFile(self.datacard_inputs.background_path(self.histdir, year), "background"),
        }
        if self.options.use_data:
            root_files["data"] = RootFile(self.datacard_inputs.data_path(self.histdir, year), "data")

        opened = []
        try:
            # Open all files for this year together so each plane reads from the
            # same signal/background/data source.
            for root_file in root_files.values():
                root_file.open()
                opened.append(root_file)
        except Exception:
            for root_file in opened:
                root_file.close()
            raise

        return root_files

    def close_root_files(self, root_files):
        for root_file in root_files.values():
            root_file.close()

    def read_plane_tables(self, root_files, plane):
        hist_name = self.datacard_inputs.plane_hist_name(plane)
        tables = {}
        for label, root_file in root_files.items():
            hist = root_file.get_hist(hist_name)
            values, errors = self.integrator.integrate(hist, hist_name)
            tables[label] = {"values": values, "errors": errors}
        return tables

    def fill_bin(self, bin_name, region, tables, observations, rates, signal_mc_stats):
        source = tables[self.options.observation_source()]["values"]
        observations[bin_name] = round(max(self.observation(region, source), 0), 4)

        # The background rate is controlled by rateParams below. Its nominal
        # Combine rate is therefore fixed to 1.
        rates[(bin_name, "sig")] = round(tables["sig"]["values"][region], 4)
        rates[(bin_name, "bkg")] = 1.0
        self.add_signal_mc_stat(bin_name, region, tables["sig"], signal_mc_stats)

    def observation(self, region, values):
        if self.options.mode == "Asimov" and region == "A":
            if values["D"] == 0:
                return 0.0
            # Blind Asimov A uses the ABCD prediction, not the observed A yield.
            return values["B"] * values["C"] / values["D"]
        return values[region]

    def add_signal_mc_stat(self, bin_name, region, sig_table, signal_mc_stats):
        sig_yield = sig_table["values"][region]
        sig_error = sig_table["errors"][region]
        if sig_yield <= 0.0 or sig_error <= 0.0:
            return

        n_events = int(round((sig_yield / sig_error) ** 2))
        if n_events <= 0:
            return

        # Convert weighted MC yield/error into the gmN form expected by Combine.
        signal_mc_stats[f"stat_sig_{bin_name}"] = {
            "bin": bin_name,
            "n": n_events,
            "alpha": sig_yield / n_events,
        }

    def add_signal_systematics(self, cb, ch):
        for sys_name, systematic in self.systematics.items():
            syst_map = ch.SystMap("era", "bin")
            for year in self.datacard_inputs.years:
                year_value = systematic["values"].get(year)
                if year_value is None:
                    continue
                if isinstance(year_value, dict):
                    for region, value in year_value.items():
                        bins = [
                            self.datacard_inputs.bin_name(year, plane, region)
                            for plane in self.datacard_inputs.planes
                        ]
                        syst_map = syst_map([year], bins, value)
                else:
                    bins = [
                        self.datacard_inputs.bin_name(year, plane, region)
                        for plane in self.datacard_inputs.planes
                        for region in self.datacard_inputs.regions
                    ]
                    syst_map = syst_map([year], bins, year_value)
            cb.cp().signals().AddSyst(cb, sys_name, systematic["type"], syst_map)

    def write_datacard(self, cb, outfile, sample_name):
        outfile.parent.mkdir(parents=True, exist_ok=True)

        # CombineHarvester requires a ROOT file path even for this counting
        # datacard. Write it as a hidden placeholder and remove it afterwards.
        root_placeholder = outfile.parent / f".{sample_name}.root"
        cb.WriteDatacard(str(outfile), str(root_placeholder))
        if root_placeholder.exists():
            root_placeholder.unlink()

    def postprocess_datacard(self, outfile, observations, signal_mc_stats):
        # CombineHarvester writes a shape-based skeleton. This analysis uses a
        # counting card, so the shape lines are removed and ABCD rate parameters
        # are appended explicitly.


        lines = self.strip_shape_lines(outfile)

        if signal_mc_stats:
            columns = self.process_columns(lines)
            lines.append("")
            for nuisance, stat in signal_mc_stats.items():
                lines.append(self.signal_mc_stat_line(nuisance, stat, columns))

        lines.append("")
        for bin_name, observation in observations.items():
            lines.append(self.rate_param_line(bin_name, observation))

        outfile.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def strip_shape_lines(self, outfile):
        lines = []
        previous_separator = False
        for line in outfile.read_text(encoding="utf-8").splitlines():
            # if line.startswith("shapes "):
            #     continue
            # is_separator = line.startswith("----")
            # if is_separator and previous_separator:
            #     continue
            lines.append(line)
            # previous_separator = is_separator
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
        raise ValueError("Could not find the process table in the datacard.")

    def signal_mc_stat_line(self, nuisance, stat, columns):
        values = [
            f"{stat['alpha']:.6g}" if bin_name == stat["bin"] and process == "sig" else "-"
            for bin_name, process in columns
        ]
        values = "".join(f"{value:<15} " for value in values).rstrip()
        return f"{nuisance:<35} {'gmN':<7} {stat['n']:<8} {values}"

    # def rate_param_line(self, bin_name, observation):
    #     nuisance = f"rate_{bin_name}"
    #     if bin_name.endswith("_A"):
    #         prefix = bin_name[:-1]
    #         value = f"(@0*@1/@2) rate_{prefix}B,rate_{prefix}C,rate_{prefix}D"
    #     else:
    #         value = observation
    #     return f"{nuisance:<20} rateParam   {bin_name:<18} bkg   {value}"

    def rate_param_range(self, n):
        n = float(n)
        sigma = math.sqrt(max(n, 0.0))

        lo = max(1e-6, round(n - 50.0 * sigma, 0))
        hi =     round(100 + n + 50.0 * sigma, 0)

        return f"[{lo:.6g},{hi:.6g}]"

    def rate_param_line(self, bin_name, observation):
        nuisance = f"rate_{bin_name}"

        if bin_name.endswith("_A"):
            prefix = bin_name[:-1]
            value = f"(@0*@1/@2) rate_{prefix}B,rate_{prefix}C,rate_{prefix}D"
            return f"{nuisance:<20} rateParam   {bin_name:<18} bkg   {value}"

        bounds = self.rate_param_range(observation)
        value = f"{max(1e-6, observation):.6g}"

        return f"{nuisance:<20} rateParam   {bin_name:<18} bkg   {value:<12} {bounds}"
