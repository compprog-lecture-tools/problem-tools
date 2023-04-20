#!/bin/sh
build() {
    g++ -Wall -O2 -static -pipe -std=c++17 -isystem. -o "$1" "$1.cpp"
}

build run_testlib_interactor
build interactor
mv interactor run
