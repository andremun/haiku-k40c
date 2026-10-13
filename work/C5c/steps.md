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
