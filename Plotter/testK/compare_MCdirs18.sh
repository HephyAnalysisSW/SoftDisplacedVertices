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

HISTDIR=/scratch-cbe/users/alikaan.gueven/AN_plots/ParT_hists/vtx_PART_464_epoch_2



# run_compareK evt all_evt exhiML_evt
# run_compareK stop_M1000_980_ct2_2018 all_SDVSecVtx_all all_SDVSecVtx_exhiML all_SDVSecVtx_genmatch
# run_compareK stop_M1000_985_ct20_2018 all_SDVSecVtx_all all_SDVSecVtx_exhiML all_SDVSecVtx_genmatch
# run_compareK stop_M1000_988_ct200_2018 potatoML_evt exloML_evt loML_evt

# run_compareK bkg all_2018 potatoML_evt loML_evt hiML_evt
# run_compareK bkg all_2018 potatoML_SDVSecVtx_all loML_SDVSecVtx_all hiML_SDVSecVtx_all

# run_compareK bkg all_2018 all_SDVSecVtx_potatoML all_SDVSecVtx_loML all_SDVSecVtx_hiML
# run_compareK sig stop_M1000_985_ct20_2018 all_SDVSecVtx_potatoML all_SDVSecVtx_loML all_SDVSecVtx_hiML # all_SDVSecVtx_genmatch
# run_compareK sig stop_M1000_988_ct200_2018 all_SDVSecVtx_potatoML all_SDVSecVtx_loML all_SDVSecVtx_hiML # all_SDVSecVtx_genmatch

# run_compareK sig stop_M600_588_ct200_2018 potatoML_evt loML_evt hiML_evt
run_compareK sig stop_M600_585_ct20_2018  all_SDVSecVtx_potatoML all_SDVSecVtx_hiML all_SDVSecVtx_genmatch
# run_compareK sig stop_M600_580_ct2_2018   potatoML_evt loML_evt hiML_evt

# run_compareK sig stop_M1000_988_ct200_2018 potatoML_evt loML_evt hiML_evt
# run_compareK sig stop_M1000_985_ct20_2018  potatoML_evt loML_evt hiML_evt
# run_compareK sig stop_M1000_980_ct2_2018   potatoML_evt loML_evt hiML_evt


