# Result: Task C5c — What the trace shows from channel creation to end of job

## Document: `docs/08-compute-launch.md`

The document has 7 sections:

1. **What ran** — GLSL compute shader, 1024 elements, PASS; NVF1 renderer (GK110B, 10de:1024); Mesa 25.2.8; kernel 6.8.0-146-generic; firmware `compute_add1` (160 bytes).
2. **Phases of the trace** — Three phases: load (52084 BAR 0 reads), job (7431 BAR 0 accesses), after (122 BAR 0 reads). The job phase is the focus.
3. **Steps of the job** — 14-step table covering instance memory writes, channel bind, runlist write, interrupt handling, wait loop, PGRAPH context setup (2 parts), instance memory writes with periodic work, FECS context-switch, channel stop, cleanup, channel unbind, and final flushes. Each step has line ranges, register lists, and Nouveau source references.
4. **Verified values** — 12 rows tying specific trace lines to register reads/writes: PFIFO_CHAN.STATE (0x800014), PFIFO_CHAN.CHAN (0x800010), PFIFO.PLAYLIST_WR (0x002270), PFIFO.PLAYLIST_WR_LEN (0x002274), PFIFO.INTR (0x002100), PFIFO.INTR_RUNLIST (0x002a00), PGRAPH.CTXCTL.WRCMD_DATA (0x409500), PGRAPH.CTXCTL.WRCMD_CMD (0x409504).
5. **What the trace does not show** — User-space USERD writes, instance memory content, inter-access gaps, GPU execution, page-table walks.
6. **Consequences for the Haiku driver** — 6 items covering channel lifecycle, runlist management, FECS context-switch, TLB flushes, interrupt handling, and design document confirmation. Each names a repository file.
7. **Not known** — 5 items (rewritten in the review).

## Three most important findings for the Haiku driver (rewritten in the review, see REVIEW.md)

1. **The channel sequence of `docs/05-fifo-design.md` is confirmed with real values.** Bind: `0x800010 = 0x802cf302` (`0x80000000 | inst->addr >> 12`; the channel ID 2 is in the register offset). Start: bit 10 of `0x800014`. Runlist: `0x002270 = 0x2cf325`, `0x002274 = 2`. Removal: bit 11, kick through `0x002634`, runlist with 1 entry, `0x800010 = 0`.
2. **The first job of a channel generates the golden context.** The FECS command in the trace is command 1 of `gf100_grctx_generate` (`engine/gr/ctxgf100.c:1508`) between two PGRAPH parts of about 6,200 register accesses. This is the largest piece of work between S2 and S3.
3. **The trace does not verify the pushbuffer or the launch descriptor.** Both are written by user space. The descriptor that Mesa printed is in `firmware/compute_add1.md`; comparing it with `src/compute/LaunchDesc.cpp` is the open check for S3.
