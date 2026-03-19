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
    --signal $SIGNAL                                                           \
    --signice "unmatched sig."                                                 \
    --bkgnice  "TTbar" "QCD" "WJets" "ZJets"                                   \
    --output $OUTDIR                                                           \
    --dirs $1                                                                  \
    --ratio                                                                    \

    mv $OUTDIR/*.pdf            $PDFDIR
    mv $OUTDIR/*log.png         $LOGPNGDIR
    mv $OUTDIR/*.png            $PNGDIR
}

HISTDIR=/scratch-cbe/users/alikaan.gueven/AN_plots/ParT_hists/vtx_PART_1111best_valloss_epoch_MET400_multiplane_dphi_test5

DATA=$HISTDIR/data/met_2018_hist.root
QCD=$HISTDIR/bkg/qcd_2018_hist.root
WJETS=$HISTDIR/bkg/wjets_2018_hist.root
ZJETS=$HISTDIR/bkg/zjets_2018_hist.root
TOP=$HISTDIR/bkg/top_2018_hist.root
SIGNAL=$HISTDIR/sig/C1N2ML_M500_485_ct200_2018_hist.root


# Extract and process the names directly using a pipeline and a while-read loop
rootls -t $QCD                  | \
awk -F'"' '{print $2}'          | \
while IFS= read -r line;
do
    run_compareK $line
done


