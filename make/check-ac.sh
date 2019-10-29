#!/usr/bin/env bash
# Usage: ./check-ac.sh solution_executable validator_executable in_file temp_dir
# Exit code is 1 if solution or validator crashed

SOLUTION="$1"
VALIDATOR="$2"
IN_FILE="$3"
TEMP_DIR="$4"

rm -rf "$TEMP_DIR"
mkdir -p "$TEMP_DIR"

if ! "$SOLUTION" < "$IN_FILE" > "$TEMP_DIR/output"; then
    # Solution crashed
    echo "Solution crashed on $(basename "$IN_FILE")" >&2
    exit 1
fi

"$VALIDATOR" "$IN_FILE" "${IN_FILE%.in}.ans" "$TEMP_DIR" < "$TEMP_DIR/output"
RESULT="$?"

if [[ $RESULT -eq 43 ]]; then
    echo "Mismatch on $(basename "$IN_FILE")"
    cat "$TEMP_DIR/judgemessage.txt"
    exit 0
elif [[ $RESULT -ne 42 ]]; then
    echo "Solution or validator crashed on $(basename "$IN_FILE")" >&2
    cat "$TEMP_DIR/judgemessage.txt" >&2
    exit 1
fi
exit 0
