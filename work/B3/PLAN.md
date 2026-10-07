# B3 Plan: MMIO access extraction

## Goal
Extract every `nvkm_rd32`, `nvkm_wr32`, `nvkm_mask` call from the 88 files of
`analysis/files.json` (872 calls expected) into `registers/mmio_accesses.json`.

## Steps

1. Build a map of `file → subsystem` from `analysis/files.json`.
2. Scan every listed file in `reference/nouveau/` for lines matching
   `nvkm_(rd32|wr32|mask)\s*\(`. Join multi-line calls (open paren not closed).
3. For each call, extract: function name, op, reg expression, value, mask.
   - `reg` is the second argument text (the register expression).
   - `value` and `mask` are the remaining argument texts.
   - `reg_value` = int when `reg` is a bare hex constant (`0x...`), else `null`.
   - `function` = the C function containing the line (walk upward for `^func(`).
4. Sort output by file, then line. One entry per call instance (multi-call lines
   produce multiple entries with the same line number).
5. Write `registers/mmio_accesses.json` and the tool `tools/extract_mmio.py`
   with `--check` mode.
6. Run `make check`. Fix failures.
7. Write `work/B3/RESULT.md` with counts per subsystem, per op, and how many
   `reg` values are constants.
