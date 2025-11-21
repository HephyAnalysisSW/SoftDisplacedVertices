#!/bin/bash

run_compareK(){
    process=wjets

    HISTDIR=/scratch-cbe/users/alikaan.gueven/AN_plots/checks_2023/2023v2018_v2
    OUTDIR=$HISTDIR/plots/${process}_comparisons/$1
    PDFDIR=$OUTDIR/pdf
    PNGDIR=$OUTDIR/png
    LOGPNGDIR=$OUTDIR/logpng

    mkdir -p $PDFDIR
    mkdir -p $PNGDIR
    mkdir -p $LOGPNGDIR


    python3 ../compareK.py                                                     \
    --data $HISTDIR/bkg/${process}_2018_hist.root                              \
    --bkg  $HISTDIR/bkg/${process}_2023_hist.root                              \
    --datanice ${process}_2018                                                 \
    --bkgnice  ${process}_2023                                                 \
    --output $OUTDIR                                                           \
    --dirs $1                                                                  \
    --ratio                                                                    \
    --norm

    mv $OUTDIR/*.pdf            $PDFDIR
    mv $OUTDIR/*log.png         $LOGPNGDIR
    mv $OUTDIR/*.png            $PNGDIR
}


# Extract and process the names directly using a pipeline and a while-read loop
rootls -t /scratch-cbe/users/alikaan.gueven/AN_plots/checks_2023/2023v2018_v2/bkg/qcd_2018_hist.root | \
awk -F'"' '{print $2}'                                                                               | \
while IFS= read -r line;
do
    run_compareK $line
done


