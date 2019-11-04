#!/usr/bin/env bash
# Usage: ./check.sh solution_executable solution_debug_executable solution_name validator_dir testcases_dir timelimit

SCRIPT_DIR="$(dirname "${BASH_SOURCE[0]}")"

EXECUTABLE="$1"
DEBUG_EXECUTABLE="$2"
SOLUTION_NAME="$3"
VALIDATOR_DIR="$4"
TESTCASES_DIR="$5"
TIMELIMIT="$6"

TYPE='ac'
if [[ "$SOLUTION_NAME" == *.wa.cpp ]] || [[ "$SOLUTION_NAME" == *.wa.py ]]; then
  TYPE='wa'
elif [[ "$SOLUTION_NAME" == *.tle.cpp ]] || [[ "$SOLUTION_NAME" == *.tle.py ]]; then
  TYPE='tle'
fi

TEMP_DIR="$VALIDATOR_DIR/$SOLUTION_NAME"
mkdir -p "$TEMP_DIR"

VALIDATOR="$VALIDATOR_DIR/run"
EARLY_EXIT_CODE=0
STDOUT_FILE="$TEMP_DIR/stdout"
STDERR_FILE="$TEMP_DIR/stderr"
rm -f "$STDOUT_FILE" "$STDERR_FILE"
touch "$STDOUT_FILE" "$STDERR_FILE"

HAS_PARALLEL=1
if [[ ! -x $(command -v parallel) ]]; then
    echo "Install GNU parallel for faster checking of solutions"
    HAS_PARALLEL=0
fi

check_executable() {
    if [[ $HAS_PARALLEL -eq 1 ]]; then
        find "$TESTCASES_DIR" \
             -maxdepth 1 \
             -type f \
             -name '*.in' \
        | parallel --halt now,fail=1 \
                   "$SCRIPT_DIR/check-$TYPE.sh" \
                   "$1" \
                   "$VALIDATOR" \
                   '{}' \
                   "$TEMP_DIR/feedback-{%}" \
                   "$TIMELIMIT >> '$STDOUT_FILE' 2>> '$STDERR_FILE'" \
                   2> /dev/null  # Silences the 'this job failed' message
        EARLY_EXIT_CODE="$?"
    else
        for f in "$TESTCASES_DIR"/*.in; do
            "$SCRIPT_DIR/check-$TYPE.sh" "$1" "$VALIDATOR" "$f" "$TEMP_DIR/feedback" "$TIMELIMIT" >> "$STDOUT_FILE" 2>> "$STDERR_FILE"
            EARLY_EXIT_CODE="$?"
            if [[ $EARLY_EXIT_CODE -ne 0 ]]; then
                break
            fi
        done
    fi
}

# For AC solutions, also run every testcase through the debug executable that
# has sanitizers enabled
check_executable "$EXECUTABLE"
# For python solutions there is no need for a debug run, so we check if the
# executable actually exists
if [[ -f $DEBUG_EXECUTABLE ]] && [[ $TYPE == 'ac' ]] && [[ $EARLY_EXIT_CODE -eq 0 ]]; then
    echo '  Checking debug build'
    check_executable "$DEBUG_EXECUTABLE"
fi

# The check-* scripts use exit code 1 to report a validator or AC solution
# crashing
if [[ $EARLY_EXIT_CODE -eq 1 ]]; then
    cat "$STDERR_FILE" >&2
    exit 1
fi

# check-wa.sh and check-tle.sh use exit code 2 to early exit when a
# failing/slow testcase was found.
# If every check-*.sh call returned exit code 0, then no such testcase was
# found and the solution is not actually WA/TLE
if [[ $TYPE == 'wa' ]] && [[ $EARLY_EXIT_CODE -eq 0 ]]; then
    echo 'No testcase failed!' >&2
    exit 1
fi
if [[ $TYPE == 'tle' ]] && [[ $EARLY_EXIT_CODE -eq 0 ]]; then
    echo 'No testcase was slow!' >&2
    exit 1
fi

# For AC solutions, we want to find all failing testcases
# Thus, even if EARLY_EXIT_CODE=0, we need to check if STDOUT_FILE
# contains messages about failing testcases
if [[ $TYPE == 'ac' ]] && [[ -s "$STDOUT_FILE" ]]; then
    cat "$STDOUT_FILE" >&2
    exit 1
fi

# Nothing failed
exit 0
