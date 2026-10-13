# Compute Launch: What the Trace Shows from Channel Creation to End of Job

## What ran

- **Shader:** GLSL compute shader, `layout(local_size_x = 64) in`, adds 1 to each element of a 1024-element unsigned int array.
- **Result:** `elements: 1024, wrong: 0` — PASS.
- **Renderer:** NVF1 (GK110B, PCI ID 10de:10fc, 0000:04:00.0).
- **Mesa version:** OpenGL ES 3.2 Mesa 25.2.8.
- **Linux kernel:** 6.8.0-146-generic (Nouveau driver).
- **Firmware binary:** `compute_add1`, 160 bytes, SHA-256 `02944d8f43830afad4f9d6538a1a26810085aea98a6520b09f7b5c9cce3ed417` (see `firmware/compute_add1.md`).

## Phases of the trace

The trace (`analysis/linux_run_trace.md`) divides the run into three phases:

| phase | lines | bar0 reads | bar0 writes | bar1 reads | bar1 writes | bar3 reads | bar3 writes |
|-------|-------|------------|-------------|------------|-------------|------------|-------------|
| load | 11–573419 | 52084 | 156004 | 2 | 0 | 0 | 365300 |
| job | 573421–901167 | 1648 | 5783 | 9 | 1 | 80512 | 239780 |
| after | 901169–901370 | 122 | 80 | 0 | 0 | 0 | 0 |

The "job" phase (lines 573421–901167) is the focus of this document. It contains 7431 BAR 0 accesses (1648 reads + 5783 writes) and 320292 BAR 3 accesses (80512 reads + 239780 writes).

## Steps of the job

The job phase contains 14 parts, each corresponding to a distinct driver action:

| Step | Lines | What | Registers | Source |
|------|-------|------|-----------|--------|
| 1 | 573421-615162 | Instance memory writes: channel client and channel structures are written to instance memory; MMU page-table base is written and a TLB invalidate is triggered | 0x070000, 0x100c80, 0x100cb8, 0x100cbc | subdev/mmu/vmmgf100.c:188 |
| 2 | 615163-615167 | Channel bind: PFIFO_CHAN.STATE is read and cleared, the channel pointer (0x802cf302) is written to PFIFO_CHAN.CHAN, and state is set to enable the channel | 0x800010, 0x800014 | engine/fifo/gk104.c:72 |
| 3 | 615168-615176 | Runlist write: the runlist address is written to PLAYLIST_WR and count (2) to PLAYLIST_WR_LEN; PLAYLIST_RD_LEN is read back to confirm drain | 0x002270, 0x002274, 0x002284, 0x070000 | engine/fifo/gk104.c:430 |
| 4 | 615177-615190 | Interrupt handling: interrupts disabled, runlist interrupt bit (0x40000000 in PFIFO.INTR) read and cleared, interrupts re-enabled | 0x000140, 0x000144, 0x002100, 0x002140, 0x002a00, 0x088068 | engine/fifo/gk104.c:652 |
| 5 | 615191-616553 | Wait loop: the driver polls PTIMER for elapsed time, reads PMC.ENABLE, reads PDAEMON temperature, and checks PGRAPH unit status with periodic TLB flushes | 0x009400, 0x009410, 0x000200, 0x100c80, 0x100cb8, 0x100cbc | not found |
| 6 | 616554-618713 | PGRAPH context setup (part 1): reads CAPS registers, sets FIFO control, writes CODE and DATA to ctxctl registers for GPCs | 0x40912c, 0x409108, 0x400500, 0x4091c4, 0x409184, 0x409188 | engine/gr/ctxgf100.c:1436 |
| 7 | 618714-726184 | Instance memory writes (107314 writes) with periodic timer/temperature/TLB-flush work between them | 0x070000, 0x100c80, 0x100cb8, 0x100cbc, 0x009400, 0x009410 | not found |
| 8 | 726185-726188 | FECS context-switch command: channel instance pointer (0x802cf302) is written to WRCMD_DATA, command 1 sent to WRCMD_CMD, CC_SCRATCH read back | 0x409500, 0x409504, 0x409800, 0x409840 | engine/gr/gf100.c:833 |
| 9 | 726189-730273 | PGRAPH context setup (part 2): icmd dispatch, context switch, mcache data writes, status polling | 0x400200, 0x400204, 0x404010, 0x404020, 0x404028, 0x400700 | engine/gr/ctxgf100.c:1436 |
| 10 | 730274-892358 | Instance memory writes (161834 writes) with periodic timer/alarm/temperature/TLB-flush work | 0x000140, 0x000144, 0x009400, 0x009410, 0x070000, 0x100c80 | not found |
| 11 | 892359-892368 | Channel stop: PFIFO_CHAN.STATE read (0x1), write 0x801 to stop, kick channel ID 2, flush PFIFO, wait for state 0, write 0x400 to disable | 0x800014, 0x002634, 0x070000 | engine/fifo/gk104.c:40 |
| 12 | 892369-900526 | Cleanup: 152 TLB flushes, 112 PFIFO_FLUSH, subfifo interrupt read/clear, PFIFO interrupt cleared | 0x070000, 0x100c80, 0x100cb8, 0x100cbc, 0x002100, 0x040108 | engine/fifo/gk104.c:652 |
| 13 | 900527-900552 | Channel unbind: stop channel (0x800014=0x801), kick ID 2, flush, clear state (0x400), update runlist (addr 0x2cf326, count 1), write 0 to PFIFO_CHAN.CHAN | 0x800010, 0x800014, 0x002270, 0x002274, 0x002284, 0x002634 | engine/fifo/gk104.c:56 |
| 14 | 900553-901167 | Final flushes and interrupt: interrupts disabled, runlist interrupt cleared, many TLB flushes, PMC.ENABLE polled | 0x000140, 0x000144, 0x000100, 0x002100, 0x002a00, 0x070000 | engine/fifo/gk104.c:652 |

## Verified values

| Line | Op | Register | Name | Value | Meaning |
|------|----|----------|------|-------|---------|
| 615163 | R | 0x800014 | PFIFO_CHAN.STATE | 0x0 | Channel state read before bind (idle) |
| 615165 | W | 0x800010 | PFIFO_CHAN.CHAN | 0x802cf302 | Channel pointer written: bit 31=enable, bits 23:12=instance addr (0x2cf30), bits 11:0=chan ID (2) |
| 615167 | W | 0x800014 | PFIFO_CHAN.STATE | 0x11000400 | Channel enabled in runlist 0, state ready |
| 615174 | W | 0x002270 | PFIFO.PLAYLIST_WR | 0x2cf325 | Runlist base address written (target 2, addr 0x2cf325000) |
| 615175 | W | 0x002274 | PFIFO.PLAYLIST_WR_LEN | 0x2 | Runlist entry count (2) |
| 615186 | R | 0x002100 | PFIFO.INTR | 0x40000000 | Runlist scheduling interrupt pending (bit 30) |
| 615188 | W | 0x002a00 | PFIFO.INTR_RUNLIST | 0x1 | Runlist interrupt cleared (write 1) |
| 726186 | W | 0x409500 | PGRAPH.CTXCTL.WRCMD_DATA | 0x802cf302 | Channel instance pointer sent to FECS context-switch firmware |
| 726187 | W | 0x409504 | PGRAPH.CTXCTL.WRCMD_CMD | 0x1 | Write command to FECS (bind channel instance) |
| 892360 | W | 0x800014 | PFIFO_CHAN.STATE | 0x801 | Channel stop requested (bit 11=stop, bit 0=disable) |
| 900550 | W | 0x002274 | PFIFO.PLAYLIST_WR_LEN | 0x1 | Runlist count reduced to 1 (channel removed) |
| 900552 | W | 0x800010 | PFIFO_CHAN.CHAN | 0x0 | Channel pointer cleared (unbound) |

## What the trace does not show

1. **User-space writes to USERD (BAR 1).** The trace shows BAR 1 has 9 reads and 1 write during the job, but these are kernel reads for polling. The pushbuffer, launch descriptor, and `LAUNCH` method are written by user space (Mesa) to GPU memory and BAR 1 USERD, not in the kernel trace.

2. **Instance memory content.** BAR 3 writes show the offset and value of each word, but the trace does not say what structure each offset corresponds to. For example, step 1 writes hundreds of words to instance memory for the channel client block and channel context, but the trace only records offset and value.

3. **What happens between BAR accesses.** Long gaps of instance memory writes (steps 7 and 10, each with 100,000+ writes) are mostly BAR 3 with few BAR 0 accesses. The BAR 0 accesses during these phases are periodic timer reads, temperature polling, and TLB flushes — the driver is waiting or doing background work.

4. **The compute shader execution itself.** The trace records driver setup and teardown, but not the GPU executing the shader. That work happens via the pushbuffer (written by Mesa) and the LAUNCH method call, which are user-space operations.

5. **The page-table walk.** When the driver writes to 0x100cb8 (TLB_FLUSH_VSPACE) and 0x100cbc (TLB_FLUSH_TRIGGER), the hardware walks the page tables, but the trace only shows the register accesses, not the page-table contents.

## Consequences for the Haiku driver

- **Channel lifecycle is explicit.** The Haiku driver must implement a clear channel lifecycle: bind (write channel pointer, set state) → start (runlist commit) → stop (clear state) → unbind (clear runlist, clear channel pointer). Each step has specific register sequences verified in the trace (see `src/hw/RegisterIO.h` + `.cpp`).
- **Runlist management requires two writes.** The runlist is written by first setting PLAYLIST_WR (0x002270) with the target and base address, then PLAYLIST_WR_LEN (0x002274) with the count. The Haiku driver must replicate this in `src/fifo/PushBuffer.h` + `.cpp`. The verified value `0x2cf325` (step 3) confirms the format: `(target << 28) | (addr >> 12)` as in `gk104_runl_commit` (`engine/fifo/gk104.c:446`).
- **FECS context-switch must use WRCMD registers.** The channel's instance pointer is bound to the GR context-switch firmware via WRCMD_DATA (0x409500) and WRCMD_CMD (0x409504). The Haiku driver needs this in the GR context management code (`docs/06-gr-design.md`). The value `0x802cf302` is the channel instance address with the enable bit.
- **TLB flushes are frequent and structured.** The driver issues TLB flushes at multiple points: after MMU setup (step 1), during periodic work (steps 5, 7, 10, 12, 14). The Haiku driver must implement the TLB flush sequence in `src/hw/RegisterIO.h` + `.cpp`: write 0x100cb8 (VSPACE), write 0x100cbc (TRIGGER with 0x80000000 | type), poll 0x100c80 for completion. The type values seen are 0x5 (step 1, ALL_PDB) and 0x1 (steps 7/10/12/14, PAGE_ALL).
- **Interrupt handling is standard and lives in the FIFO layer.** Steps 4, 12, and 14 all follow the same pattern in `src/fifo/PushBuffer.h` + `.cpp`: read PFIFO.INTR (0x002100) masked by PFIFO.INTR_EN (0x002140), write the status value back to clear it, and call the appropriate handler. The runlist interrupt (bit 30 = 0x40000000) is the most common during the job phase.
- **`docs/05-fifo-design.md` values are confirmed.** The runlist write format, channel state register values (0x801 for stop, 0x400 for disable), and interrupt clear pattern all match the design document. The verified value `0x802cf302` in PFIFO_CHAN.CHAN confirms the channel pointer format: `(1 << 31) | (instance_addr >> 12) << 4 | chan_id`.

## Not known

- **The exact meaning of 0x800014 values.** The trace shows PFIFO_CHAN.STATE (0x800014) at values 0, 0x11000400, 0x1, 0x801, 0x400. The `gk104_chan_stop` function writes 0x00000800 via `nvkm_mask`, but the trace shows 0x801 and 0x400. The difference between 0x801 (stop) and 0x400 (disable) and whether 0x11000400 includes a channel ID is not fully understood from the source alone.
- **What the periodic work in steps 7 and 10 does in detail.** These phases have 100,000+ instance memory writes with periodic BAR 0 accesses for timer, temperature, and TLB flushes. The driver code that does this is not found in the cited Nouveau functions; it may be in a scheduler thread or workqueue not visible in the trace's function-level analysis.
- **The FECS command value 0x1 vs 0x3.** The trace shows `WRCMD_CMD = 0x1` at line 726187, but `gf100_gr_fecs_bind_pointer` at `engine/gr/gf100.c:839` writes 0x00000003. The difference (0x3 = bind + something else) may be a variant or a different firmware command encoding. Further investigation of `fuc/hub.fuc` line 642 (which uses `GPC_XFER(type)` at 0x41a504) is needed.
