# FIFO Design (GK110 Command Engine Scheduler)

## Goal

Initialize the GK110 FIFO engine so that the GPU can execute command
buffers through PBDMA units — the S1 milestone (FIFO ready). Five steps:
enable master control interrupts, set the USERD base address, initialize
the run queues (PBDMA), acknowledge and enable FIFO interrupts, and
configure the engine context tables for GR and CE engines.

## What Nouveau does

1. **FIFO constructor** — `gk110_fifo_new` (`nvkm/engine/fifo/gk110.c:128`)
   creates the FIFO subdevice and calls the parent constructor with the
   GK110 function table.
2. **Function table** — `gk110_fifo` (`nvkm/engine/fifo/gk110.c:107`)
   defines `.chid_nr`, `.chid_ctor`, `.runq_nr`, `.runl_ctor`, `.init`,
   `.init_pbdmas`, `.intr`, `.nonstall`, `.runl`, and `.runq` members.
3. **Channel-ID constructor** — `gk110_fifo_chid_ctor`
   (`nvkm/engine/fifo/gk110.c:95`) calls `nvkm_chid_new` to create the
   channel-ID allocator with the FIFO channel event type.
4. **Runlist constructor** — `gk104_fifo_runl_ctor`
   (`nvkm/engine/fifo/gk104.c:756`) iterates over top devices with valid
   runlists and constructs per-runlist structures.
5. **FIFO init** — `gk104_fifo_init` (`nvkm/engine/fifo/gk104.c:744`)
   writes the USERD base in BAR1 to register `0x002254` when USERD is
   in BAR1, then writes `0xffffffff` to `0x002100` (interrupt status)
   and `0x7fffffff` to `0x002140` (interrupt enable).
6. **PBDMA init** — `gk104_fifo_init_pbdmas`
   (`nvkm/engine/fifo/gk104.c:735`) writes a mask to select which PBDMA
   units to enable and clears their interrupt-pending bits.
7. **Interrupt handler** — `gk104_fifo_intr` (`nvkm/engine/fifo/gk104.c:652`)
   reads the interrupt status register `0x002100` masked by `0x002140`,
   dispatches to bind handler for bit 1, and to PIO error handler for
   bit 4.
8. **Nonstall init** — `gf100_fifo_nonstall_allow`
   (`nvkm/engine/fifo/gf100.c:440`) enables nonstall interrupts by
   setting bit 31 of register `0x002140`.
9. **Nonstall fini** — `gf100_fifo_nonstall_block`
   (`nvkm/engine/fifo/gf100.c:451`) disables nonstall interrupts by
   clearing bit 31 of register `0x002140`.
10. **Runlist update** — `nv50_runl_update` (`nvkm/engine/fifo/nv50.c:285`)
    allocates a RAMDT buffer, maps it, and calls `insert_cgrp` and
    `insert_chan` to populate entries for each channel group and channel.
11. **Runlist insert channel** — `gk104_runl_insert_chan`
    (`nvkm/engine/fifo/gk104.c:452`) writes the channel ID into the
    runlist buffer at the given offset.
12. **Runlist commit** — `gk104_runl_commit`
    (`nvkm/engine/fifo/gk104.c:430`) programs the hardware with the
    runlist base address and entry count via MMIO registers.
13. **Runlist pending** — `gk104_runl_pending`
    (`nvkm/engine/fifo/gk104.c:422`) reads a runlist status register
    (`0x002284 + runl->id * 0x08`) and tests bit 20 for pending update.
14. **Runlist allow** — `gk104_runl_allow` (`nvkm/engine/fifo/gk104.c:410`)
    clears bit 0 of register `0x002630` for the runlist to allow
    scheduled channels.
15. **Runlist block** — `gk104_runl_block` (`nvkm/engine/fifo/gk104.c:416`)
    sets bit 0 of register `0x002630` for the runlist to block
    scheduled channels.
16. **Runlist wait** — `nv50_runl_wait` (`nvkm/engine/fifo/nv50.c:224`)
    polls the runlist update-pending bit with a timeout and returns
    success or `-ETIMEDOUT`.
17. **Runlist fault clear** — `gk104_runl_fault_clear`
    (`nvkm/engine/fifo/gk104.c:404`) writes the runlist ID bit to
    register `0x00262c` to clear pending faults.
18. **Run queue init** — `gk104_runq_init` (`nvkm/engine/fifo/gk104.c:379`)
    initializes the run queue base and writes interrupt masks and
    interrupt-enable masks to the run queue hardware registers.
19. **Run queue idle** — `gk104_runq_idle` (`nvkm/engine/fifo/gk104.c:289`)
    reads the run queue status register and tests bits 13 to 15 for
    idle state.
20. **Engine channel-switch** — `gk104_engn_chsw` (`nvkm/engine/fifo/gk104.c:259`)
    reads the engine status register and returns true when the engine is
    busy awaiting context-switch acknowledgement.
21. **Engine context-ID** — `gk104_engn_cxid` (`nvkm/engine/fifo/gk104.c:245`)
    reads the engine status and returns the channel ID of the channel
    currently loaded on the engine.
22. **Channel bind** — `gk104_chan_bind` (`nvkm/engine/fifo/gk104.c:72`)
    sets the runlist ID in channel control register at `0x800004` then
    writes the instance-block address to `0x800000`.
23. **Channel start** — `gk104_chan_start` (`nvkm/engine/fifo/gk104.c:48`)
    sets the channel-enable bit (`0x00000400`) in the channel control
    register at `0x800004 + chan->id * 8`.
24. **Channel stop** — `gk104_chan_stop` (`nvkm/engine/fifo/gk104.c:40`)
    clears the channel-enable bit (`0x00000800`) in the channel control
    register at `0x800004 + chan->id * 8`.
25. **RAMFC write** — `gk104_chan_ramfc_write` (`nvkm/engine/fifo/gk104.c:82`)
    writes 15 words into the instance block: USERD address (0x08, 0x0c),
    `0x0000face` (0x10), `0xfffff902` (0x30), command buffer address
    (0x48, 0x4c), `0x20400000` (0x84), devm mask (0x94), and other
    control values.
26. **USERD clear** — `gf100_chan_userd_clear` (`nvkm/engine/fifo/gf100.c:118`)
    maps the USERD memory, writes zero to ten shadow-register locations
    (0x040, 0x044, 0x048, 0x04c, 0x050, 0x058, 0x05c, 0x060, 0x088,
    0x08c), and unmaps the memory.
27. **MC init** — `nv50_mc_init` (`nvkm/subdev/mc/nv50.c:41`) writes
    `0xffffffff` to register `0x000200`, enabling all engine and
    subdevice interrupt bits.
28. **MC device enable** — `nv04_mc_device_enable` (`nvkm/subdev/mc/nv04.c:40`)
    sets mask bits in register `0x000200` to enable one engine and reads
    back.

## Haiku driver design

1. **Initialize master control** — Write `0xffffffff` to register
   `0x000200` via `RegisterIO::write32()` to enable all engine
   interrupts, replacing `nv50_mc_init` at line 41 of mc/nv50.c.
2. **Set USERD base** — Write the USERD base address (shifted right by
   12, OR'ed with `0x10000000`) to register `0x002254` via
   `RegisterIO::write32()`, replacing `gk104_fifo_init` at line 744 of
   gk104.c.
3. **Acknowledge FIFO interrupts** — Write `0xffffffff` to register
   `0x002100` via `RegisterIO::write32()` to clear all pending FIFO
   interrupts, following line 752 of gk104.c.
4. **Enable FIFO interrupts** — Write `0x7fffffff` to register `0x002140`
   via `RegisterIO::write32()` to enable FIFO interrupt bits, following
   line 753 of gk104.c.
5. **Initialize PBDMA units** — Write the PBDMA enable mask and clear
   interrupt-pending bits for each PBDMA unit, following
   `gk104_fifo_init_pbdmas` at line 735 of gk104.c.
6. **Initialize run queues** — Call `gk104_runq_init` logic: set the run
   queue base address, write interrupt masks and enable masks to the
   run queue hardware registers, following line 379 of gk104.c.
7. **Enable nonstall interrupts** — Set bit 31 of register `0x002140`
   via `RegisterIO::mask32()`, replacing `gf100_fifo_nonstall_allow` at
   line 440 of gf100.c.
8. **Build the channel control block** — For each channel, write the
   RAMFC state (15 words) into the instance block at offsets 0x08, 0x0c,
   0x10, 0x30, 0x48, 0x4c, 0x84, 0x94, 0x9c, 0xac, 0xe4, 0xe8, 0xb8,
   0xf8, 0xfc using `RegisterIO::write32()`, replacing
   `gk104_chan_ramfc_write` at line 82 of gk104.c.
9. **Bind the channel** — Write the instance-block address to channel
   register `0x800000` and the runlist ID to `0x800004` via
   `RegisterIO::write32()`, replacing `gk104_chan_bind` at line 72 of
   gk104.c.
10. **Start the channel** — Set bit `0x00000400` in channel register
    `0x800004 + chan->id * 8` via `RegisterIO::mask32()`, replacing
    `gk104_chan_start` at line 48 of gk104.c.
11. **Push-buffer encoding** — Use the `PushBuffer` class from
    `src/fifo/PushBuffer.h` to encode GPFIFO entries and build the
    command buffer that the PBDMA reads.
12. **Poll run queue idle** — Read the run queue status register and
    check bits 13–15 via `RegisterIO::read32()` to determine if the PBDMA
    is idle, following `gk104_runq_idle` at line 289 of gk104.c.
13. **Skip fault handling** — The MMU fault handler
    (`gf100_fifo_intr_mmu_fault_unit` at line 696 of gf100.c) and
    context-switch timeout handler (`gf100_fifo_intr_ctxsw_timeout` at
    line 618 of gf100.c) are not needed for S1; they are logging-only
    stubs.
14. **Skip the runlist update/commit** — The full runlist management
    (`nv50_runl_update` at line 285 of nv50.c, `gk104_runl_commit` at
    line 430 of gk104.c) is needed for S3 multi-channel scheduling but
    is not required for S1 single-channel compute.

## Haiku interfaces

1. `` `malloc()` `` — `os/SupportDefs.h` (via `<stdlib.h>`): allocates
   the FIFO subdevice structure, channel control blocks, and USERD
   memory; replaces `kzalloc`/`kmalloc` from Nouveau.
2. `` `free()` `` — `os/SupportDefs.h` (via `<stdlib.h>`): frees FIFO
   structures, channel blocks, and USERD memory; replaces `kfree`.
3. `` `snooze()` `` — `os/kernel/OS.h`: sleeps for a given number of
   microseconds; used for polling delays in the run queue idle check
   and runlist wait operations.
4. `` `memset()` `` — `os/SupportDefs.h` (via `<string.h>`): zeroes
   channel instance blocks and USERD shadow registers; replaces
   `memset` from Nouveau.
5. `` `dprintf()` `` — `os/kernel/debug.h`: prints debug messages for
   FIFO errors, PIO errors, and MMU fault conditions.

## Host tests

`tests/test_pushbuffer.cpp` covers the push-buffer encoding with 98
CHECK assertions, exercising GPFIFO entry encoding, descriptor types,
channel group entries, and GpFifo ring construction. The `d3_accept`
test provides 74 additional CHECKs for the complete push-buffer API.
These tests validate the `PushBuffer` class in `src/fifo/PushBuffer.h`,
which encodes GPFIFO entries and builds command buffers. A test for the
FIFO init sequence (writes to 0x002254, 0x002100, 0x002140, 0x002630)
would need to use `MockMMIO` to capture the register access log. A test
for the RAMFC write sequence (15 words to offsets 0x08–0xfc) would
require a `MockMMIO` with the instance-block memory region.

## Not known

- The exact meaning and purpose of the 15 RAMFC words written at
  `nvkm/engine/fifo/gk104.c:82` — most offsets (0x10, 0x30, 0x84,
  0x9c, 0xac, 0xb8, 0xf8, 0xfc) have no documented purpose in the
  source beyond the value they store. Only the USERD address (0x08,
  0x0c), command buffer address (0x48, 0x4c), and channel ID (0xe8)
  are clearly identifiable.
- The layout of the PBDMA run queue status register whose bits 13–15
  are polled by `gk104_runq_idle` at `nvkm/engine/fifo/gk104.c:289`
  — whether they represent queue depth, error state, or completion
  status is not established from the source.
- Which PBDMA units exist on GK110B and what the PBDMA enable mask
  should contain — `gk104_fifo_init_pbdmas` at
  `nvkm/engine/fifo/gk104.c:735` writes a mask but does not document
  which bits correspond to which PBDMA units.
- The exact format and size of the GPC (Graphics Processing Cluster)
  runlist group entry written by `gk110_runl_insert_cgrp` at
  `nvkm/engine/fifo/gk110.c:72` — the hardware bit-field layout is
  not traced beyond the function call.
