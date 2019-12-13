#!/usr/bin/env bash
die() {
    echo "$1" >&2
    exit 1
}

if [[ $# -eq 0 ]]; then
    die "Usage: $0 out_pdf problem1 problem2 ..."
fi

for program in pdfjoin pdfinfo; do
    if [[ ! -x $(command -v "$program") ]]; then
        die "$program required but not installed"
    fi
done

SCRIPT_DIR="$(dirname "${BASH_SOURCE[0]}")"
(
    cd "$SCRIPT_DIR"/almost-blank-page || exit 1
    latexmk -quiet -pdf blank.tex > /dev/null
)

PDFJOIN_ARGS=()
for p in "${@:2}"; do
    make -C "$p" pdf
    PAGES="$(pdfinfo "$p/build/problem/problem.pdf" | grep 'Pages:' | awk '{print $2}')"
    PDFJOIN_ARGS+=("$p/build/problem/problem.pdf")
    if [[ $((PAGES % 2)) -eq 1 ]]; then
        PDFJOIN_ARGS+=("$SCRIPT_DIR/almost-blank-page/blank.pdf")
    fi
done
pdfjoin -q -o "$1" "${PDFJOIN_ARGS[@]}"
