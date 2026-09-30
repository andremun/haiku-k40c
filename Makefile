# make check: repository format checks plus host-side tests (if present).
.PHONY: check test
check:
	python3 tools/check_repo.py
	@if [ -f tests/Makefile ]; then $(MAKE) -s -C tests; fi
	@if ls tests/test_*.py >/dev/null 2>&1; then python3 -m pytest -q tests; fi

test:
	@if [ -f tests/Makefile ]; then $(MAKE) -C tests; fi
