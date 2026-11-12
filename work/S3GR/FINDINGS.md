# S3GR findings

## The GR bring-up in the reference run (KNOWN, from reference/linux-run/mmiotrace.txt.xz)

Measured on 2026-11-12 with BAR0 at 0xc1000000 (trace line 10). GR range
0x400000-0x51ffff.

| Block | Trace lines | BAR0 GR accesses | Content |
|---|---|---:|---|
| Early | 46085-46092 | 8 | Reads at device set-up |
| Engine start | 616417-619444 | 2,103 | `gf100_gr_init`, microcode load, FECS and GPCCS start |
| Golden context | 726185-730273 | 4,044 | FECS command 1, `gf100_grctx_generate` |

- Nouveau starts the GR engine at the first use by a channel, in the job phase,
  not at driver load. The load phase has no GR init.
- 0x000260 is written 0 then 1 twice: around the microcode load (617099, 618559)
  and around the context generation (726189, 730259).
- FECS reset: 0x409614 = 0x70, then 0x770 (619426-619441), after the load.
- FECS ready: 0x409800 reads 0 three times, then 0x80000000 (618698-618710).
- Power gating off before the engine start: 0x10a78c and 0x020520
  (616302-616315, again at 616447), `subdev/pmu/gk110.c`, `gk104.c`.
- Between the two blocks are about 107,000 instance-memory writes (BAR3), and
  about 162,000 after the golden context (docs/08-compute-launch.md steps 7, 10).

Consequence: the oracle compares about 6,150 BAR0 accesses. This is small enough
to require zero unexplained differences.

## UNKNOWN

- Content and size of the instance-memory blocks of steps 7 and 10 (context image
  and its copies). S3CTX decodes them.
- Whether kernel 6.8 (trace) and 6.12 (source pin) differ in the GR path. The
  oracle answers this.

## First oracle result (2026-11-12, KNOWN, TRACE_VERIFIED for the table data)

`tools/gr/tables.py` reads 232 register tables and 68 packs from
`nvkm/engine/gr/*.c`. The expansion of `gk110b_gr_pack_mmio` gives 153 writes.
They equal trace lines 616569-616721 in address, value and order: 0 differences.
The kernel of the trace (6.8) and the source pin (6.12) agree for this pack.

The trace around it follows `gf100_gr_init` (`gf100.c:2342-2463`) line by line:

| Trace lines | Source | Content |
|---|---|---|
| 616297-616416 | `gf100_gr_oneinit` area, `subdev/pmu/gk110.c`, `mc` | Unit reset through 0x000200, power gating off (0x10a78c, 0x0206b4, 0x020520-0x020530), twice |
| 616417-616433 | `gf100_gr_oneinit`, `gf100_gr_rops` | 0x409604 = 0x60005; per GPC 0x2608, 0x0c30, 0x0c34 |
| 616554-616557 | `gf100_gr_init_ctxctl` set-up | Falcon capability reads 0x40912c, 0x409108, 0x41a12c, 0x41a108 |
| 616558-616568 | `gf100.c:2347-2349`, `gf100_gr_init_gpc_mmu` | 0x400500, 0x418880-0x4188b8 |
| 616569-616721 | `gf100_gr_mmio` | The 153 table writes |
| 616722-616725 | `gf100_gr_wait_idle` | 0x400700, 0x000200, 0x002640, 0x40060c |
| 616726-616753 | init hooks | vsc stream master, zcull, active LTCs, ROP active FBPs |
| 616754 onward | `gf100.c:2385` onward | Enables, exceptions per GPC and TPC, then the microcode load |

Card topology read from the trace (KNOWN for 0000:04:00.0): 0x409604 = 0x60005
(5 GPCs, 6 ROPs by `gf100_gr_oneinit`), 3 TPCs in each GPC (0x2608 = 0x40003),
15 TPCs in total (0x500910 = 0x4000f).

## Engine start reproduced (2026-11-12, HOST_ONLY, TRACE_VERIFIED for the sequence)

`tools/gr/model.py` is a host model of `gf100_gr_oneinit` (unit counts, tile map),
`gf100_gr_init` with the hooks of `gk110b_gr`, the ZBC set-up with its LTC part,
the load of the four microcode arrays and `gf100_gr_init_ctxctl_int`.
`tools/gr/oracle.py` runs it against the trace: every model access must be the
next trace access (timer reads of kernel wait loops excluded).

Result: trace lines 616417-616433 and 616554-618711, 2,166 accesses, 0 differences.

- KNOWN: FECS reports ready (0x409800 bit 31) after four polls in the reference run.
- KNOWN: context image size 0x409804 = 0x4ea00 (322,048 bytes).
- KNOWN: the microcode arrays of the 6.12 pin are the ones the 6.8 kernel loaded
  (every data and code word is compared).
- The two MMU fault page addresses (0x4188b4, 0x4188b8) are run data. The oracle
  takes them from the trace. The native driver must supply its own pages
  (`gf100.c:2277-2278`, `fb->mmu_wr`, `fb->mmu_rd`): to source in S3GR native work.
- Not in the model, by decision: the interrupt enable that follows (0x000640,
  trace 618712-618713). The driver polls and enables no interrupt.
- Not yet in the model: the reset and power-gating sequence before the start
  (trace 616297-616416, 616434-616553). Next step.
- One error found by the oracle on the way: the TPC count register 0x2608 reads
  0x40003; the kernel keeps the low byte (`gf100.h:107`, u8).
