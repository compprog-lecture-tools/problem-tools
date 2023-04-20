#!/bin/sh
build() {
    g++ -Wall -O2 -static -pipe -std=c++20 -isystem. -o "$1" "$1.cpp"
}

build interactor
mv interactor run
