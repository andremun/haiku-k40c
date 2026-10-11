# RESULT: D2 — GK104 page-table encoding (attempt 3 / completion)

## What was done

The encoding functions (`encodePte`, `encodePde`, `splitVa`, `encodeInstPdb`,
`encodeInstLimit`) and the `AddressSpace` model were written and reworked in
two prior sessions (see `work/D2/REVIEW.md`). That code passes the acceptance
test (74 checks).

This session completed the remaining four items:

1. **`tests/test_pagetable.cpp`** — 18 test functions, 31 CHECKs, covering:
   - `encodePte` with all flags, kind=0, NCOH target
   - `splitVa` at zero, 128 MiB boundary, last 40-bit address
   - `encodePde` with various null/VRAM/HOST combinations
   - Map → unmap → map again (same VA)
   - Two independent address spaces (no shared tables)
   - Large mapping crossing a directory boundary
   - `translate` at first and last byte of a page
   - Error cases: overlap, unmap unmapped, nonexistent table
   - `encodeInstPdb` VRAM, `encodeInstLimit` variants

2. **`tests/Makefile`** — added `test_pagetable` and `d2_accept` to `all`
   and build rules, following the existing D1 pattern.

3. **`docs/mmu-encoding.md`** — 147 lines: address-split diagram, PTE/PDE
   entry-bit tables with source line references, two worked examples
   (small-page VRAM and large-page HOST), instance-block encoding,
   `AddressSpace` model summary, and a "Not covered" table (compression,
   sparse mappings, MMU flush, large-page/small-page coexistence).

4. **Handoff** — this `RESULT.md` and updated `STATUS.md`.

## Verification

```
make check
check_repo: 0 failure(s)
test_registerio: 49 checks, 0 failures
d1_accept: 57 checks, 0 failures
test_pagetable: 31 checks, 0 failures
d2_accept: 74 checks, 0 failures
```

## Files

| File | Lines | Description |
|------|-------|-------------|
| `src/mmu/PageTable.h` | 132 | Interface: constants, encoding functions, `AddressSpace` |
| `src/mmu/PageTable.cpp` | 414 | Implementation of all functions |
| `tests/test_pagetable.cpp` | ~260 | 31 own CHECKs |
| `tests/Makefile` | ~35 | Updated with D2 targets |
| `docs/mmu-encoding.md` | 147 | Address-split, entry bits, examples, not-covered |
| `work/D2/PLAN.md` | ~30 | This session's plan |
| `work/D2/REVIEW.md` | 57 | Previous session reviews (6 defects) |
