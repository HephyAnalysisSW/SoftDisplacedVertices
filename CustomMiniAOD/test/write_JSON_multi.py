#!/usr/bin/env python

import sys
import json
import optparse

import ROOT
ROOT.gROOT.SetBatch(True)

from DataFormats.FWLite import Lumis

def merge_ranges(lumis):
    """Convert a sorted list of lumis into merged lumi ranges."""
    if not lumis:
        return []

    merged = []
    start = lumis[0]
    end = lumis[0]

    for l in lumis[1:]:
        if l == end + 1:
            end = l
        else:
            merged.append([start, end])
            start = l
            end = l

    merged.append([start, end])
    return merged


def main(output_json, files):
    all_runs = {}

    print("Reading MiniAOD EDM files:")
    for f in files:
        print(f)
        try:
            lumis = Lumis(f)
        except Exception as e:
            print("  !! Failed to open with FWLite:", f)
            print("     Error:", e)
            continue

        # Loop over luminosity blocks
        print("Looping over lumis")
        for li in lumis:
            aux = li.aux()  # edm::LuminosityBlockAuxiliary
            run  = aux.run()
            lumi = aux.luminosityBlock()

            if run not in all_runs:
                all_runs[run] = set()
            all_runs[run].add(lumi)

    # Convert sets to merged ranges
    json_dict = {}
    for run in sorted(all_runs.keys()):
        lumis_sorted = sorted(all_runs[run])
        json_dict[run] = merge_ranges(lumis_sorted)

    # Write JSON
    with open(output_json, "w") as out:
        json.dump(json_dict, out, indent=2, sort_keys=True)

    print("\n Wrote cumulative JSON to:", output_json)
    print("  Runs processed:", len(json_dict))


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: writeJSON.py output.json input1.root [input2.root] ...")
        print("Wildcards: writeJSON.py output.json input_path/* ...")
        sys.exit(1)

    output_json = sys.argv[1]
    input_files = sys.argv[2:]

    main(output_json, input_files) 
