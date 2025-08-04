#!/usr/bin/env python3
"""
Quick check of the IsoMu24 trigger bit in EDM/ROOT files (AOD, MiniAOD, etc.)

Prints run:lumi:event and a 0/1 flag (1 = passed).
At the end, prints the total number of events and the number that passed.
"""

import sys
from DataFormats.FWLite import Events, Handle
import ROOT

if len(sys.argv) < 2:
    sys.exit("Usage:  python checkIsoMu24.py <file1.root> [file2.root ...]")

files = sys.argv[1:]

# --- Handles --------------------------------------------------------------
trig_handle      = Handle("edm::TriggerResults")
trig_label       = ("TriggerResults", "", "HLT")   # process name = HLT (original trigger)

# --- First event: find the bit index for HLT_IsoMu24_* --------------------
events = Events(files)
events.toBegin()
events.getByLabel(trig_label, trig_handle)
trigres = trig_handle.product()
names   = events.object().triggerNames(trigres)

# exact version inside the file (e.g. HLT_IsoMu24_v12)
pathname = next((n for n in names.triggerNames() if n.startswith("HLT_IsoMu24_v")), None)
if pathname is None:
    sys.exit("Path HLT_IsoMu24_v* not found in TriggerResults")

idx = names.triggerIndex(pathname)
print("Found {} at bit index {}".format(pathname, idx))

# --- Loop over events -----------------------------------------------------
n_tot = 0
n_pass = 0

for ev in events:
    ev.getByLabel(trig_label, trig_handle)
    trigres = trig_handle.product()
    fired   = trigres.accept(idx)
    n_tot  += 1
    n_pass += fired
    print ev.object().id().run(), ev.object().luminosityBlock(), ev.object().id().event(), fired
    # print("{ev.object().id().run()}:{ev.object().luminosityBlock()}:{ev.object().id().event()}  {int(fired)}")

# print(f"\nSummary: {n_pass}/{n_tot} events pass {pathname}")
