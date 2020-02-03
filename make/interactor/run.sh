#!/bin/sh

TESTIN="$1";  shift
PROGOUT="$1"; shift
ANSFILE="$1"; shift
COMPAREMETA="$1"; shift
FEEDBACKDIR="$1"; shift

MYDIR=$(dirname "$0")

exec ../dj-bin/runpipe ${DEBUG:+-v} -o "$PROGOUT" -M "$COMPAREMETA" "$MYDIR/run_testlib_interactor" "$MYDIR/interactor" "$TESTIN" "$ANSFILE" "$FEEDBACKDIR" = "$@"
