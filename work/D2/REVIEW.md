# Review of D2, attempt 1 (2026-10-12): REWORK, with the defects located

The session wrote `src/mmu/PageTable.h` and `PageTable.cpp` and then
stopped several times without output. The encoding functions are mostly
right. The acceptance test aborts with "Mapping overlaps existing
mapping". The scaffold read the code and found four defects. Fix exactly
these, compile the acceptance test after each, and do not write debug
programs.

1. **`splitVa`, the `spte` line.** It is `va & 0x7fff`. The small-page
   index is the 15 address bits above the 12 offset bits:
   `(va >> kSmallShift) & 0x7fff`. This is the cause of the overlap
   error: every address in one 4 KiB page gets a different index.
2. **`encodeInstPdb`, the `HOST` case.** There is a `break` at the end of
   the line `base |= 2ULL << 0;`, so the next line (bit 2, VOL) never
   runs. Remove that `break`. The test expects `0x40006`.
3. **`translate`, the address decode.** `typeMask` is wrong. A page table
   entry is `(phys >> 8) | type`; `phys` is a multiple of 4096 and below
   `1 << 40`, so `phys >> 8` is in bits 4 to 31 and everything else is
   type. Use `uint64_t phys = (pte & 0xfffffff0ULL) << 8;`. Delete the
   long comment above it.
4. **`translate`, two tables under one directory entry.** The loop
   returns "not mapped" as soon as the first table it finds has an empty
   entry. With a large-page table and a small-page table under the same
   entry it must look at both: replace `return std::nullopt;` after `if
   (pte == kPteUnmapped)` by `continue;`. Do the same for the size check
   two lines above it.

Then the rest of the task, which is not started: `tests/test_pagetable.cpp`
(15 checks or more), `tests/Makefile` (build and run all test programs),
`docs/mmu-encoding.md`, and the handoff. Read `docs/tasks/D2.md` again
for these.
