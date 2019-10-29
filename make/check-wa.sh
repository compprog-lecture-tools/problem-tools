#!/usr/bin/env bash
# Usage: ./check-wa.sh solution_executable validator_executable in_file temp_dir
# Exit code is 1 if the validator crashed or 2 if a failing solution was found

SOLUTION="$1"
VALIDATOR="$2"
IN_FILE="$3"
TEMP_DIR="$4"

rm -rf "$TEMP_DIR"
mkdir -p "$TEMP_DIR"

# We allow the solution to crash, but not the validator
"$SOLUTION" < "$IN_FILE" > "$TEMP_DIR/output"
"$VALIDATOR" "$IN_FILE" "${IN_FILE%.in}.ans" "$TEMP_DIR" < "$TEMP_DIR/output"
RESULT="$?"

if [[ $RESULT -eq 43 ]]; then
    exit 2
elif [[ $RESULT -ne 42 ]]; then
    echo "Validator crashed on $(basename "$IN_FILE")" >&2
    cat "$TEMP_DIR/judgemessage.txt" >&2
    exit 1
fi
exit 0
