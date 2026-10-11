# D2 Plan: GK104 page-table encoding

## Source references
- PTE: vmmgf100.c:32 `(addr >> 8) | map->type`, vmmgf100.c:237-319 (type bits)
- PDE: vmmgf100.c:106-143 (target bits for large/small tables)
- Layout: vmmgk104.c:40, 47 (17/17 and 17/12 desc arrays)
- Instance: vmmgf100.c:341-362 (0x0200 base, 0x0208 limit)
- LPT invalid: vmmgk104.c:29 (BIT_ULL(1) = 2)

## Steps
1. Write `src/mmu/PageTable.h` — all types, constants, and class declarations.
2. Write `src/mmu/PageTable.cpp` — implementation of encoding functions and AddressSpace.
3. Build + run acceptance test: `g++ -std=c++17 -Wall -Wextra -Werror -Isrc tests/accept/d2_accept.cpp src/mmu/*.cpp -o build/d2 && build/d2`.
4. Write `tests/test_pagetable.cpp` — 15+ checks (map/unmap/re-map, two address spaces, crossing boundary, last-byte translate, all-flags encode).
5. Update `tests/Makefile` — add D2 targets.
6. Write `docs/mmu-encoding.md` (50+ lines) — split diagram, entry-bit table, worked example, "Not covered".
7. Run `make check` and fix.
