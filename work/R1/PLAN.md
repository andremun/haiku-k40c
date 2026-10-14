# R1 Plan: Fix review defects F1–F7

## Steps (in order)

1. **F3 (PageTable.cpp)** — Validate shift before `1ULL << shift`; use subtraction-based bounds for va+size and phys+size; reject phys >= 2^40.
2. **F1 (PageTable.cpp)** — Overlap check must cover the full interval of both page sizes, not just page starts.
3. **F2 (PageTable.cpp)** — Reject unmap when page size doesn't match the mapping.
4. **F5 (LaunchDesc.cpp)** — Promote to 64-bit before adding 0xFF in fld_shared_mem; validate localMemLow width; reject Qmd::get with width > 64.
5. **F6 (PushBuffer.cpp/.h)** — Add pending-packet guard to bindObject(); add finishedWords().
6. **F7 (RegisterIO.cpp)** — Use stoull with pos; reject out-of-range, partial tokens, negatives, trailing tokens.
7. **F4 (qmd_compare.py)** — Reject unknown fields/values/duplicates/short lists/bad words; verify output files; replace eval().
8. Build, run all tests, run make check, commit.
