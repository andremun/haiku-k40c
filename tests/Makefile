# tests/Makefile — builds and runs the host-side tests.
# Distributed under the terms of the MIT License.
#
# To add a test: put NAME:DIR in CXX_TESTS (the program is built from
# NAME.cpp, or accept/NAME.cpp, with all of ../src/DIR/*.cpp; DIR may be
# several directories joined by +, for example compute+fifo), or the
# script path in PY_TESTS. `make -s -C tests` exits 0 only when all pass.

CXX      := g++
# -fsanitize=undefined: an overflowing shift or similar stops the test
# (task R1; the external review found two that the tests did not see).
CXXFLAGS := -std=c++17 -Wall -Wextra -Werror -I../src -fsanitize=undefined -fno-sanitize-recover=all
BUILDDIR := ../build/tests

CXX_TESTS := test_s1_boundaries:fifo+hw+mmu test_s1_experiment:runtime \
             test_registerio:hw d1_accept:hw \
             test_pagetable:mmu d2_accept:mmu \
             test_pushbuffer:fifo d3_accept:fifo \
             test_launchdesc:compute+fifo d5_accept:compute+fifo \
             ref_qmd:compute+fifo r1_accept:compute+fifo+hw+mmu
# The Python tests run once the tool of task D4 exists.
PY_TESTS  := $(if $(wildcard ../tools/compare_register_traces.py),$(wildcard test_compare_traces.py accept/d4_accept.py)) \
             accept/r1_accept.py

PROGRAMS := $(foreach t,$(CXX_TESTS),$(BUILDDIR)/$(firstword $(subst :, ,$(t))))

.PHONY: all clean
all: $(PROGRAMS)
	@for p in $(PROGRAMS); do $$p || exit 1; done
	@for t in $(PY_TESTS); do (cd .. && python3 tests/$$t) || exit 1; done

define RULE
$(BUILDDIR)/$(1): $(firstword $(wildcard $(1).cpp accept/$(1).cpp)) $(foreach d,$(subst +, ,$(2)),$(wildcard ../src/$(d)/*.cpp ../src/$(d)/*.h)) | $(BUILDDIR)
	$$(CXX) $$(CXXFLAGS) $$< $(foreach d,$(subst +, ,$(2)),$(wildcard ../src/$(d)/*.cpp)) -o $$@
endef
$(foreach t,$(CXX_TESTS),$(eval $(call RULE,$(firstword $(subst :, ,$(t))),$(lastword $(subst :, ,$(t))))))

$(BUILDDIR):
	mkdir -p $(BUILDDIR)

clean:
	rm -rf $(BUILDDIR)
