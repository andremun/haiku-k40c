# Task C5c: What the trace shows from channel creation to the end of the job

Phase C: hardware database and firmware. This file is the whole task text. `make check` verifies the
checks named here. General rules: `AGENTS.md`. Paths to Nouveau files in
any output are relative to `reference/nouveau/`; line numbers are 1-based.

- Why: the register trace of the reference run is the only record of
  what a working driver does on this card, in order, with the real
  values. The Haiku driver must do the same things for milestones S2
  (a channel) and S3 (a compute job). This task writes
  `docs/08-compute-launch.md`: what the kernel driver did while the
  job ran, with every statement tied to lines of the trace.
- Output: `docs/08-compute-launch.md`. Nothing else (no tool, no code).
- How to look at the trace. Never open the trace file,
  `analysis/linux_run_trace.json` or `analysis/linux_run_trace.md`
  (they are too large and fill your context). Use only these commands,
  with the line ranges of the table "The 14 parts of the job" below:
  - `python3 tools/trace_lines.py --regs FIRST LAST`: the different
    BAR 0 registers of the range with reads, writes, the first line
    and the name. Short. Use this first for each part.
  - `python3 tools/trace_lines.py --reg 0x800010`: every access of
    one register in the job, with line and value.
  - `python3 tools/trace_lines.py FIRST LAST --bar0`: the accesses
    themselves, `LINE TIME R|W BAR:OFFSET VALUE NAME`. At most 60
    lines are printed. Use it for small ranges (50 lines or fewer).
  - Names: the NAME column is from the register database. `-` means
    that the database has no name. Do not invent one.
- What you can know and what not:
  - BAR 0 is the registers. BAR 3 is instance memory: the kernel
    writes page tables, the channel's instance block and the graphics
    context there. The trace shows the offset and the value of such a
    write, not what structure it belongs to. Say "writes to instance
    memory" and give the mapping number; do not say what the words
    mean unless a Nouveau source line shows it.
  - BAR 1 in this trace is the kernel's view of the channel control
    area (USERD). User space (Mesa) has its own mapping, and its
    writes are not in the trace. The pushbuffer, the launch descriptor
    and the `LAUNCH` method are written by Mesa to GPU memory: they
    are not in the trace. `firmware/compute_add1.md` (task C5a) has
    the launch descriptor.
  - The job phase is the lines between the two markers
    (`analysis/linux_run_trace.md`, section "Phases").
- Where to find what Nouveau does, to explain a step (read only the
  functions that you cite): channel creation and removal
  `nvkm/engine/fifo/gk104.c` (`gk104_chan_bind`, `gk104_chan_start`,
  `gk104_chan_stop`, `gk104_chan_unbind`, `gk104_runl_commit`); the
  flush register `nvkm/subdev/bar/gf100.c` or
  `nvkm/subdev/instmem/nv50.c`; the page-table flush
  `nvkm/subdev/mmu/vmmgf100.c` (`gf100_vmm_invalidate`); the graphics
  context `nvkm/engine/gr/gf100.c` (`gf100_gr_fecs_bind_pointer`,
  `gf100_gr_chan_new`) and `nvkm/engine/gr/ctxgf100.c`
  (`gf100_grctx_generate`). Use `grep -n` to find the line.
- The document has these `## ` sections, in this order:
  1. "What ran": the job, the result, the versions, the files (5 to
     10 lines; take the facts from `reference/linux-run/RESULT.txt`
     and `firmware/compute_add1.md`).
  2. "Phases of the trace": the three phases with their line ranges
     and numbers of accesses (from `analysis/linux_run_trace.md`).
  3. "Steps of the job": a table
     `| Step | Lines | What | Registers | Source |` with exactly the
     14 rows of the table "The 14 parts of the job" below, same `Step`
     and `Lines`.
     - `Registers`: 1 to 6 BAR 0 registers that matter in these lines,
       as `0x......` (6 hex digits), separated by commas. Take them
       from the output of `--regs` for the lines of the row; a
       register that is not accessed in these lines is an error.
     - `What`: one sentence, in plain words, of what the driver does.
     - `Source`: the Nouveau function and `file.c:LINE` that does it
       (write enough of the path, for example
       `engine/fifo/gk104.c:40`), or `not found`.
  4. "Verified values": a table
     `| Line | Op | Register | Name | Value | Meaning |` with 12 rows
     or more. Each row is one line of the trace, copied from the
     output of `tools/trace_lines.py`: the line number, `R` or `W`,
     the register `0x......`, the name (or `-`), the value as the
     tool prints it. `Meaning`: what the value is, from a Nouveau
     source line (`file.c:LINE`) or `not known`. The table must have
     rows for the registers `0x800010`, `0x800014`, `0x002270`,
     `0x002274`, `0x409500` and `0x409504`.
  5. "What the trace does not show": a list (see "What you can know").
  6. "Consequences for the Haiku driver": a list of 4 items or more.
     Each names a file of this repository that is affected
     (`` `src/...` `` or `` `docs/...` ``; the file must exist) and
     says what the trace confirms or what must change. Compare the
     values of "Verified values" with `docs/05-fifo-design.md`.
  7. "Not known": a list of 3 items or more.
- The 14 parts of the job (the reviewer made this division from the
  timeline; the hints say what to expect, verify them with `--regs`):

  | Step | Lines | Hint |
  |---|---|---|
  | 1 | 573421-615162 | almost only instance memory: structures of the new client and channel are written |
  | 2 | 615163-615167 | the channel is bound to its instance block and enabled (`0x800010`, `0x800014`) |
  | 3 | 615168-615176 | the runlist is written (`0x002270`, `0x002274`) |
  | 4 | 615177-615190 | an interrupt is handled (PMC, PFIFO) |
  | 5 | 615191-616553 | instance memory, then loops that read the timer and wait |
  | 6 | 616554-618713 | first long PGRAPH part |
  | 7 | 618714-726184 | 107,000 writes to instance memory; in between, periodic work that is not part of the job (timer, temperature) |
  | 8 | 726185-726188 | a command to the context-switch firmware (FECS) with the channel's instance address (`0x409500`, `0x409504`) |
  | 9 | 726189-730273 | second long PGRAPH part |
  | 10 | 730274-892358 | 161,000 writes to instance memory; periodic work in between |
  | 11 | 892359-892368 | the channel is stopped (`0x800014`) |
  | 12 | 892369-900526 | cleanup: flushes; an interrupt with PSUBFIFO registers |
  | 13 | 900527-900552 | the channel is removed: the runlist is written again, `0x800010` is cleared |
  | 14 | 900553-901167 | the rest: flushes and an interrupt |

- How to do it. The work is in small parts, and each part is saved in
  a file before the next one starts. Your context is small: after a
  compaction you know only what is in the files.
  - Write `work/C5c/PLAN.md` (10 lines).
  - Part A, the steps. For each of the 14 steps, one at a time: run
    `--regs` for its lines; for steps 2, 3, 4, 8, 11 and 13 also look
    at the accesses with `--bar0`; find the Nouveau function with
    `grep -n`; then APPEND the finished table row to
    `work/C5c/steps.md`, and under it 1 to 3 lines of the tool output
    that you want to use in "Verified values" (copied, not typed).
    After steps 4, 8, 11 and 14: `git add work/C5c && git commit`.
    If `work/C5c/steps.md` already has rows, go on with the next
    step: do not start again.
  - Part B, the document. Write `docs/08-compute-launch.md` from
    `work/C5c/steps.md`: the steps table from the rows, "Verified
    values" from the copied lines (12 rows or more). Then the other
    sections. Commit.
  - Part C: `make check`, fix what it reports, commit. For a failure
    about a register or a line, run the tool for that line again; do
    not change a number without the tool output.
  - Do not read `tools/check_repo.py` (AGENTS.md).
  - The work directory is `work/C5c`. In `docs/STATUS.md` the task ID in
    the task log is `C5c`. `work/C5c/RESULT.md`: what the document
    has, and the 3 most important findings for the Haiku driver.
- Check: the sections; every row of "Steps of the job" (ranges inside
  the job, in order, registers accessed in the range, the required
  steps); every row of "Verified values" against the trace (line,
  operation, register, name, value) and the required registers; the
  cited source lines exist; the named files exist. The reviewer reads
  the "What" and "Meaning" columns against the source.
