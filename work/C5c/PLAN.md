# Plan for C5c: What the trace shows from channel creation to end of job

## Goal
Write `docs/08-compute-launch.md` describing every step the Linux driver took during the reference compute run, tied to trace lines.

## Steps

### Part A — Build the 14-step table (appended to `work/C5c/steps.md`)
For each of the 14 steps (in order):
1. Run `python3 tools/trace_lines.py --regs <first> <last>` to see which BAR 0 registers are accessed.
2. For steps 2, 3, 4, 8, 11, 13: also run `--bar0` for the range to see the actual accesses.
3. For `0x800010` and `0x800014` (steps 2, 11, 13): run `--reg 0x800010`.
4. Search Nouveau for the function that does this: check `gk104_chan_bind`, `gk104_chan_start`, `gf100_gr_fecs_bind_pointer`, `gf100_gr_chan_new`, `gf100_grctx_generate`, `gk104_chan_stop`, `gk104_chan_unbind`, etc.
5. Append one table row to `work/C5c/steps.md` and 1–3 lines of tool output.
6. After steps 4, 8, 11, 14: `git add work/C5c && git commit`.

### Part B — Write the document
From `steps.md`, assemble `docs/08-compute-launch.md` with 7 sections:
- "What ran" (from `reference/linux-run/RESULT.txt` and `firmware/compute_add1.md`)
- "Phases of the trace" (from `analysis/linux_run_trace.md`)
- "Steps of the job" (14 rows from steps.md)
- "Verified values" (12+ rows, must include regs 0x800010, 0x800014, 0x002270, 0x002274, 0x409500, 0x409504)
- "What the trace does not show"
- "Consequences for the Haiku driver" (4+ items)
- "Not known" (3+ items)

### Part C — `make check` and fix
Run `make check`, fix failures by re-running tools (never guess numbers).

### Part D — Handoff
Write `work/C5c/RESULT.md`, update `docs/STATUS.md`, commit.
