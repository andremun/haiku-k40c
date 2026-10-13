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
- How to look at the trace (never open the trace file or
  `analysis/linux_run_trace.json`; they are too large):
  - `analysis/linux_run_trace.md`: the mappings, the phases, the
    domains, and the timeline of the job as 509 runs. Read it in parts
    (`sed -n '1,80p'`, ...).
  - `python3 tools/trace_lines.py --runs FIRST LAST`: the runs that
    have a line in FIRST..LAST.
  - `python3 tools/trace_lines.py FIRST LAST`: the trace lines
    FIRST..LAST, decoded: `LINE TIME R|W BAR:OFFSET VALUE NAME`. Ask
    for 200 lines or fewer at a time. Add `--bar0` to see only the
    registers (BAR 0) and not the writes to instance memory (BAR 3).
  - `python3 tools/trace_lines.py --reg 0x800010`: every access of
    one register in the job.
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
     `| Step | Lines | What | Registers | Source |` with 8 rows or
     more, in the order of the trace.
     - `Lines` is `FIRST-LAST`, inside the job phase. The ranges do not
       overlap and each starts after the one before.
     - `Registers`: the BAR 0 registers that matter in these lines, as
       `0x......` (6 hex digits), separated by commas; or the words
       `instance memory only`. Each register must really be accessed
       in the lines of the row.
     - `What`: one sentence, in plain words, of what the driver does.
     - `Source`: the Nouveau function and `file.c:LINE` that does it,
       or `not found`.
     - The steps must include: the channel is bound to its instance
       block (the write to `0x800010`), the channel is enabled, the
       runlist is written, the graphics context of the channel is
       made (the long part with domain PGRAPH), the first command to
       the context-switch firmware with the channel's instance
       address (`0x409500` and `0x409504`), and the removal of the
       channel at the end.
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
- How to do it:
  - Write `work/C5c/PLAN.md` (10 lines).
  - Work through the timeline in order. Write `work/C5c/NOTES.md` as
    you go: for each part of the timeline, the line range, what you
    saw, the registers. Commit the notes after each part, so that the
    work can go on after an interruption. Write the document from the
    notes.
  - Copy line numbers and values from the tool output. Do not write a
    number from memory. Before the handoff, check each row of
    "Verified values" again with `tools/trace_lines.py LINE LINE`.
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
