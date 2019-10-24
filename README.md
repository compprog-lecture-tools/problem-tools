# problem-tools

Tools to develop and build competitive programming problems.
Should be included as a submodule in problem repositories.

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
