# R1 Result: Fix review defects F1–F7

## F1 — PageTable.cpp, AddressSpace::map()
Overlap check now iterates individual PTE entries instead of entire table ranges, and checks both directions (existing PTE VA within new range, and new VA within existing PTE range) to detect mixed-page-size overlaps without false positives.

## F2 — PageTable.cpp, AddressSpace::unmap()
Rejects unmap with a page size that does not match the mapping by verifying each page exists with the correct page size before clearing any PTEs.

## F3 — PageTable.cpp, AddressSpace::map()
Validates page shift before any `1ULL << shift`; uses subtraction-based bounds checks for va+size and phys+size; added `physBeyond40bits()` helper to reject physical addresses beyond 40 bits.

## F5 — LaunchDesc.cpp, fld_shared_mem() / fld_local_mem_low() / Qmd::get()
Promotes to 64-bit before adding 0xFF in `fld_shared_mem`; `fld_local_mem_low()` validates 24-bit width before masking; `Qmd::get` rejects width > 64.

## F6 — PushBuffer.cpp / PushBuffer.h
`bindObject()` throws `std::logic_error` when a packet still waits for data; added `finishedWords()` method that throws when `pending() > 0`.

## F7 — RegisterIO.cpp, parseTrace()
Uses `std::stoull` with `pos` argument; validates 32-bit range, no partial tokens, no negatives, no trailing tokens (unless followed by `#` comment).

## F4 — tools/qmd_compare.py
Complete rewrite: `argparse` CLI with `--reference`, `--words`, `--header`, `--out-json`, `--out-md`, `--verify`, `--check`; recursive descent `compute_expr()` replaces `eval()`; rejects unknown fields/values/duplicates/short lists/bad words; `--verify` checks all fields match and output files are correct.

## Test counts (from `make -s -C tests`)
- test_registerio: 49 checks, 0 failures
- d1_accept: 57 checks, 0 failures
- test_pagetable: 31 checks, 0 failures
- d2_accept: 74 checks, 0 failures
- test_pushbuffer: 98 checks, 0 failures
- d3_accept: 74 checks, 0 failures
- test_launchdesc: 56 checks, 0 failures
- d5_accept: 101 checks, 0 failures
- ref_qmd: 10 checks, 0 failures
- r1_accept: 33 checks, 0 failures
- test_compare_traces: 17 checks, 0 failures
- d4_accept: 38 checks, 0 failures
- r1_accept.py: 11 checks, 0 failures

## make check
0 failures. All checks pass.
