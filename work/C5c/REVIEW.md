# Review C5c (scaffold, 2026-10-13): ACCEPT after corrections by the reviewer

Second start of the task (the first one is described in the task state
of 2026-10-13 and in `docs/tasks/C5c.md`). 2 h 19 min, five commits in
the planned order, no compaction before the document was written.

Correct as delivered: the 14 steps with their lines and registers and
the 12 rows of "Verified values" (line, operation, register, name,
value), all compared with the trace by `make check`. The session did
not read the checker.

Corrected by the reviewer, each against the Nouveau source:

- `0x800010 = 0x802cf302` was explained as "bits 23:12 instance address,
  bits 11:0 channel ID 2". Wrong: the value is
  `0x80000000 | inst->addr >> 12` (`engine/fifo/gk104.c:68`); the channel
  ID is in the register offset.
- `0x002270 = 0x2cf325` was explained as "target 2". The target is 0
  (`gk104.c:446`). `0x002274` is `(runl->id << 20) | count` (`gk104.c:447`).
- The FECS command at lines 726186-726187 was attributed to
  `gf100_gr_fecs_bind_pointer` (command 3) and the value 1 listed as an
  open question. It is command 1 of `gf100_grctx_generate`
  (`engine/gr/ctxgf100.c:1506-1510`, with the write to `0x409840` and
  the wait on `0x409800` that the trace also shows): the golden context.
- `0x800014 = 0x400` was called "disable". Bit 10 is the enable of
  `gk104_chan_start`; bit 11 (`0x800`) is the stop. Step 11 is a stop
  followed by a start, not the final stop.
- The PCI ID (10de:10fc) was wrong: 10de:1024.
- "Consequences" assigned the runlist and the interrupt handling to
  `src/fifo/PushBuffer.h` and the channel sequence to
  `src/hw/RegisterIO.h`. Rewritten: each item names the design
  document that it confirms or changes.
- "Not known" rewritten: two of the three items were answered by the
  source.

Finding for later tasks: the agent copies values from a tool reliably,
and explains them unreliably even with the source line in front of it.
Ask it for the first; give it the source lines, or do it in review, for
the second.
