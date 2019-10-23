#!/usr/bin/env bash
set -e
shopt -s nullglob

VALIDATOR_SCRIPT_DIR="$(dirname "${BASH_SOURCE[0]}")"

EXT="${1##*.}"
DIR="$(dirname "$1")"
case "$EXT" in
    cpp)
        cp "$1" validator.cpp
        if [[ -n $(echo "$DIR"/*.h "$DIR"/*.hpp) ]]; then
            cp "$DIR"/*.h "$DIR"/*.hpp .
        fi
        cp "$VALIDATOR_SCRIPT_DIR/build-cpp.sh" build
        ;;
    py)
        cp "$1" validator.py
        cp "$VALIDATOR_SCRIPT_DIR/build-nothing.sh" build
        cp "$VALIDATOR_SCRIPT_DIR/run-py.sh" run
        ;;
esac
