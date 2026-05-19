# Usage:
# python3 AN-25-092_make_multiplane_datacards_ch_v2.py
# python3 AN-25-092_make_multiplane_datacards_ch_v2.py --xcut 350 --ycut 0.999

import argparse
import getpass
import tempfile
from ctypes import c_double
from pathlib import Path

import CombineHarvester.CombineTools.ch as ch
import ROOT
import yaml


USER = getpass.getuser()

if USER == "alikaan.gueven":
    OUTDIR = Path("/scratch-cbe/users/alikaan.gueven/AN_plots/ParT_hists/AN-25-092_ML_plots_limitcalc_v3")
    SYSTEMATICS_PATH = Path(__file__).with_name("systematics_sig.yaml")

    PLANES = ["SP1", "SP2", "SP3"]
    REGIONS = ["A", "B", "C", "D"]
    YEARS = [
        "2017",
        "2018",
        "2022Pre",
        "2022Post",
        "2023Pre",
        "2023Post",
        "2024",
    ]
    SIG_DIR_BY_YEAR = {year: f"sig_{year}" for year in YEARS}
    BKG_DIR_BY_YEAR = {year: f"bkg_{year}" for year in YEARS}
    DATA_DIR_BY_YEAR = {year: f"data_{year}" for year in YEARS}
    SIGNAL_FILE_YEAR_BY_YEAR = {year: "2018" for year in YEARS}
    DATACARD_DIR_NAME = "all_years"

    def file_year_token(year):
        return year

    def signal_file_year_token(year):
        return SIGNAL_FILE_YEAR_BY_YEAR[year]

    def signal_file_name(sample_name, year):
        return f"{sample_name}_{signal_file_year_token(year)}_hist.root"

    def background_file_name(year):
        return f"bkg_{file_year_token(year)}_hist.root"

    def data_file_name(year):
        return f"data_{file_year_token(year)}_hist.root"

    def plane_hist_name(plane):
        return f"{plane}_evt/MET_pt_corr_vs_{plane}_Max_ML_score"

SIGNAL_SYSTEMATICS = yaml.safe_load(SYSTEMATICS_PATH.read_text(encoding="utf-8"))





# ------------------------------------------------------------------------------------------------------


parser = argparse.ArgumentParser(
    description="Create CombineHarvester ABCD datacards from a plotter unique directory."
)
parser.add_argument(
    "--xcut",
    type=float,
    default=350.0,
    help="MET threshold. Default: 350.",
)
parser.add_argument(
    "--ycut",
    type=float,
    default=0.999,
    help="ML score threshold. Default: 0.999.",
)
parser.add_argument(
    "--mode",
    choices=["Asimov", "observation"],
    default="Asimov",
    help="Datacard mode. Default: Asimov.",
)
parser.add_argument(
    "--data",
    action="store_true",
    help="Use data histograms instead of MC background as the observation source.",
)
args = parser.parse_args()
observation_source = "data" if args.data else "bkg"

histdir = OUTDIR

sample_names = set()
for year in YEARS:
    sig_dir = SIG_DIR_BY_YEAR[year]
    sig_suffix = f"_{signal_file_year_token(year)}_hist.root"
    for path in sorted((histdir / sig_dir).glob(f"*{sig_suffix}")):
        if path.name.endswith(sig_suffix):
            sample_names.add(path.name[:-len(sig_suffix)])

outdir = histdir / "datacards" / DATACARD_DIR_NAME / args.mode
outdir.mkdir(parents=True, exist_ok=True)

for sample_name in sorted(sample_names):
    observations = {}
    rates = {}
    cb = ch.CombineHarvester()
    category_id = 1

    for datacard_year in YEARS:
        sig_dir = SIG_DIR_BY_YEAR[datacard_year]
        bkg_dir = BKG_DIR_BY_YEAR[datacard_year]
        data_dir = DATA_DIR_BY_YEAR[datacard_year]
        year_label = f"y{datacard_year}"

        sig_file = histdir / sig_dir / signal_file_name(sample_name, datacard_year)
        bkg_file = histdir / bkg_dir / background_file_name(datacard_year)
        data_file = histdir / data_dir / data_file_name(datacard_year)
        sig_root = ROOT.TFile.Open(str(sig_file))
        bkg_root = ROOT.TFile.Open(str(bkg_file))
        data_root = ROOT.TFile.Open(str(data_file)) if args.data else None

        categories = []
        for plane in PLANES:
            hist_name = plane_hist_name(plane)
            tables = {}

            hist_sources = [("sig", sig_root.Get(hist_name)), ("bkg", bkg_root.Get(hist_name))]
            if args.data:
                hist_sources.append(("data", data_root.Get(hist_name)))

            for label, hist in hist_sources:
                xbin = hist.GetXaxis().FindBin(args.xcut)
                ybin = hist.GetYaxis().FindBin(args.ycut)
                last_x_bin = hist.GetNbinsX() + 1
                last_y_bin = hist.GetNbinsY() + 1
                ranges = {
                    "A": (xbin, last_x_bin, ybin, last_y_bin),
                    "B": (1, xbin - 1, ybin, last_y_bin),
                    "C": (xbin, last_x_bin, 1, ybin - 1),
                    "D": (1, xbin - 1, 1, ybin - 1),
                }

                tables[label] = {}
                for region, (bx1, bx2, by1, by2) in ranges.items():
                    err = c_double(0.0)
                    tables[label][region] = hist.IntegralAndError(bx1, bx2, by1, by2, err)

            for region in REGIONS:
                bin_name = f"{year_label}_{plane}_{region}"
                categories.append((category_id, bin_name))
                category_id += 1
                if args.mode == "Asimov" and region == "A":
                    source = tables[observation_source]
                    observation = source["B"] * source["C"] / source["D"] if source["D"] else 0.0
                else:
                    observation = tables[observation_source][region]
                observations[bin_name] = round(max(observation, 0), 4)
                rates[(bin_name, "sig")] = round(tables["sig"][region], 4)
                rates[(bin_name, "bkg")] = 1.0

        sig_root.Close()
        bkg_root.Close()
        if data_root:
            data_root.Close()

        cb.AddObservations(["mass"], ["AN-25-092"], [datacard_year], ["channel"], categories)
        cb.AddProcesses(["mass"], ["AN-25-092"], [datacard_year], ["channel"], ["sig"], categories, True)
        cb.AddProcesses(["mass"], ["AN-25-092"], [datacard_year], ["channel"], ["bkg"], categories, False)

    cb.ForEachObs(lambda obs: obs.set_rate(observations[obs.bin()]))
    cb.ForEachProc(lambda proc: proc.set_rate(rates[(proc.bin(), proc.process())]))

    for sys_name, systematic in SIGNAL_SYSTEMATICS.items():
        syst_map = ch.SystMap("era", "bin")
        for year in YEARS:
            year_value = systematic["values"].get(year)
            if year_value is None: # skip missing years, e.g. lumi_13TeV_151617 uncertainty
                continue
            if isinstance(year_value, dict):
                for region, value in year_value.items():
                    bins = [f"y{year}_{plane}_{region}" for plane in PLANES]
                    syst_map = syst_map([year], bins, value)
            else:
                bins = [
                    f"y{year}_{plane}_{region}"
                    for plane in PLANES
                    for region in REGIONS
                ]
                syst_map = syst_map([year], bins, year_value)
        cb.cp().signals().AddSyst(cb, sys_name, systematic["type"], syst_map)

    outfile = outdir / f"{sample_name}.txt"

    # CombineHarvester requires a ROOT-file argument even for this counting card.
    # Put it in a temporary directory so only the text datacard remains.
    with tempfile.TemporaryDirectory() as tmpdir:
        cb.WriteDatacard(str(outfile), str(Path(tmpdir) / f"{sample_name}.root"))

    # Remove CombineHarvester's placeholder shape directives.
    # Collapse the double separator left behind after those lines are removed.
    lines = []
    previous_separator = False
    for line in outfile.read_text(encoding="utf-8").splitlines():
        if line.startswith("shapes "):
            continue
        is_separator = line.startswith("----")
        if is_separator and previous_separator:
            continue
        lines.append(line)
        previous_separator = is_separator

    # Add the per-year ABCD background model. B, C, and D are free rate parameters;
    # A is constrained by the transfer factor B*C/D in the same year and plane.
    lines.append("")
    for bin_name in observations:
        nuisance = f"rate_{bin_name}"
        if bin_name.endswith("_A"):
            prefix = bin_name[:-1]
            value = f"(@0*@1/@2) rate_{prefix}B,rate_{prefix}C,rate_{prefix}D"
        else:
            value = observations[bin_name]
        lines.append(f"{nuisance:<20} rateParam   {bin_name:<18} bkg   {value}")

    outfile.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote all-year datacard to: {outfile}")
