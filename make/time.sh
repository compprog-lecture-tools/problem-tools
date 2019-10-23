#!/usr/bin/env bash

TIMEFORMAT=%R

TIMES=''
echo -n "Timing $(basename "$(dirname "$1")")"
if [[ -n $FULL ]]; then
    echo ''
fi
for f in build/testcases/*.in; do
    TIME="$( (time "$1" < "$f" > /dev/null) 2>&1)"
    if [[ -n $FULL ]]; then
        # TODO: find actual longest name instead of justifying to 30
        printf '%-30s' "$(basename "$f"): "
        echo "${TIME}s"
    fi
    TIMES="${TIMES} $TIME"
done
MAXTIME="$(echo "$TIMES" | tr ' ' '\n' | sort -r | head -n1)"
if [[ ! -n $FULL ]]; then
    echo -n ': '
fi
echo "Maximum runtime: ${MAXTIME}s"
