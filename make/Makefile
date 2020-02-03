# vim: set fdm=marker:
REPO_ROOT=$(shell git rev-parse --show-toplevel)
TOOLS_MAKE_DIR=$(REPO_ROOT)/tools/make
PROBLEM_ID=$(shell basename $$PWD)
TIMELIMIT=$(shell grep -o "^timelimit=\S*" domjudge-problem.ini | sed 's/timelimit=//')

find_program = $(if $(wildcard executables/$(1).cpp),executables/$(1).cpp,$(if $(wildcard executables/$(1).py),executables/$(1).py,))
has_marker = $(findstring $(1).cpp,$(2))$(findstring $(1).py,$(2))

GENERATOR = $(call find_program,generator)
SOLUTION = $(call find_program,solution)
VALIDATOR = $(call find_program,validator)
ALL_SOLUTIONS=$(wildcard executables/solution*.cpp) $(wildcard executables/solution*.py)

TLE_SOLUTIONS=$(foreach s,$(ALL_SOLUTIONS),$(if $(call has_marker,tle,$(s)),$(s),))
WA_SOLUTIONS=$(foreach s,$(ALL_SOLUTIONS),$(if $(call has_marker,wa,$(s)),$(s),))
NON_TLE_SOLUTIONS=$(foreach s,$(ALL_SOLUTIONS),$(if $(call has_marker,tle,$(s)),,$(s)))
AC_SOLUTIONS=$(foreach s,$(NON_TLE_SOLUTIONS),$(if $(call has_marker,wa,$(s)),,$(s)))

NOTES_PDF=build/$(PROBLEM_ID)-notes.pdf
GENERATOR_RUN=$(patsubst executables/%,build/builds/%/run,$(GENERATOR))
SOLUTION_RUN=$(patsubst executables/%,build/builds/%/run,$(SOLUTION))
VALIDATOR_RUN=$(patsubst executables/%,build/builds/%/run,$(VALIDATOR))


.PHONY: all
all: pack $(NOTES_PDF)

ifndef VERBOSE
.SILENT:
endif


# Building {{{
.SECONDARY:
build/builds/%.cpp/run: executables/%.cpp $(wildcard executables/*.h) $(wildcard executables/*.hpp)
	echo 'Building $*.cpp'
	mkdir -p '$(dir $@)'
	cd '$(dir $@)'; '$(TOOLS_MAKE_DIR)/build-cpp.sh' '../../../executables/$*.cpp'

.SECONDARY:
build/builds/debug/%.cpp/run: executables/%.cpp $(wildcard executables/*.h) $(wildcard executables/*.hpp)
	echo 'Building $*.cpp in debug mode'
	mkdir -p '$(dir $@)'
	cd '$(dir $@)'; DEBUG=1 '$(TOOLS_MAKE_DIR)/build-cpp.sh' '../../../../executables/$*.cpp'

.SECONDARY:
build/builds/%.py/run: executables/%.py
	echo 'Building $*.py'
	mkdir -p '$(dir $@)'
	cd '$(dir $@)'; \
		echo '#!/bin/sh' > run; \
		echo 'exec python3 '$(realpath executables/$*.py)' "$$@"' >> run; \
		chmod +x run

.SECONDARY:
build/builds/debug/%.py/run: executables/%.py
	# Don't do anything
	true

.SECONDARY:
build/validator/run: $(VALIDATOR_RUN)
	mkdir -p '$(dir $@)'
ifeq ($(strip $(VALIDATOR)),)
	cd '$(dir $@)'; '$(TOOLS_MAKE_DIR)/build-cpp.sh' '$(TOOLS_MAKE_DIR)/validator/default-validator.cpp'
else
	ln -sf '$(realpath $(VALIDATOR_RUN))' '$@'
endif
# }}}


# Checking {{{
check-%: build/builds/%/run build/validator/run build/testcases/testcases-stamp build/testcases/answers-stamp
	echo 'Checking $*'
	mkdir -p build/validator
	'$(TOOLS_MAKE_DIR)/check.sh' 'build/builds/$*/run' '' '$*' build/validator build/testcases '$(TIMELIMIT)'

check-full-%: build/builds/%/run build/builds/debug/%/run build/validator/run build/testcases/testcases-stamp build/testcases/answers-stamp
	echo 'Checking $* (full)'
	mkdir -p build/validator
	'$(TOOLS_MAKE_DIR)/check.sh' 'build/builds/$*/run' 'build/builds/debug/$*/run' '$*' build/validator build/testcases '$(TIMELIMIT)'

# Check all solutions so that the main solutions gets run with sanitizers enabled
check-all: $(patsubst executables/%,check-%,$(ALL_SOLUTIONS))

check-full-all: $(patsubst executables/%,check-full-%,$(ALL_SOLUTIONS))
# }}}


# Timing {{{
time-%: build/builds/%/run build/testcases/testcases-stamp
	'$(TOOLS_MAKE_DIR)/time.sh' 'build/builds/$*/run'

time-all: $(patsubst executables/%,time-%,$(NON_TLE_SOLUTIONS))

time: time-$(notdir $(SOLUTION))

time-full-%: build/builds/%/run build/testcases/testcases-stamp
	FULL=1 '$(TOOLS_MAKE_DIR)/time.sh' 'build/builds/$*/run'

time-full-all: $(patsubst executables/%,time-full-%,$(NON_TLE_SOLUTIONS))

time-full: time-full-$(notdir $(SOLUTION))
# }}}


# {{{ Latex building
build/problem/metainfo-include.tex: domjudge-problem.ini ..
	mkdir -p build/problem/
	printf '\\newcommand{\\problemName}{$(PROBLEM_ID)}\n' > $@
	printf '\\newcommand{\\problemDir}{../..}\n' >> $@
	printf '\\newcommand{\\timelimit}{%s}\n' "$(TIMELIMIT)" >> $@

build/problem/problem.pdf: problem.tex $(wildcard .template/*) build/testcases/sample-answers-stamp build/problem/metainfo-include.tex
	echo Building problem.pdf
	mkdir -p build/problem/
	cp -f problem.tex build/problem/
	if [ ! -e build/problem/.template ]; then \
		ln -s ../../.template build/problem/.template; \
	fi
	cd build/problem; latexmk -quiet -pdf -interaction=nonstopmode problem > ../tex.log
# }}}


# {{{ Generating testcases
build/testcases/testcases-stamp: $(GENERATOR_RUN)
	echo Generating testcases
	rm -rf build/testcases
	mkdir -p build/testcases
	cd build/testcases; '$(realpath $(GENERATOR_RUN))'
	touch build/testcases/testcases-stamp
# }}}


# {{{ Generating answers
build/testcases/%.ans: build/testcases/%.in $(SOLUTION_RUN) build/testcases/testcases-stamp
	'$(SOLUTION_RUN)' < $< > $@

build/testcases/answers-stamp: build/testcases/testcases-stamp $(SOLUTION_RUN)
	echo Generating answers
	TESTCASES=$$(find build/testcases/ -name *.in | sed 's/\.in/\.ans/g'); \
	if [ -n "$$TESTCASES" ]; then \
		'$(MAKE)' $$TESTCASES; \
	fi
	touch build/testcases/answers-stamp
	touch build/testcases/sample-answers-stamp

build/testcases/sample-answers-stamp: build/testcases/testcases-stamp $(SOLUTION_RUN)
	echo Generating sample answers
	TESTCASES=$$(find build/testcases/ -name sample*.in | sed 's/\.in/\.ans/g'); \
	if [ -n "$$TESTCASES" ]; then \
		'$(MAKE)' $$TESTCASES; \
	fi
	touch build/testcases/sample-answers-stamp
# }}}


# {{{ Packing
build/$(PROBLEM_ID).zip: build/testcases/answers-stamp build/problem/problem.pdf \
	                     domjudge-problem.ini $(wildcard executables/solution*.cpp) \
						 $(wildcard executables/solution*.py)
	echo 'Packing $(notdir $@)'
	rm -rf build/judge-package
	mkdir -p build/judge-package/data/sample
	mkdir -p build/judge-package/data/secret
	mkdir -p build/judge-package/submissions/accepted
	mkdir -p build/judge-package/submissions/wrong_answer
	mkdir -p build/judge-package/submissions/time_limit_exceeded
	for f in $(AC_SOLUTIONS); do \
		cp "$$f" build/judge-package/submissions/accepted; \
	done
	for f in $(TLE_SOLUTIONS); do \
		cp "$$f" build/judge-package/submissions/time_limit_exceeded; \
	done
	for f in $(WA_SOLUTIONS); do \
		cp "$$f" build/judge-package/submissions/wrong_answer; \
	done
ifneq ($(VALIDATOR),)
	for f in '$(TOOLS_MAKE_DIR)'/validator/solutions/wa/*; do \
		cp "$$f" build/judge-package/submissions/wrong_answer; \
	done
	for f in '$(TOOLS_MAKE_DIR)'/validator/solutions/tle/*; do \
		cp "$$f" build/judge-package/submissions/time_limit_exceeded; \
	done
endif
	for f in $$(find build/testcases/ -name 'sample*' '(' -name '*.in' -or -name '*.ans' -or -name '*.desc' ')'); do \
		cp "$$f" build/judge-package/data/sample; \
	done
	for f in $$(find build/testcases/ -not -name 'sample*' '(' -name '*.in' -or -name '*.ans' -or -name '*.desc' ')'); do \
		cp "$$f" build/judge-package/data/secret; \
	done
	cp build/problem/problem.pdf domjudge-problem.ini build/judge-package
ifneq ($(VALIDATOR),)
	# Add special_compare entry to domjudge-problem.ini
	if grep -q special_compare domjudge-problem.ini; then \
		echo "Remove special_compare from domjudge-problem.ini, it will be added automatically" >&2; \
		exit 1; \
	fi
	echo "special_compare=$(PROBLEM_ID)-validator" >> build/judge-package/domjudge-problem.ini
endif
	cd build/judge-package; zip -q -r ../judge-package-temp.zip ./*
	mv build/judge-package-temp.zip $@

ifneq ($(VALIDATOR),)
build/$(PROBLEM_ID)-validator.zip: $(VALIDATOR) $(if $(find cpp,$(suffix $(VALIDATOR))),$(wildcard executables/*.h) $(wildcard executables/*.hpp),)
	echo 'Packing $(notdir $@)'
	rm -rf build/validator-package
	mkdir -p build/validator-package
	cd build/validator-package; '$(TOOLS_MAKE_DIR)/validator/assemble.sh' '$(realpath $(VALIDATOR))' '$(PROBLEM_ID)'
	cd build/validator-package; zip -q -r ../validator-temp.zip ./*
	mv build/validator-temp.zip '$@'
endif
# }}}


# {{{ Ipe building
$(NOTES_PDF): notes.ipe
	echo 'Generating $(notdir $(NOTES_PDF))'
	mkdir -p build
	ipetoipe -pdf -export notes.ipe '$@' 2> /dev/null
# }}}


# {{{ Misc.
.PHONY: clean
clean:
	rm -rf build

.PHONY: upload
upload: build/$(PROBLEM_ID).zip $(if $(VALIDATOR),build/$(PROBLEM_ID)-validator.zip)
	echo Uploading archive
	'$(TOOLS_MAKE_DIR)/upload.py' 'build/$(PROBLEM_ID).zip' $(if $(VALIDATOR),'build/$(PROBLEM_ID)-validator.zip')

.PHONY: check-notes
check-notes:
	if grep -qF 'TODO: create notes' notes.ipe; then \
		echo 'Missing notes for $(PROBLEM_ID)'; \
	fi
# }}}


# {{{ Aliases
.PHONY: pack
pack: build/$(PROBLEM_ID).zip $(if $(VALIDATOR),build/$(PROBLEM_ID)-validator.zip)

.PHONY: pdf solution generator testcases notes upload
pdf: build/problem/problem.pdf
solution: $(SOLUTION_RUN)
generator: $(GENERATOR_RUN)
testcases: build/testcases/testcases-stamp
answers: build/testcases/answers-stamp
notes: $(NOTES_PDF)
validator: build/builds/validator.cpp/run
# }}}
