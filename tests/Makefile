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

# Resident owner construction now binds freestanding POST image storage.
OWNER_POST_CORE := ../src/devinit/PostImage.cpp ../src/devinit/BoardPolicy.cpp ../src/devinit/Sha256.cpp
OWNER_POST_HEADERS := $(wildcard ../src/devinit/*.h)

CXX_TESTS := test_a7_diagnostics:devinit \
             test_bootstrap:runtime+memory test_prestart:runtime+memory \
             test_devinit:devinit s1a_accept:devinit test_board:devinit test_i2c:devinit test_post_image:devinit \
             test_memory:memory \
             test_s1_boundaries:fifo+hw+mmu test_s1_experiment:runtime+memory \
             test_registerio:hw d1_accept:hw \
             test_pagetable:mmu d2_accept:mmu \
             test_pushbuffer:fifo d3_accept:fifo \
             test_launchdesc:compute+fifo d5_accept:compute+fifo \
             ref_qmd:compute+fifo r1_accept:compute+fifo+hw+mmu
# The Python tests run once the tool of task D4 exists.
PY_TESTS  := $(if $(wildcard ../tools/compare_register_traces.py),$(wildcard test_compare_traces.py accept/d4_accept.py)) \
             accept/r1_accept.py test_dma_model.py test_observer.py test_observer_binding.py test_task_stream.py test_observer_supervisor.py test_d0_monitor.py test_d0_topology.py test_d0_evidence.py test_d0_kernel_log.py test_d0_run.py test_a7_run.py test_a7_omissions.py test_a7_install.py test_a7_i2c.py test_vm_tools.py test_owner_runner.py test_card_run.py test_board_tools.py test_devinit_inventory.py test_load_trace.py test_devinit_preflight.py test_devinit_closure.py test_post_policy.py test_devinit_rom.py test_devinit_trace_join.py

PROGRAMS := $(foreach t,$(CXX_TESTS),$(BUILDDIR)/$(firstword $(subst :, ,$(t))))

$(BUILDDIR)/test_a7_diagnostics: ../src/a7/PostDiagnostics.h

.PHONY: all clean
all: $(BUILDDIR)/test_a7_native $(BUILDDIR)/test_a7_client $(BUILDDIR)/test_map_owner_probe $(BUILDDIR)/owner_post_probe $(PROGRAMS) $(BUILDDIR)/post_probe $(BUILDDIR)/board_probe $(BUILDDIR)/devinit_rom_sim $(BUILDDIR)/test_haiku_backend $(BUILDDIR)/test_identity_probe $(BUILDDIR)/test_haiku_memory $(BUILDDIR)/test_native_owner $(BUILDDIR)/test_owner_probe
	@for p in $(BUILDDIR)/test_a7_native $(BUILDDIR)/test_a7_client $(BUILDDIR)/test_map_owner_probe $(PROGRAMS) $(BUILDDIR)/test_haiku_backend $(BUILDDIR)/test_identity_probe $(BUILDDIR)/test_haiku_memory $(BUILDDIR)/test_native_owner $(BUILDDIR)/test_owner_probe; do $$p || exit 1; done
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

$(BUILDDIR)/test_board: board_fake.h

$(BUILDDIR)/board_probe: board_probe.cpp board_fake.h $(wildcard ../src/devinit/*.cpp ../src/devinit/*.h) | $(BUILDDIR)
	$(CXX) $(CXXFLAGS) board_probe.cpp $(wildcard ../src/devinit/*.cpp) -o $@

$(BUILDDIR)/test_haiku_memory: test_haiku_memory.cpp ../src/os/HaikuMemory.cpp ../src/os/HaikuMemory.h ../src/os/HaikuBackend.h ../src/memory/Memory.cpp ../src/memory/Memory.h os_shim/KernelExport.h os_shim/PCI.h | $(BUILDDIR)
	$(CXX) $(CXXFLAGS) -Ios_shim test_haiku_memory.cpp ../src/os/HaikuMemory.cpp ../src/memory/Memory.cpp -o $@

$(BUILDDIR)/test_native_owner: test_native_owner.cpp os_shim/module.h os_shim/KernelExport.h $(wildcard ../src/os/NativeOwner.* ../src/os/HaikuOwnerModule.* ../src/os/OwnerClient.* ../src/os/HaikuMemory.* ../src/runtime/BootState.h) | $(BUILDDIR)
	$(CXX) $(CXXFLAGS) -Ios_shim test_native_owner.cpp ../src/os/NativeOwner.cpp ../src/os/HaikuOwnerModule.cpp ../src/os/OwnerClient.cpp ../src/os/HaikuMemory.cpp $(OWNER_POST_CORE) -o $@

$(BUILDDIR)/test_owner_probe: test_owner_probe.cpp os_shim/module.h os_shim/Drivers.h os_shim/KernelExport.h ../src/runtime/BootState.h ../tools/haiku/selftest/owner.cpp $(wildcard ../src/os/NativeOwner.* ../src/os/HaikuOwnerModule.* ../src/os/OwnerClient.* ../src/os/HaikuMemory.*) | $(BUILDDIR)
	$(CXX) $(CXXFLAGS) -Ios_shim test_owner_probe.cpp ../tools/haiku/selftest/owner.cpp ../src/os/NativeOwner.cpp ../src/os/HaikuOwnerModule.cpp ../src/os/OwnerClient.cpp ../src/os/HaikuMemory.cpp $(OWNER_POST_CORE) -o $@

$(BUILDDIR)/post_probe: post_probe.cpp board_fake.h $(wildcard ../src/devinit/*.cpp ../src/devinit/*.h) | $(BUILDDIR)
	$(CXX) $(CXXFLAGS) post_probe.cpp $(wildcard ../src/devinit/*.cpp) -o $@

$(BUILDDIR)/test_i2c $(BUILDDIR)/post_probe: i2c_wire.h board_fake.h

$(BUILDDIR)/test_native_owner $(BUILDDIR)/test_owner_probe: $(OWNER_POST_CORE) $(OWNER_POST_HEADERS)

$(BUILDDIR)/owner_post_probe: owner_post_probe.cpp i2c_wire.h board_fake.h $(wildcard ../src/devinit/*.h ../src/devinit/*.cpp ../src/os/NativeOwner.* ../src/os/OwnerPostSimulation.cpp ../src/os/HaikuMemory.*) | $(BUILDDIR)
	$(CXX) $(CXXFLAGS) -pthread -Ios_shim owner_post_probe.cpp ../src/os/NativeOwner.cpp ../src/os/OwnerPostSimulation.cpp ../src/os/HaikuMemory.cpp $(wildcard ../src/devinit/*.cpp) -o $@

$(BUILDDIR)/test_map_owner_probe: test_map_owner_probe.cpp ../tools/haiku/selftest/map_owner.cpp $(wildcard ../src/os/NativeOwner.* ../src/os/HaikuOwnerModule.* ../src/os/OwnerClient.* ../src/os/HaikuMemory.*) $(OWNER_POST_CORE) $(OWNER_POST_HEADERS) | $(BUILDDIR)
	$(CXX) $(CXXFLAGS) -Ios_shim test_map_owner_probe.cpp ../tools/haiku/selftest/map_owner.cpp ../src/os/NativeOwner.cpp ../src/os/HaikuOwnerModule.cpp ../src/os/OwnerClient.cpp ../src/os/HaikuMemory.cpp $(OWNER_POST_CORE) -o $@

# Actual A7 native platform/client against host failure-injection APIs only.
$(BUILDDIR)/test_a7_native: test_a7_native.cpp ../src/a7/NativePlatform.cpp ../src/a7/NativePlatform.h ../src/os/HaikuMemory.cpp $(wildcard a7_shim/*.h os_shim/*.h ../src/a7/*.h) | $(BUILDDIR)
	$(CXX) $(CXXFLAGS) -Ia7_shim -Ios_shim test_a7_native.cpp ../src/a7/NativePlatform.cpp ../src/os/HaikuMemory.cpp -o $@

$(BUILDDIR)/test_a7_client: test_a7_client.cpp ../tools/haiku/selftest/a7_client.cpp ../src/a7/Module.h $(wildcard a7_shim/*.h os_shim/*.h) | $(BUILDDIR)
	$(CXX) $(CXXFLAGS) -Ia7_shim -Ios_shim test_a7_client.cpp ../tools/haiku/selftest/a7_client.cpp -o $@
