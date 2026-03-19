import glob
import re
import os
from collections import defaultdict

# Match all relevant files
files = glob.glob("/scratch-cbe/users/alikaan.gueven/AN_plots/ParT_hists/vtx_2018_v11/sig/stop_M*_ct*_2018_hist*.root")

# Dictionary to group files by their common prefix
groups = defaultdict(list)

# Regular expression to extract the group key (everything before _hist...)
pattern = re.compile(r"(stop_M\d+_\d+_ct\d+_2018)_hist\d+\.root")

for f in files:
    match = pattern.match(os.path.basename(f))
    if match:
        key = match.group(1)  # e.g., "stop_M600_585_ct20_2018"
        groups[key].append(f)

# Print grouped files
for key, group in groups.items():
    print(f"\nGroup: {key}")
    for f in group:
        print(f"  {f}")