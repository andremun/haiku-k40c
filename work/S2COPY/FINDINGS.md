# S2COPY findings

All statements are from pinned sources. Nothing here ran on a card.

## Copy sequence (KNOWN, SOURCE_ONLY)

- The Linux kernel moves buffers on Kepler with class 0xa0b5 on subchannel 4
  (`reference/nouveau/nouveau_bo.c:937`, `include/nvif/push906f.h:19`).
- Object bind: method 0x0000 with `handle & 0xffff` (`nouveau_boa0b5.c:85`). The
  handle is `oclass | (engine << 16)` (`nouveau_bo.c:962-967`), so the value is 0xa0b5.
- Copy: eight methods from OFFSET_IN_UPPER 0x400 to LINE_COUNT 0x41c, then an
  immediate LAUNCH_DMA 0x300 (`nouveau_boa0b5.c:48-71`, `include/nvhw/class/cla0b5.h:37-109`).
- Launch value 0x386: NON_PIPELINED, FLUSH_ENABLE, source and destination PITCH,
  MULTI_LINE_ENABLE, both types VIRTUAL, no semaphore, no interrupt.
- Method header fields: `include/nvhw/class/cl906f.h:54-70`.

## Engine (KNOWN from source, INFERRED for the card)

- `nvkm/engine/ce/gk104.c` has no init, no firmware and no context function.
  `gk104_engn_ce` (`fifo/gk104.c:279-285`) has no `ctor` and no `bind`: a CE
  channel needs no engine context. INFERRED: the S1 channel can run a copy with no
  further set-up. Only the card can confirm it (ladder rung 3).
- Errors: interrupt status 0x104908 bit 2 and launch error code 0x104f14
  (`ce/gk104.c:52,64-76`). The driver reads both. It enables and clears nothing.
- Engine busy: bit 31 of 0x002640 + id*8 (`fifo/gk104.c:206-208`). The engine ID
  comes from the TOP entry of CE0 (`top/gk104.c:55-56`).

## UNKNOWN until rung 3

- Whether GP_GET reaches 2 before or after the copy ends. The driver waits for
  GP_GET, then for a not-busy engine, then compares.
- Whether bit 31 of the engine status clears after one copy with the channel still
  on the runlist. If it does not, the run fails its predicate with equal data
  (host test scenario "Busy"). The prebuilt diagnostic variant must drop this
  condition from the predicate and only record it. Not built yet: task LADDER.
- Whether the interrupt status register reads nonzero for events that are not
  errors. Bits 0 and 1 (BLOCKPIPE, NONBLOCKPIPE) are recorded and not part of the
  predicate.

## Design choices

- Read-only source entry, writable destination entry (`vmmgf100.c:313-316`, bit 2).
- The compare runs through the slow window (`instmem/nv50.c:62-71`), not BAR1. It
  uses no new mapping and stays inside the reviewed upload path. Q7 is not used.
- A wrong destination word is journaled as a Compare event and latches no upload
  error, so that the mandatory teardown still runs.
- The arena now holds 16 records, its software capacity. S3 needs a larger ledger.
