# B3 Result: MMIO access extraction

## Summary

Extracted all 872 MMIO accesses (nvkm_rd32/wr32/mask) from 43 of the 88
files in `analysis/files.json` into `registers/mmio_accesses.json`.
`make check` passes with 0 failures.

## Counts

| Op | Count |
|---|---|
| rd32 | 288 |
| wr32 | 462 |
| mask | 122 |
| **Total** | **872** |

By subsystem: fifo 228, gr 467, fb 46, privring 23, pci 19, bar 15,
mc 14, ltc 30, bus 9, ce 8, imem 8, mmu 4, top 1.

587 of 872 register expressions are bare hex constants (`0x...`).
0 entries have `reg = null`.

## Bugs fixed during dev

1. **Nested calls misattributed**: Multi-line calls containing nested MMIO
   calls (e.g. `nvkm_error(... nvkm_rd32(...) ...)`) assigned all nested
   entries to the first line. Fixed by building a character-to-line offset
   map (`_build_line_map`) when joining lines and using it in
   `_extract_from_joined` to assign each call to its actual source line.

2. **Duplicate entries from double processing**: Multi-line calls starting
   on line N (detected inside `_extract_from_line`) caused the main loop to
   re-process line N+1 as its own MMIO line. Fixed by returning the
   `end_line` from `_extract_from_line` and using `i = max(i+1, end+1)`
   in the main loop to skip joined lines.

3. **875 vs 872 total**: The two bugs above produced 3 extra entries (lines
   342, 345, 349 in `nv04.c` each had a duplicate `rd32`). After fixes:
   872 entries, matching the expected count exactly.

## Files

- `tools/extract_mmio.py` — extraction tool with `--check` mode
- `registers/mmio_accesses.json` — 872 extracted entries
- `work/B3/PLAN.md` — task plan
