#!/bin/bash

run_compareK(){

    OUTDIR=$HISTDIR/plots/datavMC/$1
    PDFDIR=$OUTDIR/pdf
    PNGDIR=$OUTDIR/png
    LOGPNGDIR=$OUTDIR/logpng

    mkdir -p $PDFDIR
    mkdir -p $PNGDIR
    mkdir -p $LOGPNGDIR


    python3 ../compare_data_new.py                                             \
    --data $DATA                                                               \
    --bkg  $TOP $QCD $WJETS $ZJETS                                             \
    --bkgnice  "TTbar" "QCD" "WJets" "ZJets"                                   \
    --output $OUTDIR                                                           \
    --dirs $1                                                                  \
    --ratio

    mv $OUTDIR/*.pdf            $PDFDIR
    mv $OUTDIR/*log.png         $LOGPNGDIR
    mv $OUTDIR/*.png            $PNGDIR
}

HISTDIR=/scratch-cbe/users/alikaan.gueven/AN_plots/checks_2023/check11_bpix

DATA=$HISTDIR/data/met_2023_hist.root
QCD=$HISTDIR/bkg/qcd_2023_hist.root
WJETS=$HISTDIR/bkg/wjets_2023_hist.root
ZJETS=$HISTDIR/bkg/zjets_2023_hist.root
TOP=$HISTDIR/bkg/top_2023_hist.root
# SIGNAL=$HISTDIR/sig/stop_M600_580_ct2_2018_hist.root


# Extract and process the names directly using a pipeline and a while-read loop
rootls -t $QCD                  | \
awk -F'"' '{print $2}'          | \
while IFS= read -r line;
do
    run_compareK $line
done


