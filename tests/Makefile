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

CXX_TESTS := test_bootstrap:runtime \
             test_devinit:devinit s1a_accept:devinit \
             test_memory:memory \
             test_s1_boundaries:fifo+hw+mmu test_s1_experiment:runtime \
             test_registerio:hw d1_accept:hw \
             test_pagetable:mmu d2_accept:mmu \
             test_pushbuffer:fifo d3_accept:fifo \
             test_launchdesc:compute+fifo d5_accept:compute+fifo \
             ref_qmd:compute+fifo r1_accept:compute+fifo+hw+mmu
# The Python tests run once the tool of task D4 exists.
PY_TESTS  := $(if $(wildcard ../tools/compare_register_traces.py),$(wildcard test_compare_traces.py accept/d4_accept.py)) \
             accept/r1_accept.py test_vm_tools.py test_card_run.py test_devinit_inventory.py test_load_trace.py test_devinit_preflight.py test_devinit_rom.py test_devinit_trace_join.py

PROGRAMS := $(foreach t,$(CXX_TESTS),$(BUILDDIR)/$(firstword $(subst :, ,$(t))))

.PHONY: all clean
all: $(PROGRAMS) $(BUILDDIR)/devinit_rom_sim $(BUILDDIR)/test_haiku_backend $(BUILDDIR)/test_identity_probe
	@for p in $(PROGRAMS) $(BUILDDIR)/test_haiku_backend $(BUILDDIR)/test_identity_probe; do $$p || exit 1; done
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

# Explicit offline-ROM simulator tool; never run without a supplied image.
$(BUILDDIR)/devinit_rom_sim: devinit_rom_sim.cpp ../src/devinit/Interpreter.cpp ../src/devinit/Interpreter.h | $(BUILDDIR)
	$(CXX) $(CXXFLAGS) $< ../src/devinit/Interpreter.cpp -o $@

$(BUILDDIR)/test_haiku_backend: test_haiku_backend.c os_shim/KernelExport.h os_shim/PCI.h ../src/os/HaikuBackend.c ../src/os/HaikuBackend.h | $(BUILDDIR)
	gcc -std=c11 -Wall -Wextra -Werror -fsanitize=undefined -fno-sanitize-recover=all -Ios_shim -I../src/os $< ../src/os/HaikuBackend.c -o $@

$(BUILDDIR)/test_identity_probe: test_identity_probe.c os_shim/KernelExport.h os_shim/PCI.h os_shim/Drivers.h ../src/os/HaikuProbe.c ../src/os/HaikuBackend.h | $(BUILDDIR)
	gcc -std=c11 -Wall -Wextra -Werror -fsanitize=undefined -fno-sanitize-recover=all -Ios_shim -I../src/os test_identity_probe.c ../src/os/HaikuProbe.c -o $@
