#!/usr/bin/env bash

set -e

find_cxx_compiler() {
    # Allow overriding the C++ compiler using the CXX env var
    if [[ -n "$CXX" ]]; then
        echo "$CXX"
    else
        if [[ $OSTYPE == "darwin"* ]]; then
            # g++ links to clang, and clang/libc++ iostreams are ridiculously slow
            # because `sync_with_stdio` is a noop.
            # Try to use the newest GCC in /usr/local/bin which includes a version number
            # (this finds homebrew installed gcc's and possibly others)
            CXX="$(find /usr/local/bin -name 'g++-*' | sort -r | head -n1)"
            if [[ $CXX == "" ]]; then
                echo "GCC required (no g++-VERSION found in /usr/local/bin)" >&2
                exit 1
            fi
            echo "$CXX"
        else
            echo "g++"
        fi
    fi
}

CXX_FLAGS="-Wall -Wextra -Wpedantic -Wno-sign-compare -std=c++17 -I$(dirname "$1")"
if [[ -n $DEBUG ]]; then
    "$(find_cxx_compiler)" -o run -g -fsanitize=undefined $CXX_FLAGS "$1"
else
    "$(find_cxx_compiler)" -o run -O2 $CXX_FLAGS "$1"
fi
