#!/bin/bash
# Extract and process the names directly using a pipeline and a while-read loop
rootls -t /scratch-cbe/users/alikaan.gueven/AN_plots/checks_2023/2023v2018_v2/bkg/qcd_2018_hist.root | \
awk -F'"' '{print $2}'                                                                               | \
while IFS= read -r s;
do
    echo "Processing: $s"
done

