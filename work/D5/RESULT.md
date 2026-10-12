# Task D5 Result — Launch descriptor and compute method encoding

**Date:** 2026-10-12

## What was done

1. **Fixed two assertion errors in `tests/test_launchdesc.cpp`:**
   - Test 1 (cross-word get): bits 63–40 of `0xDEADBEEF` are `0xDEADBE`
     (24 bits), not `0xDEADB` (20 bits).
   - Test 6 (encodeDecode): address `0xABCDEF000 >> 8 = 0x0ABCDEF0`,
     not `0xABCDEF`. The `encodeLaunch` encoder shifts the GPU address
     right by 8 bits; `decodeBuffer` recovers the shifted value as-is.

2. **Verified all tasks are complete:**
   - Source citations: `provenance.py --check` passes (0 uncited lines).
   - Own tests: `tests/test_launchdesc.cpp` has 16 categories, 56 CHECKs.
   - Acceptance test: `d5_accept` passes 101 checks, 0 failures.
   - Makefile: `test_launchdesc:compute+fifo` and `d5_accept:compute+fifo`
     added to `CXX_TESTS`.
   - Documentation: `docs/launch-descriptor.md` written (108 lines) with
     field table, constant-buffer table, launch methods table, "Not
     covered" section.

## make check result

```
python3 tools/check_repo.py — 0 failures
test_registerio: 49 checks, 0 failures
d1_accept: 57 checks, 0 failures
test_pagetable: 31 checks, 0 failures
d2_accept: 74 checks, 0 failures
test_pushbuffer: 98 checks, 0 failures
d3_accept: 74 checks, 0 failures
test_launchdesc: 56 checks, 0 failures
d5_accept: 101 checks, 0 failures
```

## Files modified

- `tests/test_launchdesc.cpp` — two assertion corrections (lines 42, 107)

## Files produced

- `docs/launch-descriptor.md` — 108 lines, full documentation

## Files not modified

- `src/compute/LaunchDesc.h` — header unchanged (scaffold wrote it)
- `src/compute/LaunchDesc.cpp` — implementation unchanged (session 2)
- `tests/accept/d5_accept.cpp` — acceptance test never edited
- `tests/Makefile` — updated by scaffold (session 2)

## Open questions

None.
