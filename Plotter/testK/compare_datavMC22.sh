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
    --ratio                                                                    \

#     python3 ../compare_data_new.py                                             \
#     --bkg  $TOP $QCD $WJETS $ZJETS                                             \
#     --bkgnice  "TTbar" "QCD" "WJets" "ZJets"                                   \
#     --signal  $SIGNAL                                                          \
#     --signice  "signal"                                                        \
#     --output $OUTDIR                                                           \
#     --dirs $1                                                                  \
#     --norm                                                                     \

    mv $OUTDIR/*.pdf            $PDFDIR
    mv $OUTDIR/*log.png         $LOGPNGDIR
    mv $OUTDIR/*.png            $PNGDIR
}

HISTDIR=/scratch-cbe/users/alikaan.gueven/AN_plots/checks_2022/check_1_ee

DATA=$HISTDIR/data/met_2022_hist.root
QCD=$HISTDIR/bkg/qcd_2022_hist.root
WJETS=$HISTDIR/bkg/wjets_2022_hist.root
ZJETS=$HISTDIR/bkg/zjets_2022_hist.root
TOP=$HISTDIR/bkg/top_2022_hist.root
SIGNAL=$HISTDIR/sig/stop_M1000_980_ct2_2018_hist.root


# Extract and process the names directly using a pipeline and a while-read loop
rootls -t $QCD                  | \
awk -F'"' '{print $2}'          | \
while IFS= read -r line;
do
    run_compareK $line
done


