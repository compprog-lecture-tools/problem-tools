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

WARNING_FLAGS="-Wall -Wextra -pedantic -Wshadow -Wformat=2 -Wfloat-equal -Wconversion -Wno-sign-conversion -Wno-sign-compare"
SANITIZER_FLAGS="-fsanitize=address,undefined -fno-omit-frame-pointer -fno-sanitize-recover=undefined"
COMMON_FLAGS="-std=c++17 -isystem$(dirname "$1")"
if [[ -n $DEBUG ]]; then
    # Suppress warnings so we only get them once
    "$(find_cxx_compiler)" -o run -g -w $SANITIZER_FLAGS $COMMON_FLAGS "$1"
else
    "$(find_cxx_compiler)" -o run -O2 $WARNING_FLAGS $COMMON_FLAGS "$1"
fi
