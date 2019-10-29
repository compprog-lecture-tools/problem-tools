#!/usr/bin/env bash
# Usage: ./check-tle.sh solution_executable validator_executable in_file temp_dir timelimit
# Exit code is 2 if a slow solution was found

TIMEFORMAT=%R

SOLUTION="$1"
IN_FILE="$3"
TEMP_DIR="$4"
TIMELIMIT="$5"

rm -rf "$TEMP_DIR"
mkdir -p "$TEMP_DIR"

if [[ ! -x $(command -v timeout) ]]; then
    echo 'GNU timeout missing!' >&2
    exit 1
fi

# A slow solution should overshoot the timelimit by at least 50%.
# We use time to measure the actual runtime, and GNU timeout to avoid
# solutions running indefinitely. Because GNU timeout is quite inaccurate,
# so we pass it double the checked timelimit
CHECKED_TIMELIMIT="$(bc -l <<< "$TIMELIMIT * 1.5")"
TIMEOUT="$(bc -l <<< "$CHECKED_TIMELIMIT * 2")"

# Use `time timeout ...` instead of `timeout time ...` s.t. bash's time gets
# used
TIME="$( (time timeout "$TIMEOUT" "$SOLUTION" < "$IN_FILE" > /dev/null) 2>&1 )"
RESULT="$?"

# Timeout uses 124 to report timeouts
if [[ $RESULT -eq 124  ]]; then
    exit 2
fi

# We ignore solution crashes (exit code != 0), we only care whether the
# solution is slow
if [[ "$(bc -l <<< "$TIME > $CHECKED_TIMELIMIT")" -eq 1 ]]; then
    exit 2
fi
exit 0
