#!/usr/bin/env bash
# Usage: ./check.sh solution_executable solution_name validator_executable testcases_dir temp_dir

SCRIPT_DIR="$(dirname "${BASH_SOURCE[0]}")"

TEMP_DIR="$5/$2"
mkdir -p "$TEMP_DIR"

CRASH=0
WRONG_MSG_FILE="$TEMP_DIR/wrong_msg"
CRASH_MSG_FILE="$TEMP_DIR/crash_msg"
rm -f "$WRONG_MSG_FILE"
rm -f "$CRASH_MSG_FILE"

if [[ -x $(command -v parallel) ]]; then
    find "$4" \
         -maxdepth 1 \
         -type f \
         -name '*.in' \
    | parallel --halt now,fail=1 \
               "$SCRIPT_DIR/check-single.sh" \
               "$1" \
               "$3" \
               '{}' \
               "$TEMP_DIR/feedback-{%} >> '$WRONG_MSG_FILE' 2>> '$CRASH_MSG_FILE'"
    CRASH="$?"
else
    echo "Install GNU parallel for faster checking of solutions"
    for f in "$4"/*.in; do
        if ! "$SCRIPT_DIR/check-single.sh" "$1" "$3" "$f" "$TEMP_DIR/feedback" >> "$WRONG_MSG_FILE" 2>> "$CRASH_MSG_FILE"; then
            CRASH=1
            break
        fi
    done
fi

if [[ $CRASH != 0 ]]; then
    echo "Validator crashed:" >&2
    # Indent output using sed
    sed 's/^/    /' < "$CRASH_MSG_FILE" >&2
    exit 2
fi
if [[ "$2" == *.wa.cpp ]] || [[ "$2" == *.wa.py ]]; then
    if [[ ! -s "$WRONG_MSG_FILE" ]]; then
        echo "No test case failed!" >&2
        exit 1
    fi
else
    if [[ -s "$WRONG_MSG_FILE" ]]; then
        echo "Testcases failed:" >&2
        sed 's/^/    /' < "$WRONG_MSG_FILE" >&2
        exit 1
    fi
fi
