#!/usr/bin/env python3
# Run Combine limits for one datacard.
# Run inside cmssw-el9.
#
# Example:
# python3 AN-25-092_run_limits_v3.py \
#   --datacard /path/to/datacards/Asimov/stop_M1000_980_ct2.txt \
#   --limitdir /path/to/limits/Asimov

import argparse

from limits import LimitRunner


def main():
    parser = argparse.ArgumentParser(description="Run one Combine AsymptoticLimits job.")
    parser.add_argument("--datacard", required=True, help="Input datacard.")
    parser.add_argument("--limitdir", required=True, help="Base output directory for limits.")
    parser.add_argument("--debug", action="store_true", help="Show combine output.")
    args = parser.parse_args()

    LimitRunner(args.datacard, args.limitdir, debug=args.debug).run()


if __name__ == "__main__":
    main()
