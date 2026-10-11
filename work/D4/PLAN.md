# D4 Plan: Register-trace comparison tool

## Steps

1. **Write `tools/compare_register_traces.py`** — the core module with:
   - `parse_trace(text)` → list of (op, offset, value) tuples
   - `format_trace(trace)` → text
   - `convert_mmiotrace(text, bar0, size=0x1000000)` → list
   - `compare(expected, actual, ...)` → dict with equal/matched/mismatch
   - CLI: compare two traces, convert mmiotrace, --names for register names
2. Run `python3 tests/accept/d4_accept.py` after each function.
3. **Write `tests/test_compare_traces.py`** — 15+ own checks.
4. Add Python test to `tests/Makefile` (run with `python3`).
5. **Write `docs/register-traces.md`** — 40+ lines documentation.
6. Run `make check` and fix failures.

## Outputs
- `tools/compare_register_traces.py`
- `tests/test_compare_traces.py`
- `docs/register-traces.md`
