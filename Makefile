# make check: repository format checks plus host-side tests (if present).
.PHONY: help check test refs vm-tools-test haiku-selftest
help:
	@echo "make refs           restore the pinned reference sources into .refs (network)"
	@echo "make check          repository checks and host tests (needs make refs)"
	@echo "make test           host tests only"
	@echo "make vm-tools-test  offline test of tools/haiku VM tools"
	@echo "make haiku-selftest load a test driver in the throw-away VM (about 2 minutes)"

refs:
	python3 tools/restore_verification_refs.py

vm-tools-test:
	python3 tests/test_vm_tools.py

check:
	python3 tools/check_repo.py
	@if [ -f tests/Makefile ]; then $(MAKE) -s -C tests; fi

test:
	@if [ -f tests/Makefile ]; then $(MAKE) -C tests; fi

# Build the toolchain test driver and load it in the Haiku test VM (about
# 2 minutes, no GPU). See docs/HAIKU_BUILD_TEST.md.
haiku-selftest:
	tools/haiku/build-driver.sh hello_pci tools/haiku/selftest/hello_pci.c
	tools/haiku/vm-test.sh build/haiku/hello_pci
