#!/bin/bash

run_compareK(){

    kind=$1
    sample=$2
    shift
    shift
    SIGNAL=$HISTDIR/${kind}/${sample}_hist.root
    
    OUTDIR=$HISTDIR/plots/compare_dirs/${kind}/${sample}

    PDFDIR=$OUTDIR/pdf
    PNGDIR=$OUTDIR/png
    LOGPNGDIR=$OUTDIR/logpng

    mkdir -p $PDFDIR
    mkdir -p $PNGDIR
    mkdir -p $LOGPNGDIR


    python3 ../compare.py                                                            \
    --input $HISTDIR/${kind}/${sample}_hist.root                                     \
    --dirs $@                                                                        \
    --nice $@                                                                        \
    --output $OUTDIR                                                                 \
    --scale

    mv $OUTDIR/*.pdf            $PDFDIR
    mv $OUTDIR/*log.png         $LOGPNGDIR
    mv $OUTDIR/*.png            $PNGDIR
}

HISTDIR=/scratch-cbe/users/alikaan.gueven/AN_plots/ParT_hists/vtx_PART_770_epoch_83


# run_compareK sig stop_M600_585_ct20_2018  all_SDVSecVtx_potatoML all_SDVSecVtx_hiML all_SDVSecVtx_genmatch
run_compareK bkg all_2018 ML80_evt ML88_evt ML93_evt ML95_evt
run_compareK bkg all_2018 ML80_SDVSecVtx_ML80 ML88_SDVSecVtx_ML88 ML93_SDVSecVtx_ML93 ML95_SDVSecVtx_ML95

run_compareK sig stop_M600_585_ct20_2018 ML80_evt ML88_evt ML93_evt ML95_evt
run_compareK sig stop_M600_585_ct20_2018 ML80_SDVSecVtx_ML80 ML88_SDVSecVtx_ML88 ML93_SDVSecVtx_ML93 ML95_SDVSecVtx_ML95