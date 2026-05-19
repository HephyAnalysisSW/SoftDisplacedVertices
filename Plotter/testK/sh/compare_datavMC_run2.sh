#!/bin/bash

run_compareK(){

    LXPLUSDIR=$HISTDIR/plots/datavMC_lxplus/$1
    SCRATCHDIR=$HISTDIR/plots/datavMC/$1

    mkdir -p "$LXPLUSDIR" "$SCRATCHDIR/pdf" "$SCRATCHDIR/png" "$SCRATCHDIR/logpng"

    python3 ../compare_data_new.py                                             \
    --data $DATA                                                               \
    --bkg  $TOP $QCD $WJETS $ZJETS                                             \
    --signal $SIGNAL                                                           \
    --signice "unmatched sig."                                                 \
    --bkgnice  "TTbar" "QCD" "WJets" "ZJets"                                   \
    --output $LXPLUSDIR                                                        \
    --dirs $1                                                                  \
    --ratio                                                                    \
    --commands="h=h.Rebin(10)"
    # --commands="h=h.Rebin(5, '', array('d', [0.0, 0.1, 0.2, 0.3, 0.9, 1.0]))"


    rm -f "$LXPLUSDIR"/*_vs_*
    rm -f "$SCRATCHDIR/pdf"/*_vs_* "$SCRATCHDIR/png"/*_vs_* "$SCRATCHDIR/logpng"/*_vs_*

    cp "$LXPLUSDIR"/*.pdf "$SCRATCHDIR/pdf"
    cp "$LXPLUSDIR"/*log.png "$SCRATCHDIR/logpng"

    for png_file in "$LXPLUSDIR"/*.png;
    do
        [[ "$png_file" == *log.png ]] || cp "$png_file" "$SCRATCHDIR/png"
    done
}

HISTDIR=/scratch-cbe/users/alikaan.gueven/AN_plots/ParT_hists/AN-25-092_ML_plots3_data

DATA=$HISTDIR/data_run2/met_run2_hist.root
QCD=$HISTDIR/bkg_run2/qcd_run2_hist.root
WJETS=$HISTDIR/bkg_run2/wjets_run2_hist.root
ZJETS=$HISTDIR/bkg_run2/zjets_run2_hist.root
TOP=$HISTDIR/bkg_run2/top_run2_hist.root
SIGNAL=$HISTDIR/sig_run2/stop_M1000_985_ct20_run2_hist.root


# Extract and process the names directly using a pipeline and a while-read loop
rootls -t $QCD                  | \
awk -F'"' '{print $2}'          | \
while IFS= read -r line;
do
    run_compareK $line
done


