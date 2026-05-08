#!/bin/bash

run_compareK(){

    OUTDIR=$HISTDIR/plots/data_years/$1
    PDFDIR=$OUTDIR/pdf
    PNGDIR=$OUTDIR/png

    mkdir -p $PDFDIR
    mkdir -p $PNGDIR

    python3 ../compare.py                                                    \
    --input $DATA17 $DATA18 $DATA22PRE $DATA22POST $DATA23PRE $DATA23POST $DATA24 \
    --nice 2017 2018 2022Pre 2022Post 2023Pre 2023Post 2024                 \
    --output $OUTDIR                                                         \
    --dirs $1                                                                \
    # --scale

    mv $OUTDIR/*.pdf            $PDFDIR
    mv $OUTDIR/*.png            $PNGDIR
}

HISTDIR=/scratch-cbe/users/alikaan.gueven/AN_plots/ParT_hists/plotconfig_Run3_effcheck

DATA17=$HISTDIR/data17/met_2017_hist.root
DATA18=$HISTDIR/data18/met_2018_hist.root
DATA22PRE=$HISTDIR/data22_pre/met_2022_hist.root
DATA22POST=$HISTDIR/data22_post/met_2022_hist.root
DATA23PRE=$HISTDIR/data23_pre/met_2023_hist.root
DATA23POST=$HISTDIR/data23_post/met_2023_hist.root
DATA24=$HISTDIR/data24/met_2024_hist.root


# Extract and process the names directly using a pipeline and a while-read loop
rootls -t $DATA18                | \
awk -F'"' '{print $2}'            | \
while IFS= read -r line;
do
    echo "Processing directory: $line"
    run_compareK $line
done
