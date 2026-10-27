# make check: repository format checks plus host-side tests (if present).
.PHONY: help check test refs vm-tools-test haiku-selftest
help:
	@echo "make refs           restore the pinned reference sources into .refs (network)"
	@echo "make check          repository checks, source and generator checks, host tests (needs make refs)"
	@echo "make test           host tests only"
	@echo "make vm-tools-test  offline test of tools/haiku VM tools"
	@echo "make haiku-selftest load a test driver in the throw-away VM (about 2 minutes)"

refs:
	python3 tools/restore_verification_refs.py

vm-tools-test:
	python3 tests/test_vm_tools.py
	python3 tests/test_card_run.py

# The three devinit tools below read the private VBIOS image. CI skips them with
# task A3 in .check-skip, the same switch that tools/check_repo.py uses.
check:
	python3 tools/check_repo.py
	python3 tools/restore_verification_refs.py --check
	python3 tools/devinit_trace_join.py --check
	python3 tools/load_trace.py --check
	@if grep -qw A3 .check-skip 2>/dev/null; then \
		echo "devinit_inventory, devinit_preflight, devinit_sources, board_trace --check: NOT RUN (A3 in .check-skip, private VBIOS image)"; \
	else \
		python3 tools/devinit_inventory.py --check && \
		python3 tools/devinit_preflight.py --check && \
		python3 tools/devinit_sources.py --check && \
		python3 tools/board_trace.py --check; \
	fi
	@if [ -f tests/Makefile ]; then $(MAKE) -s -C tests; fi

test:
	@if [ -f tests/Makefile ]; then $(MAKE) -C tests; fi

# Build the toolchain test driver and load it in the Haiku test VM (about
# 2 minutes, no GPU). See docs/HAIKU_BUILD_TEST.md.
haiku-selftest:
	tools/haiku/build-driver.sh hello_pci tools/haiku/selftest/hello_pci.c
	tools/haiku/vm-test.sh build/haiku/hello_pci
