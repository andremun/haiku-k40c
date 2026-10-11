# PLAN: D2 remaining work

The code in `src/mmu/` is complete and the acceptance test (74 checks) passes.

## Steps

1. **`tests/test_pagetable.cpp`** — 15+ checks in the style of `test_registerio.cpp`:
   - `encodePte` with all flags set
   - `splitVa` at boundaries (0, first 128 MiB, last valid VA)
   - `encodePde` null combinations
   - Map then unmap then map again
   - Two independent address spaces (no shared tables)
   - Large mapping crossing a directory boundary
   - `translate` at the last byte of a page
   - `map` error: overlap
   - `unmap` error: unmapped page
   - `pte` accessor: `std::out_of_range` for non-existent table

2. **`tests/Makefile`** — add `d2_accept` and `test_pagetable` rules, run them in `all`.

3. **`docs/mmu-encoding.md`** — 50+ lines: address-split diagram, entry-bit table with source lines, worked example, "Not covered" section.

4. **Handoff** — `work/D2/RESULT.md`, update `docs/STATUS.md`, commit.

## Check

`make check` passes (acceptance test + own tests).
