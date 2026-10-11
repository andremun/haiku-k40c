# Task C4a: Source provenance of the driver constants

Phase C: hardware database and firmware. This file is the whole task text. `make check` verifies the
checks named here. General rules: `AGENTS.md`. Paths to Nouveau files in
any output are relative to `reference/nouveau/`; line numbers are 1-based.

- Why: the rule of this project is that no hardware constant is
  invented. Every shift, mask, register offset and size in the driver
  code must name the line of Nouveau or Mesa that it comes from, so
  that a reviewer can check it and so that a later hardware test can
  mark it as verified. The code of phase D has such comments in
  `src/mmu/` and almost none in `src/fifo/`. This task completes them
  and writes the provenance table from them.
- Outputs: comments in `src/mmu/*` and `src/fifo/*` (comments only),
  `tools/provenance.py`, `docs/register-provenance.md`.
- What counts as a constant line: a line of a `.h` or `.cpp` file under
  `src/` (not `src/hw/`) whose code part (before `//`, with string
  literals removed) has a hex number of two digits or more (`0x1fff`) or
  the word `constexpr`.
- Every constant line needs, on the same line or in the comment lines
  directly above it, one of:
  - a citation `path/file.c:LINE` or `file.h:LINE`. Write enough of the
    path that exactly one file under `reference/nouveau/` or
    `reference/mesa/` ends with it (`vmmgf100.c:314` is enough;
    `gf100.c:10` is not, write `subdev/mmu/gf100.c:10`). The line must
    exist and must be the line that shows the value: open it and look,
    `sed -n 'LINEp' FILE`.
  - `no source: REASON` for a line that is plain arithmetic and not a
    hardware fact (for example a mask of 32 bits when a 64-bit value is
    split in two words).
- Where the constants of `src/fifo/` come from (read these, not more):
  `reference/mesa/src/gallium/drivers/nouveau/nvc0/nvc0_winsys.h` lines
  60 to 90 (header types, bit positions of count, subchannel and
  method), `nouveau_dma.c` lines 72 to 106 and `nouveau_dma.h` line 50
  (GPFIFO entry, length limit, USERD offsets), `nvkm/engine/fifo/gk104.c`
  lines 82 to 96 (the word at `0x4c`).
- Do not change code: only comments. `make -s -C tests` must still pass
  with the same numbers of checks.
- `tools/provenance.py` reads the constant lines and writes
  `docs/register-provenance.md`:
  - a short introduction (what the table is, what the statuses mean:
    `SOURCE_ONLY`, `TRACE_VERIFIED`, `HARDWARE_VERIFIED`,
    `HAIKU_VERIFIED`; all rows are `SOURCE_ONLY` now, because nothing
    has run on the card);
  - one table for each source file under `src/`, with one row for each
    constant line: `` | `src/fifo/PushBuffer.cpp:42` | the code of the
    line | tree and full path:line of the citation, or "no source:
    reason" | the text of the cited line | SOURCE_ONLY | ``. Replace
    `|` inside a cell by `\|`.
  - a last section "Open": the lines marked `no source`, and a
    sentence that says which constants a trace of task C5 can verify.
  - `tools/provenance.py --check` writes nothing and exits 0 when the
    document is what the tool generates. The same output on every run.
- How to do it:
  - Write `work/C4a/PLAN.md` (10 lines). Then the tool with a mode that
    lists the constant lines without a citation (`--missing`). Run it:
    it shows the work list. Add the comments file by file, then run
    `make check`.
  - If you cannot find the source of a constant, do not guess a line:
    write `no source: not found` and list it in `work/C4a/RESULT.md`.
  - The work directory is `work/C4a`. In `docs/STATUS.md` the task ID in
    the task log is `C4a`.
- Check: no constant line without a citation or `no source:`; every
  citation names exactly one file and an existing line; the document is
  what the tool generates and has a row for each constant line.
  The reviewer opens the cited lines.
