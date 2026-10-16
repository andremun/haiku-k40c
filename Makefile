# make check: repository format checks plus host-side tests (if present).
.PHONY: check test haiku-selftest
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
