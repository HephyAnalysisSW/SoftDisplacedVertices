#!/usr/bin/env python3
# Create all signal-sample datacards for one MET/ML threshold pair.
# Run inside cmssw-el9.
#
# Example:
# python3 AN-25-092_make_multiplane_datacards_v3.py \
#   --histdir /scratch-cbe/users/alikaan.gueven/AN_plots/ParT_hists/AN-25-092_ML_plots_limitcalc_merge_w_Ang_v3 \
#   --xcut 350 --ycut 0.999 \
#   --output-dir /scratch-cbe/users/alikaan.gueven/AN_plots/ParT_hists/AN-25-092_ML_plots_limitcalc_merge_w_Ang_v3/ABCDscan/MET350_ML0p999/datacards/Asimov


# Example:
# python3 AN-25-092_make_multiplane_datacards_v3.py --data --mode Asimov --xcut 600 --ycut 0.9982 --output-dir .
# combine C1N2_M200_195_ct20.txt -M AsymptoticLimits --rMin 0 --rMax 20 --run blind
# combine C1N2_M200_195_ct20.txt -M HybridNew --LHCmode LHC-limits -T 500 --saveToys --saveHybridResult -v 1
# combine C1N2_M200_195_ct20.txt -M HybridNew --LHCmode LHC-limits -T 5000 -v 1 --saveToys --saveHybridResult --fork 10

import argparse
from pathlib import Path

from datacards import AnalysisConfig, DatacardGenerator, DEFAULT_HISTDIR, RunOptions


def parse_args():
    parser = argparse.ArgumentParser(
        description="Create CombineHarvester ABCD datacards from a plotter unique directory."
    )
    parser.add_argument("--xcut", type=float, default=350.0, help="MET threshold. Default: 350.")
    parser.add_argument("--xlo", type=float, default=250.0, help="Lower MET threshold. Default: 250.")
    parser.add_argument("--ycut", type=float, default=0.999, help="ML score threshold. Default: 0.999.")
    parser.add_argument("--ylo", type=float, default=0.80, help="Lower ML score threshold. Default: 0.80.")
    parser.add_argument("--histdir", type=Path, default=DEFAULT_HISTDIR, help="Plotter unique directory.")
    parser.add_argument("--datacard-dir-name", default="test", help="Directory below <histdir>/datacards.")
    parser.add_argument("--output-dir", type=Path, default=None, help="Exact datacard output directory.")
    parser.add_argument("--mode", choices=["Asimov", "observation"], default="Asimov", help="Datacard mode.")
    parser.add_argument("--data", action="store_true", help="Use data histograms as observation source.")
    return parser.parse_args()


def main():
    args = parse_args()

    # This script is run inside cmssw-el9, either manually or through
    # submit_limitcalc.sh from a job_ids.json entry.
    options = RunOptions(
        xcut=args.xcut,
        xlo=args.xlo,
        ycut=args.ycut,
        ylo=args.ylo,
        histdir=args.histdir,
        output_dir=args.output_dir,
        datacard_dir_name=args.datacard_dir_name,
        mode=args.mode,
        use_data=args.data,
    )

    generator = DatacardGenerator(AnalysisConfig(), options)
    # generator.generate_sample('C1N2_M200_195_ct20')
    generator.generate_all()


if __name__ == "__main__":
    main()
