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

# Review of D2, attempt 2 (2026-10-12): the code is fixed, the rest is open

The rework session applied the four fixes and then stopped without
output again. The scaffold found and fixed the last two defects:

5. `map` did not check that `phys` is a multiple of the page size, so a
   call that must throw mapped a page, and a later valid call then failed
   with "overlaps". Added `validateAlign(phys, pageSize)`.
6. `map` kept pointers into `fTableRefs` and then called `push_back` on
   it, which can move the storage: the directory entry lost its
   large-page half. It now copies the two references.

The acceptance test passes: 74 checks, also with the address and
undefined-behaviour sanitizers. **Do not change `src/mmu/` any more.**

Left to do (nothing else):

1. `tests/test_pagetable.cpp`: 15 checks or more of your own, in the
   style of `tests/test_registerio.cpp` (see `docs/tasks/D2.md`).
2. `tests/Makefile`: add the two page-table test programs, as the file
   does for the register tests. `make -s -C tests` must exit 0.
3. `docs/mmu-encoding.md` (50 lines or more), as `docs/tasks/D2.md`
   describes.
4. `work/D2/RESULT.md` and the handoff.

# Review of D2, attempt 3 (2026-10-12): ACCEPT

The last session (41 minutes) wrote the tests, the Makefile rules and the
document, and left `src/mmu/` alone as asked. Acceptance test 74 checks,
own tests 31 checks, both also clean under the address and
undefined-behaviour sanitizers.

The scaffold corrected the worked examples of `docs/mmu-encoding.md`:
three of the numbers did not follow from the formulas beside them (the
second entry is `0x500800005`, the directory entry is `0x20100000311`),
and the instance-block note named the wrong bits.

Limits:

- Of the six code defects in this task, the agent found none by itself;
  the scaffold located all six. The model is correct against the
  acceptance test, which covers the cases listed in it and no others.
- The table "Not covered" names Nouveau functions for sparse mappings
  and for the large-page entry above small pages. These attributions are
  not verified.
