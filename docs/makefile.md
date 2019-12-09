# Problem makefile

This makefile is symlinked into every problem directory.
It provides the meat of the functionality provided by the problem tools.

## TL;DR

Use `make` if you are lazy or just want to build everything.
Use `make pdf` to rebuild the problem statement (to `build/problem/problem.pdf`) and `make notes` for the notes (to `build/<PROBLEM>-notes.pdf`).
Use `make testcases` and `make answers` to generate testcases and answers respectively.

Use `make check-all` to check all solutions against the testcases and `make check-full-all` to additionally run C++ solutions with sanitizers enabled (do this at least once before uploading).
Similarly, use `make time-all` to check the runtime of each solution, or `make time-full-all` for a by-testcase breakdown for each.
Both `check` and `time` can be run for a single solution, for example `make check-solution2.cpp`, `make time-full-solution-linear.cpp`, and so on.

Finally, use `make upload` to upload your problem to the judge.
Don't forget to copy the `login.template.toml` to the root folder as `login.toml` and fill in your judge login.

## Solution checking

How a solution is checked by the `make check-*` targets depends on its type:
 * **AC**: Runs the solution against every testcase and compares the output with the one of the primary solution using the custom validator, if available, or else using the default validator.
           All failing testcases will be reported after all testcases have been checked.
           Should the solution crash (i.e. non-zero exit code), this is reported and the checking aborted.
 * **WA**: Check that the solution outputs a wrong answer on at least one testcase.
           Crashes of the solution are ignored.
 * **TLE**: Checks that the solution takes at least `1.5 * timelimit` seconds to finish on at least one testcase.
            The solution is stopped after `3 * timelimit` seconds (this is quite inaccurate, thus the particularly safe limit).
            If your computer is much faster/slower than the judge, you can create a `.timefactor` file in the root folder containing a real number.
            This number will be multiplied into every timelimit, so you could use `2.0` if your computer is roughly twice as fast as the judge.
            If general however, you should design your problems to keep the time gap between AC and TLE solutions as large as possible.

## Reference

Below is a breakdown of every target in the makefile by category.
Sometimes `<PLACEHOLDER>`'s are used.
In this case, `<SOLUTION>` refers to a solution in `executables` by its filename with extension, and `<PROBLEM>` to the problem name dictated by its directory name.

If you ever want to see exactly what the makefile is doing, you can pass `VERBOSE=1` to `make` to enable commands being printed out before being run.

### Convenience aliases
 * **`all`**: Builds everything ready for uploading and the problem notes, but does not run any checks
 * **`pack`**: Packs the problem archive for uploading, as well as the validator zip (if applicable)
 * **`pdf`**: Builds the problem statement to `build/problem/problem.pdf`
 * **`solution`**: Builds the primary solution (`executables/solution.{cpp|py}`)
 * **`generator`**: Builds the testcase generator
 * **`testcases`**: Generates all testcases into `build/testcases`
 * **`answers`**: Generate answers for all testcases using the primary solution
 * **`notes`**: Builds the problem notes to `build/<PROBLEM>-notes.pdf`
 * **`validator`**: Builds the validator

### Misc.
 * **`clean`**: Deletes the `build` directory, resetting everything built so far
 * **`upload`**: Uploads the problem to a judge defined in the `login.toml` in the root directory
 * **`check-notes`**: Checks whether problem notes have been written in `notes.ipe`

### Checking
 * **`check-<SOLUTION>`**: Checks `<SOLUTION>` against the testcases (see [Solution checking](#solution-checking) for details)
 * **`check-full-<SOLUTION>`**: For C++ AC solutions, this additionally runs it again with sanitizers enabled
 * **`check-all`**: Run `check-<SOLUTION>` for every solution
 * **`check-full-all`**: Run `check-full-<SOLUTION>` for every solution

### Timing
 * **`time-<SOLUTION>`**: Run `<SOLUTION>` against the testcases and report the maximum runtime
 * **`time-full-<SOLUTION>`**: Breakdown the runtime of `<SOLUTION>` for every testcase 
 * **`time`**: Time the primary solution
 * **`time-full`**: Time the primary solution for every testcase
 * **`time-all`**: Time all non-TLE solutions
 * **`time-full-all`**: Time all solutions non-TLE solutions

### Internal

These targets are mostly used internally, but can occasionally be useful.
They refer directly to the file that is created as result of the target.

 * **`build/builds/<SOLUTION>/run`**: Build an executable for running `<SOLUTION>`. For Python scripts, this generates a wrapper shell script.
 * **`build/builds/<SOLUTION>/debug/run`**: For C++ executables, this builds them with sanitizers enabled. For Python scripts, this build step is a no-op and does not create the `run` file.
 * **`build/validator/run`**: Builds the validator executable. If the problem is not using a custom validator, this builds the default validator.
 * **`build/probljem/metainfo-exclude.tex`**: Builds a latex file containing meta info about the problem (name, timelimit, etc.). These will then be available in the main `problem.tex` as TeX commands.
 * **`build/problem/problem.pdf`**: Builds the problem statement pdf.
 * **`build/testcases/testcases-stamp`**: Generates all testcases. The stamp file is used to avoid rebuilds if nothing has changed.
 * **`build/testcases/<TESTCASE>.ans`**: Generates the answer for `<TESTCASE>` using the primary solution.
 * **`build/testcases/answers-stamp`**: Generates all answers, using a stamp just as for testcases.
 * **`build/testcases/sample-answers-stamp`**: Generate answers for sample testcases. This is used to speed up building of the problem statement
 * **`build/<PROBLEM>.zip`**: Packs the problem archive
 * **`build/<PROBLEM>-validator.zip`**: Packs the validator archive
 * **`build/<PROBLEM>-notes.pdf`**: Builds the problem notes
