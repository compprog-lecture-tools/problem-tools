#!/usr/bin/env bash
# Usage: ./check-single.sh solution_executable validator_executable in_file temp_dir

rm -rf "$4"
mkdir -p "$4"

# shellcheck disable=SC2094
"$1" < "$3" | "$2" "$3" "${3%.in}.ans" "$4"
RESULT="$?"

if [[ $RESULT -eq 43 ]]; then
    echo "Mismatch on $(basename "$3")"
    cat "$4/judgemessage.txt"
    exit 0
elif [[ $RESULT -ne 42 ]]; then
    echo "Validator crashed on $(basename "$3")" >&2
    cat "$4/judgemessage.txt" >&2
    exit 1
fi
exit 0
