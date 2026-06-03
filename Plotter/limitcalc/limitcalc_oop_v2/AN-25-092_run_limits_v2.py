#!/usr/bin/env python3

import argparse

from limits import LimitRunner


def parse_args():
    parser = argparse.ArgumentParser(description="Run one Combine AsymptoticLimits job.")
    parser.add_argument("--datacard", required=True, help="Input datacard.")
    parser.add_argument("--limitdir", required=True, help="Base output directory for limits.")
    parser.add_argument("--debug", action="store_true", help="Show combine output.")
    return parser.parse_args()


def main():
    args = parse_args()
    LimitRunner(args.datacard, args.limitdir, debug=args.debug).run()


if __name__ == "__main__":
    main()
