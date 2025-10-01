#!/bin/bash

run_compareK(){

    OUTDIR=$HISTDIR/plots/datavMC/$1
    PDFDIR=$OUTDIR/pdf
    PNGDIR=$OUTDIR/png
    LOGPNGDIR=$OUTDIR/logpng

    mkdir -p $PDFDIR
    mkdir -p $PNGDIR
    mkdir -p $LOGPNGDIR


    # python3 ../compare_data_new.py                                             \
    # --bkg  $TOP $QCD $WJETS $ZJETS                                             \
    # --bkgnice  "TTbar" "QCD" "WJets" "ZJets"                                   \
    # --output $OUTDIR                                                           \
    # --dirs $1                                                                  \
    # --ratio                                                                    \

    python3 ../compare_data_new.py                                             \
    --bkg  $TOP $QCD $WJETS $ZJETS                                             \
    --bkgnice  "TTbar" "QCD" "WJets" "ZJets"                                   \
    --signal  $SIGNAL                                                          \
    --signice  signal                                                          \
    --output $OUTDIR                                                           \
    --dirs $1                                                                  \
#     --norm                                                                     \

# python3 ../compare.py                                                            \
# --input $SIGNAL                                                                  \
# --dirs all_evt exhiML_evt                                                        \
# --nice all_evt exhiML_evt                                                        \
# --output $OUTDIR                                                                 \
# --scale


    mv $OUTDIR/*.pdf            $PDFDIR
    mv $OUTDIR/*log.png         $LOGPNGDIR
    mv $OUTDIR/*.png            $PNGDIR
}

HISTDIR=/scratch-cbe/users/alikaan.gueven/AN_plots/ParT_hists/SDVSecVtx_ParTScore

DATA=$HISTDIR/data/met_2018_hist.root
QCD=$HISTDIR/bkg/qcd_2018_hist.root
WJETS=$HISTDIR/bkg/wjets_2018_hist.root
ZJETS=$HISTDIR/bkg/zjets_2018_hist.root
TOP=$HISTDIR/bkg/top_2018_hist.root
SIGNAL=$HISTDIR/sig/stop_M600_585_ct20_2018_hist.root


# Extract and process the names directly using a pipeline and a while-read loop
rootls -t $QCD                  | \
awk -F'"' '{print $2}'          | \
while IFS= read -r line;
do
    echo "Processing directory: $line"
    run_compareK $line
done


