# Result: Task C5c — What the trace shows from channel creation to end of job

## Document: `docs/08-compute-launch.md`

The document has 7 sections:

1. **What ran** — GLSL compute shader, 1024 elements, PASS; NVF1 renderer (GK110B, 10de:10fc); Mesa 25.2.8; kernel 6.8.0-146-generic; firmware `compute_add1` (160 bytes).
2. **Phases of the trace** — Three phases: load (52084 BAR 0 reads), job (7431 BAR 0 accesses), after (122 BAR 0 reads). The job phase is the focus.
3. **Steps of the job** — 14-step table covering instance memory writes, channel bind, runlist write, interrupt handling, wait loop, PGRAPH context setup (2 parts), instance memory writes with periodic work, FECS context-switch, channel stop, cleanup, channel unbind, and final flushes. Each step has line ranges, register lists, and Nouveau source references.
4. **Verified values** — 12 rows tying specific trace lines to register reads/writes: PFIFO_CHAN.STATE (0x800014), PFIFO_CHAN.CHAN (0x800010), PFIFO.PLAYLIST_WR (0x002270), PFIFO.PLAYLIST_WR_LEN (0x002274), PFIFO.INTR (0x002100), PFIFO.INTR_RUNLIST (0x002a00), PGRAPH.CTXCTL.WRCMD_DATA (0x409500), PGRAPH.CTXCTL.WRCMD_CMD (0x409504).
5. **What the trace does not show** — User-space USERD writes, instance memory content, inter-access gaps, GPU execution, page-table walks.
6. **Consequences for the Haiku driver** — 6 items covering channel lifecycle, runlist management, FECS context-switch, TLB flushes, interrupt handling, and design document confirmation. Each names a repository file.
7. **Not known** — 3 items: meaning of 0x800014 values, periodic work details in steps 7/10, FECS command 0x1 vs 0x3 discrepancy.

## Three most important findings for the Haiku driver

1. **Channel lifecycle has a precise register sequence.** Bind writes 0x800010 (channel pointer 0x802cf302) then sets 0x800014 to 0x11000400. Stop writes 0x801 to 0x800014. Unbind clears 0x800010 to 0. These verified values in `src/hw/RegisterIO.h` must be replicated exactly for S2 (channel) milestone.

2. **Runlist is a two-write operation.** PLAYLIST_WR (0x002270) gets the target+address in format `(target << 28) | (addr >> 12)`, then PLAYLIST_WR_LEN (0x002274) gets the count. Verified value 0x2cf325 (step 3) confirms the encoding. This must be in `src/fifo/PushBuffer.h` for S3 (compute job).

3. **FECS context-switch uses WRCMD registers, not direct instance writes.** The channel instance pointer (0x802cf302) is sent to the GR context-switch firmware via WRCMD_DATA (0x409500) and WRCMD_CMD (0x409504, value 0x1). This is a distinct step between the two PGRAPH context setup phases, and the value 0x1 (not 0x3 as in some Nouveau paths) is what the hardware expects on this card.
