#!/bin/sh
exec g++ -Wall -O2 -static -pipe -std=c++20 -isystem. -o run validator.cpp
