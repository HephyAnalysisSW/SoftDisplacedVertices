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

HISTDIR=/scratch-cbe/users/alikaan.gueven/AN_plots/ParT_hists/AN-25-092_ML_plots1

QCD=$HISTDIR/bkg17/qcd_2017_hist.root
WJETS=$HISTDIR/bkg17/wjets_2017_hist.root
ZJETS=$HISTDIR/bkg17/zjets_2017_hist.root
TOP=$HISTDIR/bkg17/top_2017_hist.root
SIGNAL=$HISTDIR/sig17/C1N2_M500_485_ct20_2017_hist.root



# Extract and process the names directly using a pipeline and a while-read loop
rootls -t "$QCD"                | \
awk -F'"' '{print $2}'          | \
while IFS= read -r line;
do
    echo "Processing directory: $line"
    run_compareK "$line"
done
