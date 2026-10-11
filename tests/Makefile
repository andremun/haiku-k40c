# tests/Makefile — builds and runs the host-side tests.
# Distributed under the terms of the MIT License.
#
# To add a test: put NAME:DIR in CXX_TESTS (the program is built from
# NAME.cpp, or accept/NAME.cpp, with all of ../src/DIR/*.cpp), or the
# script path in PY_TESTS. `make -s -C tests` exits 0 only when all pass.

CXX      := g++
CXXFLAGS := -std=c++17 -Wall -Wextra -Werror -I../src
BUILDDIR := ../build/tests

CXX_TESTS := test_registerio:hw d1_accept:hw \
             test_pagetable:mmu d2_accept:mmu \
             test_pushbuffer:fifo d3_accept:fifo
# The Python tests run once the tool of task D4 exists.
PY_TESTS  := $(if $(wildcard ../tools/compare_register_traces.py),$(wildcard test_compare_traces.py accept/d4_accept.py))

PROGRAMS := $(foreach t,$(CXX_TESTS),$(BUILDDIR)/$(firstword $(subst :, ,$(t))))

.PHONY: all clean
all: $(PROGRAMS)
	@for p in $(PROGRAMS); do $$p || exit 1; done
	@for t in $(PY_TESTS); do (cd .. && python3 tests/$$t) || exit 1; done

define RULE
$(BUILDDIR)/$(1): $(firstword $(wildcard $(1).cpp accept/$(1).cpp)) $(wildcard ../src/$(2)/*.cpp ../src/$(2)/*.h) | $(BUILDDIR)
	$$(CXX) $$(CXXFLAGS) $$< $(wildcard ../src/$(2)/*.cpp) -o $$@
endef
$(foreach t,$(CXX_TESTS),$(eval $(call RULE,$(firstword $(subst :, ,$(t))),$(lastword $(subst :, ,$(t))))))

$(BUILDDIR):
	mkdir -p $(BUILDDIR)

clean:
	rm -rf $(BUILDDIR)
