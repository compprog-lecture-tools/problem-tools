# problem-tools

Tools to develop and build competitive programming problems.
Should be included as a submodule in problem repositories.

## Requirements

To use these tools, you will need:
  * Bash 4+ with the GNU `realpath` tool installed
  * Make
  * Python 3.6+ with everything listed in `requirements.txt` installed (run `pip install -r requirements.txt` with the `pip` version corresponding to your python 3.6+ version)
  * GCC 8.1 or newer (on macOS, you will need to install this using homebrew, the builtin `g++` program links to clang). See the faq entry below for g++ vs. clang.
  * Latex including `latexmk` (already included with most latex setups)
  * Ipe (the `ipetoipe` program should be available in your `PATH`)
  * (optional) GNU parallel to speed up some scripts

For some helper scripts you will also need `pdfjoin` and `pdfinfo`.
Lastly, if you want to run a local judge setup for testing, you will also need the requirements listed in [local-judge/README.md]().

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
