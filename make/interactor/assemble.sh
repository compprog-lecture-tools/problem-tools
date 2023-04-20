#!/usr/bin/env bash
set -e
shopt -s nullglob

INTERACTOR_SCRIPT_DIR="$(dirname "${BASH_SOURCE[0]}")"

EXT="${1##*.}"
DIR="$(dirname "$1")"
case "$EXT" in
    cpp)
        cp "$1" interactor.cpp
        if [[ -n $(echo "$DIR"/*.h "$DIR"/*.hpp) ]]; then
            cp "$DIR"/*.h "$DIR"/*.hpp .
        fi
        cp "$INTERACTOR_SCRIPT_DIR/build.sh" build
        ;;
    *)
        echo "Interactors are only supported in c++" >&2
        ;;
esac
