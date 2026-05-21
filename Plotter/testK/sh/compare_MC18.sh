#!/bin/bash

run_compareK(){

    OUTDIR=$HISTDIR/plots/MC/$1
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
    --signice  "matched signal"                                                          \
    --output $OUTDIR                                                           \
    --dirs $1                                                                  \
    --norm                                                                     \

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

# HISTDIR=/scratch-cbe/users/alikaan.gueven/AN_plots/ParT_hists/SDVSecVtx_ParTScore
HISTDIR=/scratch-cbe/users/alikaan.gueven/AN_plots/ParT_hists/AN-25-092_ML_plots_inputs_k0_v_sig
# DATA=$HISTDIR/data/met_2018_hist.root
QCD=$HISTDIR/bkg_2018/qcd_2018_hist.root
WJETS=$HISTDIR/bkg_2018/wjets_2018_hist.root
ZJETS=$HISTDIR/bkg_2018/zjets_2018_hist.root
TOP=$HISTDIR/bkg_2018/top_2018_hist.root
SIGNAL=$HISTDIR/sig_2018/C1N2_M500_485_ct20_2018_hist.root
# SIGNAL=$HISTDIR/sig/stopMLstudy_M1000_988_ct20_2018_hist.root


# Extract and process the names directly using a pipeline and a while-read loop
rootls -t $QCD                  | \
awk -F'"' '{print $2}'          | \
while IFS= read -r line;
do
    echo "Processing directory: $line"
    run_compareK $line
done


