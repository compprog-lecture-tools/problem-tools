#!/bin/sh
exec g++ -Wall -O2 -static -pipe -std=c++17 -o run validator.cpp
