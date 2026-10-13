# Compute Launch: What the Trace Shows from Channel Creation to End of Job

## What ran

- **Shader:** GLSL compute shader, `layout(local_size_x = 64) in`, adds 1 to each element of a 1024-element unsigned int array.
- **Result:** `elements: 1024, wrong: 0` — PASS.
- **Renderer:** NVF1 (GK110B, PCI ID 10de:1024, 0000:04:00.0).
- **Mesa version:** OpenGL ES 3.2 Mesa 25.2.8.
- **Linux kernel:** 6.8.0-146-generic (Nouveau driver).
- **Shader binary:** `compute_add1`, 160 bytes, SHA-256 `02944d8f43830afad4f9d6538a1a26810085aea98a6520b09f7b5c9cce3ed417` (see `firmware/compute_add1.md`).

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
| 2 | 615163-615167 | Channel bind and start: the runlist ID is set in the state register, the address of the instance block is written to the channel register of channel 2, and bit 10 of the state register enables the channel | 0x800010, 0x800014 | gk104_chan_bind engine/fifo/gk104.c:72, gk104_chan_bind_inst engine/fifo/gk104.c:68, gk104_chan_start engine/fifo/gk104.c:52 |
| 3 | 615168-615176 | Runlist commit: the address of the new runlist is written to PLAYLIST_WR and the number of entries (2) to PLAYLIST_WR_LEN; PLAYLIST_RD_LEN is read to wait for the change | 0x002270, 0x002274, 0x002284, 0x070000 | gk104_runl_commit engine/fifo/gk104.c:430 |
| 4 | 615177-615190 | Interrupt handling: interrupts disabled, runlist interrupt bit (0x40000000 in PFIFO.INTR) read and cleared, interrupts re-enabled | 0x000140, 0x000144, 0x002100, 0x002140, 0x002a00, 0x088068 | engine/fifo/gk104.c:652 |
| 5 | 615191-616553 | Instance memory writes, then wait loops: the driver reads the timer (PTIMER) between polls of registers that have no name in the database; what it waits for is not known | 0x009400, 0x009410, 0x000200, 0x100c80, 0x100cb8, 0x100cbc | not found |
| 6 | 616554-618713 | PGRAPH context setup (part 1): reads CAPS registers, sets FIFO control, writes CODE and DATA to ctxctl registers for GPCs | 0x40912c, 0x409108, 0x400500, 0x4091c4, 0x409184, 0x409188 | engine/gr/ctxgf100.c:1436 |
| 7 | 618714-726184 | Instance memory writes (107314 writes) with periodic timer/temperature/TLB-flush work between them | 0x070000, 0x100c80, 0x100cb8, 0x100cbc, 0x009400, 0x009410 | not found |
| 8 | 726185-726188 | Golden context generation: the address of the instance block (0x802cf302) is written to WRCMD_DATA and command 1 to WRCMD_CMD of the context-switch firmware (FECS); the driver then reads CC_SCRATCH until bit 31 is set | 0x409500, 0x409504, 0x409800, 0x409840 | gf100_grctx_generate engine/gr/ctxgf100.c:1507 |
| 9 | 726189-730273 | PGRAPH context setup (part 2): icmd dispatch, context switch, mcache data writes, status polling | 0x400200, 0x400204, 0x404010, 0x404020, 0x404028, 0x400700 | engine/gr/ctxgf100.c:1436 |
| 10 | 730274-892358 | Instance memory writes (161834 writes) with periodic timer/alarm/temperature/TLB-flush work | 0x000140, 0x000144, 0x009400, 0x009410, 0x070000, 0x100c80 | not found |
| 11 | 892359-892368 | Channel stop and start again: bit 11 of the state register stops the channel, the channel is kicked off the hardware (KICK_CHID = 2), then bit 10 enables it again; the trace does not say why (in Nouveau this pair surrounds a change of the engine context of a channel) | 0x800014, 0x002634, 0x070000 | gk104_chan_stop engine/fifo/gk104.c:44, gk104_chan_start engine/fifo/gk104.c:52 |
| 12 | 892369-900526 | Cleanup: 152 TLB flushes, 112 PFIFO_FLUSH, subfifo interrupt read/clear, PFIFO interrupt cleared | 0x070000, 0x100c80, 0x100cb8, 0x100cbc, 0x002100, 0x040108 | engine/fifo/gk104.c:652 |
| 13 | 900527-900552 | Channel removal: the channel is stopped and kicked (twice, with an enable in between), the runlist is committed again without it (1 entry left), and 0 is written to the channel register | 0x800010, 0x800014, 0x002270, 0x002274, 0x002284, 0x002634 | gk104_chan_stop engine/fifo/gk104.c:44, gk104_runl_commit engine/fifo/gk104.c:446, gk104_chan_unbind engine/fifo/gk104.c:60 |
| 14 | 900553-901167 | Final flushes and interrupt: interrupts disabled, runlist interrupt cleared, many TLB flushes, PMC.ENABLE polled | 0x000140, 0x000144, 0x000100, 0x002100, 0x002a00, 0x070000 | engine/fifo/gk104.c:652 |

## Verified values

| Line | Op | Register | Name | Value | Meaning |
|------|----|----------|------|-------|---------|
| 615163 | R | 0x800014 | PFIFO_CHAN.STATE | 0x0 | Channel state read before bind (idle) |
| 615165 | W | 0x800010 | PFIFO_CHAN.CHAN | 0x802cf302 | `0x80000000 OR inst->addr >> 12`: bit 31 and the address of the instance block divided by 4096 (address 0x2cf302000). The channel ID (2) is in the register offset, 0x800000 + 2 × 8 (engine/fifo/gk104.c:68) |
| 615167 | W | 0x800014 | PFIFO_CHAN.STATE | 0x11000400 | Bit 10 (0x400) set by gk104_chan_start (engine/fifo/gk104.c:52); the other bits were read from the register at line 615166 and are not known |
| 615174 | W | 0x002270 | PFIFO.PLAYLIST_WR | 0x2cf325 | `(target << 28) OR (addr >> 12)`: target 0, runlist at address 0x2cf325000 (engine/fifo/gk104.c:446) |
| 615175 | W | 0x002274 | PFIFO.PLAYLIST_WR_LEN | 0x2 | `(runl->id << 20) OR count`: runlist 0, 2 entries (engine/fifo/gk104.c:447) |
| 615186 | R | 0x002100 | PFIFO.INTR | 0x40000000 | Runlist scheduling interrupt pending (bit 30) |
| 615188 | W | 0x002a00 | PFIFO.INTR_RUNLIST | 0x1 | `BIT(runl->id)`: the interrupt of runlist 0 is acknowledged (engine/fifo/gk104.c:647) |
| 726186 | W | 0x409500 | PGRAPH.CTXCTL.WRCMD_DATA | 0x802cf302 | `0x80000000 OR addr`: the same instance-block value as at line 615165, given to FECS for the golden context (engine/gr/ctxgf100.c:1507) |
| 726187 | W | 0x409504 | PGRAPH.CTXCTL.WRCMD_CMD | 0x1 | FECS command 1 of gf100_grctx_generate (engine/gr/ctxgf100.c:1508); not the bind-pointer command 3 of engine/gr/gf100.c:839 |
| 892360 | W | 0x800014 | PFIFO_CHAN.STATE | 0x801 | Bit 11 (0x800) set by gk104_chan_stop (engine/fifo/gk104.c:44); bit 0 was read from the register at line 892359 |
| 900550 | W | 0x002274 | PFIFO.PLAYLIST_WR_LEN | 0x1 | `(runl->id << 20) OR count`: 1 entry left after the channel was removed (engine/fifo/gk104.c:447) |
| 900552 | W | 0x800010 | PFIFO_CHAN.CHAN | 0x0 | gk104_chan_unbind writes 0 (engine/fifo/gk104.c:60) |

## What the trace does not show

1. **User-space writes to USERD (BAR 1).** The trace shows BAR 1 has 9 reads and 1 write during the job, but these are kernel reads for polling. The pushbuffer, launch descriptor, and `LAUNCH` method are written by user space (Mesa) to GPU memory and BAR 1 USERD, not in the kernel trace.

2. **Instance memory content.** BAR 3 writes show the offset and value of each word, but the trace does not say what structure each offset corresponds to. For example, step 1 writes hundreds of words to instance memory for the channel client block and channel context, but the trace only records offset and value.

3. **What happens between BAR accesses.** Long gaps of instance memory writes (steps 7 and 10, each with 100,000+ writes) are mostly BAR 3 with few BAR 0 accesses. The BAR 0 accesses during these phases are periodic timer reads, temperature polling, and TLB flushes — the driver is waiting or doing background work.

4. **The compute shader execution itself.** The trace records driver setup and teardown, but not the GPU executing the shader. That work happens via the pushbuffer (written by Mesa) and the LAUNCH method call, which are user-space operations.

5. **The page-table walk.** When the driver writes to 0x100cb8 (TLB_FLUSH_VSPACE) and 0x100cbc (TLB_FLUSH_TRIGGER), the hardware walks the page tables, but the trace only shows the register accesses, not the page-table contents.

## Consequences for the Haiku driver

- **`docs/05-fifo-design.md`: the channel sequence is confirmed, with real values.** Bind (runlist ID in `0x800004 + 8 × id`, instance address in `0x800000 + 8 × id` as `0x80000000 | addr >> 12`), start (bit 10), runlist commit (`0x002270`, `0x002274`), and for removal stop (bit 11), kick (`0x002634`), commit, unbind (0). The lines of "Verified values" can be used as expected values of a host test.
- **`docs/05-fifo-design.md`: the stop is always followed by a kick.** In the trace every write of bit 11 is followed by a write of the channel ID to `0x002634` and a read of it until bit 20 is clear (lines 892361-892362, 900529-900534). The design document must have this step.
- **`docs/06-gr-design.md`: the first job of a channel makes the golden context.** The command to FECS in the trace is command 1 of `gf100_grctx_generate` (`engine/gr/ctxgf100.c:1508`), surrounded by the two long PGRAPH parts (steps 6 and 9, about 6,200 register accesses). A Haiku driver must do this once before any compute job; it is the largest part of the work between a channel and a launch.
- **`docs/04-mmu-design.md`: every change of instance memory or page tables is followed by a flush.** `0x070000` (write 1, read until bit 1 is clear) and the page-table invalidate (`0x100cb8`, `0x100cbc`, wait on `0x100c80`, `subdev/mmu/vmmgf100.c:188`) appear 106 and 140 times in the job.
- **`src/fifo/PushBuffer.h`, `src/compute/LaunchDesc.h`: not verified by this trace.** The pushbuffer and the launch descriptor are written by user space and are not in the trace. `firmware/compute_add1.md` has the descriptor that Mesa printed; a comparison of it with the output of `src/compute/LaunchDesc.cpp` is still to do.
- **`tools/compare_register_traces.py`: the trace can be used as a reference.** A Haiku driver run in a guest with the card can be traced the same way and compared with lines 615163-615176 (channel) and 726185-726188 (FECS command).

## Not known

Answered on 2026-10-13 (after the first version of this document):

- **The bits of `0x800014`.** The register database has them
  (`tools/rnndb.py 0x800014`): bit 0 ENABLED (a state), bit 10
  ENABLE_TRIGGER, bit 11 DISABLE_TRIGGER, bits 19:16 ENGINE, bits 26:24
  and 28 read-only status without a name. So `0x801` is "enabled, and
  disable requested", and `0x11000000` is read-only status.
- **Why the channel is stopped and started again (step 11).**
  `nvkm_chan_cctx_bind` (`engine/fifo/chan.c:41`) does this when an
  engine context is attached to or removed from a channel: block,
  preempt (the kick through `0x002634`), change the pointer, allow.
- **What step 5 waits for.** The registers `0x020520` to `0x020530` and
  `0x10a78c` are written by the power-management code
  (`subdev/pmu/gk110.c:39`, `subdev/pmu/gk104.c:69`): power gating of
  the graphics engine is switched off before the engine is used. The
  timer reads are the delays of that sequence. A driver that uses the
  graphics engine (milestone S3) probably needs this sequence.
- **Which function does what, in order.** `reference/linux-run-debug/`
  has a second run with the driver's own log next to the trace.

Still not known:

- **The read-only status bits of `0x800014`** (bits 26:24 and 28).
- **What the 142 registers without a name do** (`analysis/linux_run_trace.md`, last section). Most are in the PGRAPH parts.
- **The content of instance memory.** About 320,000 writes to BAR 3 in the job: page tables, the instance block, the graphics context image. The trace gives offset and value only.
