# problem-tools

Tools to develop and build competitive programming problems.
Should be included as a submodule in problem repositories.

## Overview

In repositories using these tools, problems will be grouped by course and by contest.
Courses are top-level directories, and also contain templates for the problem statements and solution notes.
Contests then are directories in a course directory and contain problem directories.

Each problem consist of:

  * a problem statement written in LaTeX
  * a testcase generator
  * one or more solutions, including intentionally wrong or slow ones
  * (optional) a validator to check submission output for correctness
  * solution notes created in Ipe
  * a `domjudge-problem.ini` containing some metadata

All of the executables are grouped in a `executables` directory, and can be written in either C++17 or Python 3.

## Requirements

To use these tools, you will need:
  * Bash 4+ with the GNU `realpath` tool installed
  * Make
  * Python 3.6+ with everything listed in `requirements.txt` installed (run `pip install -r requirements.txt` with the `pip` version corresponding to your python 3.6+ version)
  * GCC 8.1 or newer (on macOS, you will need to install this using homebrew, the builtin `g++` program links to clang). See the faq entry below for g++ vs. clang.
  * Latex including `latexmk` (already included with most latex setups)
  * Ipe (the `ipetoipe` program should be available in your `PATH`)
  * (optional) GNU `parallel` to speed up some scripts

For some helper scripts you will also need `pdfjoin` and `pdfinfo`.
Lastly, if you want to run a local judge setup for testing, you will also need the requirements listed in [local-judge/README.md](local-judge/README.md).

## Usage

You interact with these tools through the `setup-problem.py` script in the root folder and through the makefiles in both the contest and problem directories.
The targets defined by these are described in full detail in [docs/Makefile.md](docs/Makefile.md) and [docs/ContestMakefile.md](docs/ContestMakefile.md) respectively.
You are encouraged to at least skim through these before working on a problem, as many common problems are already solved by these.

## FAQ

  * *Why do I need g++ instead of clang?*
    Clang's standard library does not implement `ios_base::sync_with_stdio`, which means that IO will be significantly slower.
    This makes it much harder to compare local runtime with runtime on the judge.

## Setting up a problem repository

To setup a new problem repository, create an empty git repo and then, from its root directory:

  * Add this repo as submodule in the `tools` folder:
    ```bash
    git submodule add git@gitlab.hpi.de:competitive-programming/problem-tools.git tools
    ```
  * Create a convenience symlink to the `setup-problem.py` script:
    ```bash
    ln -s ./tools/setup-problem.py setup-problem.py
    ```
  * Add `/timefactor` and `/login.toml` to your repos `.gitignore`
