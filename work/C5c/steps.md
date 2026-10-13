# Step 1: Instance memory setup + MMU TLB flush
**Lines 573421-615162**
Registers: 0x070000, 0x100c80, 0x100cb8, 0x100cbc
What: The driver writes the channel's instance block and performs an MMU TLB invalidate, writing the page-table base to 0x100cb8, triggering a flush on 0x100cbc, and polling 0x100c80 for completion; it also flushes PFIFO and PFFB.
Source: subdev/mmu/vmmgf100.c:188

```
573453 39.426001 W 0:0x070000 0x1 PFIFO_FLUSH.FLUSH_CTRL
573456 39.426045 W 0:0x100cb8 0x2cf6360 PFFB.VM.TLB_FLUSH_VSPACE
573457 39.426053 W 0:0x100cbc 0x80000005 PFFB.VM.TLB_FLUSH_TRIGGER
```

# Step 2: Channel bind and enable
**Lines 615163-615167**
Registers: 0x800010, 0x800014
What: The driver reads PFIFO_CHAN.STATE (0x800014), clears it, writes the channel pointer (0x802cf302) to PFIFO_CHAN.CHAN (0x800010), waits for state 0x11000000, then sets state to 0x11000400.
Source: engine/fifo/gk104.c:72

```
615163 39.820113 R 0:0x800014 0x0 PFIFO_CHAN.STATE
615165 39.820135 W 0:0x800010 0x802cf302 PFIFO_CHAN.CHAN
615166 39.820144 R 0:0x800014 0x11000000 PFIFO_CHAN.STATE
```

# Step 3: Runlist write
**Lines 615168-615176**
Registers: 0x002270, 0x002274, 0x002284, 0x070000
What: The driver flushes PFIFO/PFFB, then writes the runlist address (0x2cf325) to PLAYLIST_WR (0x002270) and count (2) to PLAYLIST_WR_LEN (0x002274), reads back PLAYLIST_RD_LEN (0x002284).
Source: engine/fifo/gk104.c:430

```
615174 39.820279 W 0:0x002270 0x2cf325 PFIFO.PLAYLIST_WR
615175 39.820288 W 0:0x002274 0x2 PFIFO.PLAYLIST_WR_LEN
615176 39.820301 R 0:0x002284 0x2 PFIFO.PLAYLIST_RD_LEN
```

# Step 4: Runlist interrupt handling
**Lines 615177-615190**
Registers: 0x000140, 0x000144, 0x002100, 0x002140, 0x002a00, 0x088068
What: The driver disables interrupts, reads PMC.INTR (0x100) and PFIFO.INTR (0x40000000), clears the runlist interrupt bit (0x002a00=0x1), and re-enables interrupts.
Source: engine/fifo/gk104.c:652

```
615182 39.820404 R 0:0x000100 0x100 PMC.INTR_HOST
615186 39.820440 R 0:0x002100 0x40000000 PFIFO.INTR
615187 39.820448 R 0:0x002a00 0x1 PFIFO.INTR_RUNLIST
615188 39.820456 W 0:0x002a00 0x1 PFIFO.INTR_RUNLIST
```

# Step 5: Wait loop with timer and temperature polling
**Lines 615191-616553**
Registers: 0x070000, 0x100c80, 0x100cb8, 0x100cbc, 0x009400, 0x009410, 0x000200, 0x10a78c, 0x409604
What: The driver enters a wait loop, repeatedly reading PTIMER (0x009400/0x009410), polling PMC.ENABLE (0x000200), reading PDAEMON registers for temperature, and checking PGRAPH unit status, with periodic TLB flushes.
Source: not found

# Step 6: PGRAPH context setup (part 1)
**Lines 616554-618713**
Registers: 0x40912c, 0x409108, 0x400500, 0x40013c, 0x4091c4, 0x409184, 0x409188, 0x41a1c0, 0x41a1c4, 0x41a184
What: The driver configures PGRAPH context: reads CAPS registers, sets up FIFO control, writes CODE and DATA to ctxctl registers (0x409184, 0x4091c4) and GPC-broadcast variants (0x41a184, 0x41a1c4), writing virtual addresses to CODE_VIRT_ADDR.
Source: engine/gr/ctxgf100.c:1436

```
616554 39.958634 R 0:0x40912c 0x40300000 PGRAPH.CTXCTL.CAPS2
616555 39.958643 R 0:0x409108 0x10000000 PGRAPH.CTXCTL.CAPS
617101 40.006676 W 0:0x4091c4 0x00000000 PGRAPH.CTXCTL.DATA
617296 40.026018 W 0:0x409184 0x00000000 PGRAPH.CTXCTL.CODE
618105 40.088731 W 0:41a184 0x00000000 PGRAPH.GPC_BROADCAST.CTXCTL.CODE
```

# Step 7: Instance memory writes + periodic work
**Lines 618714-726184**
Registers: 0x070000, 0x100c80, 0x100cb8, 0x100cbc, 0x009400, 0x009410, 0x404170, 0x40802c, 0x000140, 0x022400, 0x0212a8, 0x020400
What: 107,314 writes to instance memory with periodic work: TLB flushes (every ~200ms), timer reads, temperature polling (PFUSE, PTHERM), and interrupt re-enable. 156 BAR 0 accesses, 107,314 BAR 3 accesses.
Source: not found (periodic scheduler work)

# Step 8: FECS context-switch command
**Lines 726185-726188**
Registers: 0x409500, 0x409504, 0x409800, 0x409840
What: The driver clears CC_SCRATCH (0x409840), writes the channel instance pointer (0x802cf302) to WRCMD_DATA (0x409500), sends command 0x1 to WRCMD_CMD (0x409504), and reads back CC_SCRATCH (0x409800) to confirm completion.
Source: engine/gr/gf100.c:833

```
726185 40.940310 W 0:0x409840 0x80000000 PGRAPH.CTXCTL.CC_SCRATCH_CLEAR
726186 40.940323 W 0:0x409500 0x802cf302 PGRAPH.CTXCTL.WRCMD_DATA
726187 40.940331 W 0:0x409504 0x1 PGRAPH.CTXCTL.WRCMD_CMD
726188 40.940340 R 0:0x409800 0x80000000 PGRAPH.CTXCTL.CC_SCRATCH
```

# Step 9: PGRAPH context setup (part 2)
**Lines 726189-730273**
Registers: 0x400200, 0x400204, 0x404004, 0x404010, 0x404020, 0x404028, 0x405800, 0x4064c0, 0x404488, 0x40448c, 0x400700, 0x40060c
What: The driver continues PGRAPH context setup: sends icmd commands (0x400200/0x400204), dispatches context switch (0x404010), sets SUBCH and MISC (0x404020/0x404028), writes mcache data (0x404488/0x40448c), and polls PGRAPH.STATUS (0x400700) and FE_STATUS (0x40060c) for readiness.
Source: engine/gr/ctxgf100.c:1436

```
726190 40.941235 W 0:0x400204 0x00000000 PGRAPH.ICMD_DATA
726192 40.941260 W 0:0x404004 0x00000000 PGRAPH.DISPATCH.CMD_ADDR
726200 40.941370 W 0:0x404020 0x00000002 PGRAPH.DISPATCH.SUBCH
726583 40.945880 R 0:0x400700 0x00000001 PGRAPH.STATUS
```

# Step 10: Instance memory + periodic work
**Lines 730274-892358**
Registers: 0x000140, 0x000144, 0x009100, 0x009400, 0x009410, 0x009420, 0x009140, 0x022400, 0x0212a8, 0x020400, 0x070000, 0x100c80, 0x100cb8, 0x100cbc
What: 161,834 writes to instance memory with periodic work: interrupt re-enable, timer/alarm polling every ~1s, temperature/fuse reading, TLB flushes every ~2s. 248 BAR 0 accesses.
Source: not found (periodic scheduler work)

# Step 11: Channel stop
**Lines 892359-892368**
Registers: 0x800014, 0x002634, 0x070000
What: The driver reads PFIFO_CHAN.STATE (0x800014=0x1), writes 0x801 to stop the channel, kicks channel ID 2 via PFIFO.KICK_CHID (0x002634), flushes PFIFO (0x070000), waits for state 0x0, then writes 0x400 to fully disable it.
Source: engine/fifo/gk104.c:40

```
892359 42.537150 R 0:0x800014 0x1 PFIFO_CHAN.STATE
892360 42.537159 W 0:0x800014 0x801 PFIFO_CHAN.STATE
892361 42.537193 W 0:0x002634 0x2 PFIFO.KICK_CHID
892368 42.537313 W 0:0x800014 0x400 PFIFO_CHAN.STATE
```
