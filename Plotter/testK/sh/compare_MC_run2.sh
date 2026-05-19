#!/bin/bash

run_compareK(){

    LXPLUSDIR=$HISTDIR/plots/MC_lxplus/$1
    MCDIR=$HISTDIR/plots/MC/$1

    mkdir -p "$LXPLUSDIR" "$MCDIR/pdf" "$MCDIR/png" "$MCDIR/logpng"


    python3 ../compare_data_new.py                                             \
    --bkg  "$TOP" "$QCD" "$WJETS" "$ZJETS"                                     \
    --bkgnice  "TTbar" "QCD" "WJets" "ZJets"                                   \
    --signal  "$SIGNAL"                                                        \
    --signice  signal                                                          \
    --output "$LXPLUSDIR"                                                      \
    --dirs "$1"                                                                \
    --norm                                                                    

    rm -f "$LXPLUSDIR"/*_vs_*
    rm -f "$MCDIR/pdf"/*_vs_* "$MCDIR/png"/*_vs_* "$MCDIR/logpng"/*_vs_*

    cp "$LXPLUSDIR"/*.pdf "$MCDIR/pdf"
    cp "$LXPLUSDIR"/*log.png "$MCDIR/logpng"

    for png_file in "$LXPLUSDIR"/*.png;
    do
        [[ "$png_file" == *log.png ]] || cp "$png_file" "$MCDIR/png"
    done
}

HISTDIR=/scratch-cbe/users/alikaan.gueven/AN_plots/ParT_hists/AN-25-092_ML_inputs_v2

QCD=$HISTDIR/bkg_run2/qcd_run2_hist.root
WJETS=$HISTDIR/bkg_run2/wjets_run2_hist.root
ZJETS=$HISTDIR/bkg_run2/zjets_run2_hist.root
TOP=$HISTDIR/bkg_run2/top_run2_hist.root
SIGNAL=$HISTDIR/sig_run2/stop_M1000_985_ct20_run2_hist.root



# Extract and process the names directly using a pipeline and a while-read loop
rootls -t "$QCD"                | \
awk -F'"' '{print $2}'          | \
while IFS= read -r line;
do
    echo "Processing directory: $line"
    run_compareK "$line"
done
