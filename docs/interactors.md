# Interactors

Interactors are quite a tricky subject, since they can quite easily crash a judgehost, possibly even sending it into a restart loop.
Therefore, we discuss how interactors work in DOMjudge, how we can integrate into that and how to safely write them.

## Interactors in DOMjudge

The official way to write interactors in DOMjudge is to write a program that accepts the solutions output as its stdin, and writes input to the solution to stdout.
Next, a program called `runpipe` is used to run both the solution and the interactor, connecting their stdins and stdouts appropriately and handling a lot of the errors that can happen.
The result looks something like this:

![interactors1](interactors1.png)

However, DOMjudge also wraps the solution in another program called `runguard`, which enforces time and memory limits, among other things.
So, in reality, the picture looks more like this:

![interactors2](interactors2.png)

The thing we want to avoid at all costs is leaving behind zombie processes when were done.
In the judgehosts `testcase_run.sh` script, remaining zombie processes are treated as a hard error, which in turn send the judgehost into a crash loop, since it will restart and retry judging the solution.
Zombie processes remain, if any of the wrapping programs crash or for some other reason don't `wait` for their child processes.

One case were this happens, is if `runguard` fails to forward some of the solutions output to the interactor.
As a result, the interactor must not finish or otherwise close its stdin before it has read all incoming data.
This is both error-prone, and in constrast to testlibs philosophy of terminating whenever an error occurred.

To combat this, we provide yet another wrapper called `run_testlib_interactor` which runs the actual interactor as a child process.
The interactor inherits the stdout and stderr of the wrapper, while the wrapper forwards data from stdin to the interactor, until the interactor closes its stdin/terminates.
From there on out, the wrapper simply discards any incoming data and finishes once no more data can be read.

So, now the complete picture looks like this:

![interactors3](interactors3.png)

## Writing interactors

Note that we only support the mode were the interactor also already validates the answer (or, in DOMjudge terms, a combined run and compare script).

With this in mind, writing interactors works much like writing validators.
You can access the input file using `inf` and the `.ans` file using `ans`.
To send messages to the solution simply use stdout/`cout`, while reading queries from the solution using `ouf` (which is mapped to stdin, however, you should not use stdin directly if at all possible).
When done, use the arsenal of `quit*` functions and verdicts described in the [validator documentation](./structure-of-a-problem.md#validator-optional).
