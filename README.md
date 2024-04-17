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
  * (optional) an interactor for interactive problems
  * (optional) an answer generator if the `.ans` files do not correspond to the solutions output
  * solution notes created in Ipe
  * a `problem.json` containing metadata for the problem list
  * a `domjudge-problem.ini` containing the timelimit

All of the executables are grouped in a `executables` directory, and can be written in either C++20 or Python 3.

## Requirements

To use these tools, you will need:
  * Bash 4+ with the GNU `realpath` tool installed
  * Make
  * Python 3.7+ with everything listed in `requirements.txt` installed (run `pip install -r requirements.txt` with the `pip` version corresponding to your python 3.7+ version)
  * GCC 8.1 or newer (on macOS, you will need to install this using homebrew, the builtin `g++` program links to clang). See the faq entry below for g++ vs. clang.
  * Latex including `latexmk` (already included with most latex setups)
  * Ipe (the `ipetoipe` program should be available in your `PATH`)
  * (optional) GNU `parallel` to speed up some scripts

For some helper scripts you will also need `pdfjam` and `pdfinfo`.
Lastly, if you want to run a local judge setup for testing, you will also need the requirements listed in [local-judge/README.md](local-judge/README.md).

## Usage

You interact with these tools through the `setup-problem.py` script in the root folder and through the makefiles in both the contest and problem directories.
The targets defined by these are described in full detail in [docs/makefile.md](docs/makefile.md) and [docs/contest-makefile.md](docs/contest-makefile.md) respectively.
You are encouraged to at least skim through these before working on a problem, as many common problems are already solved by these.

The different parts of a problem listed in [Overview](#overview) are described in more detail in [docs/structure-of-a-problem.md](docs/structure-of-a-problem.md).
You can read through it while building your first problem.

## FAQ

  * *Why do I need g++ instead of clang?*
    Clang's standard library does not implement `ios_base::sync_with_stdio`, which means that IO will be significantly slower.
    This makes it much harder to compare local runtime with runtime on the judge.
  * *How do I upgrade old problems to a new format?*
    The `setup-problem.py` has an upgrade mode (`setup-problem.py --upgrade`) that aims to help with that process.
    Currently, it prompts you for `problem.json` metadata if it is missing, and detects old `domjudge-problem.ini`'s containing outdated/unnecessary data.
  * *How do I update the python dependencies?*
    The dependency management in this repository follows the method described [here](https://www.kennethreitz.org/essays/a-better-pip-workflow).
    The packages should be installed in a virtual environment.
    In summary: the file `requirements-to-freeze.txt` describes the packages directly required by this repository, possibly with version specifications.
    The file `requirements.txt` describes all direct and indirect dependencies, down to the specific version.
    Thus, running `pip install -r requirements.txt` ensures identical environments with identical versions.
    If you want to modify the dependencies, then optionally specify the new direct dependencies in `requirements-to-freeze.txt` and run `pip install -r requirements-to-freeze.txt --upgrade`.
    Now your environment is up to date. To reflect these changes to `requirements.txt`, run `pip freeze > requirements.txt`.

## Setting up a problem repository

To setup a new problem repository, create an empty git repo and then, from its root directory:

  * Add this repo as submodule in the `tools` folder:
    ```bash
    git submodule add git@github.com:compprog-lecture-tools/problem-tools.git tools
    ```
  * Create a convenience symlink to the `setup-problem.py` script:
    ```bash
    ln -s ./tools/setup-problem.py setup-problem.py
    ```
  * Add `/timefactor` and `/login.toml` to your repos `.gitignore`
