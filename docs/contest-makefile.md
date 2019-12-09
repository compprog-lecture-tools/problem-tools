# Contest makefile

This makefile is symlinked into every contest directory, and provides some small but useful functionality.

The provided targets are:
 * **`notes`**: Builds the problem notes of all problems and joins them (in alphabetical problem name order) into a single pdf
 * **`check-notes`**: Checks for problems for which the problem notes haven't been written
 * **`contest-pdf`**: Joins the problem statements into a single pdf, including almost empty pages as needed s.t. every problem starts on a front side when printing double-sided
 * **`clean`**: Removes the pdfs left by `notes` and `contest-pdf`

As with the problem makefile, you can pass `VERBOSE=1` to `make` to see exactly which commands are being called by the makefile.
