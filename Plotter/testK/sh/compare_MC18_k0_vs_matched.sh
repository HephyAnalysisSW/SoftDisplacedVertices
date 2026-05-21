#!/bin/bash

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

run_compare_pair(){

    kind=$1
    sample=$2
    dir_k0=$3
    dir_matched=$4

    INPUT=$HISTDIR/${kind}/${sample}_hist.root
    PAIR=${dir_k0}_vs_${dir_matched}
    OUTDIR=$HISTDIR/plots/compare_dirs_18/${kind}/${sample}/${PAIR}

    PDFDIR=$OUTDIR/pdf
    PNGDIR=$OUTDIR/png
    LOGPNGDIR=$OUTDIR/logpng

    mkdir -p "$PDFDIR" "$PNGDIR" "$LOGPNGDIR"

    python3 "$SCRIPT_DIR/../compare.py"                                              \
    --input "$INPUT"                                                                 \
    --dirs "$dir_k0" "$dir_matched"                                                  \
    --nice k0 matched                                                                \
    --output "$OUTDIR"                                                              \
    --scale                                                                         \
    --ratio

    for pdf_file in "$OUTDIR"/*.pdf;
    do
        [[ -e "$pdf_file" ]] && mv "$pdf_file" "$PDFDIR"
    done

    for png_file in "$OUTDIR"/*.png;
    do
        [[ -e "$png_file" ]] || continue
        if [[ "$png_file" == *log.png ]];
        then
            mv "$png_file" "$LOGPNGDIR"
        else
            mv "$png_file" "$PNGDIR"
        fi
    done
}

run_compare_sample(){

    kind=$1
    sample=$2

    run_compare_pair "$kind" "$sample"    all_SDVTrack_pair_k0     all_SDVTrack_pair_matched
    run_compare_pair "$kind" "$sample"    all_SDVTrack_k0          all_SDVTrack_matched
    run_compare_pair "$kind" "$sample"    all_SDVSecVtx_k0         all_SDVSecVtx_matched
}

HISTDIR=/scratch-cbe/users/alikaan.gueven/AN_plots/ParT_hists/vtx_PART_1111best_valloss_epoch_MET400_multiplane_dphi_test3

run_compare_sample bkg all_2018
run_compare_sample sig C1N2ML_M500_485_ct20_2018
