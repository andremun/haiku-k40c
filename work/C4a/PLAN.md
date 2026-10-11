# Plan: C4a Source provenance of driver constants

## Goal
Add source citations to every constant line in `src/mmu/*` and `src/fifo/*`,
write `tools/provenance.py`, and generate `docs/register-provenance.md`.

## Steps

1. Run `tools/provenance.py --missing` to identify all uncited constant lines.
2. Add citations to `src/mmu/PageTable.h` (line 19 `constexpr` + hex constants,
   line 40 `kPteUnmapped=0`, line 43 `kLptInvalid=2`, line 113 field comment).
3. Add citations to `src/mmu/PageTable.cpp` (lines with hex constants in encodePte/encodePde).
4. Add citations to `src/fifo/PushBuffer.h` (kPushMaxLength, kUserdGpGet, kUserdGpPut, kGpEntryBytes, HeaderType enum values).
5. Add citations to `src/fifo/PushBuffer.cpp` (header bases, masks, bit shifts).
6. Write `tools/provenance.py` with `--check` mode.
7. Write `docs/register-provenance.md` by running the tool.
8. Run `make check` — fix failures.
