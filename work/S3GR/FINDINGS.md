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

## Golden context reproduced (2026-11-12, HOST_ONLY, TRACE_VERIFIED for the sequence)

`model.generate` follows `gf100_grctx_generate` and `gf100_grctx_generate_main`
with the hooks of `gk110b_grctx`. Trace lines 619424-730273, GR accesses and the
five other registers the functions touch: 4,095 accesses, 0 differences.

- During generation the per-context values (page pool, bundle buffer, attribute
  buffer, LTC patch) are direct register writes, because the channel has no mmio
  list yet (`ctxgf100.c:997-1000`, `gf100.c:440-456`). For each later channel the
  same pairs go into its mmio list (`gf100.c:469-479`).
- The addresses of the instance block, page pool, bundle buffer and attribute
  buffer are run data: the oracle takes them from the trace.
- `gf100_gr_icmd` runs a second time with an empty list and writes only its two
  bracket words (trace 728803-728804).
- KNOWN: the context unload at the end (0x409b04, 0x409000 = 0x100, poll of
  0x409b00) completed in the reference run.
- Two oracle findings on the way: the fifth GPC lies at 0x520000 and above (the
  first filter cut it); PPC masks read 5 and 2 (3 TPCs: two on PPC 0, one on PPC 1).

Still not modelled: instance-memory work of the stage (context memory mapping,
words 0x210 and 0x214, read of the golden image, per-channel context copy and
mmio list, engine context pointer), and the prelude before the engine start.

## Power gating, recorded program and native runner (2026-11-12, HOST_ONLY)

- `model.pgob` follows `gk110_pmu_pgob` (`pmu/gk110.c:32-82`). Both runs of the
  reference trace (616297-616416, 616434-616553) match: 144 accesses, 0 differences.
- `tools/gr/program.py` records the model as 6,253 ops in three stages (gating,
  start, golden) with 52 slots and a 36-entry per-channel patch list. Values that
  only the driver knows are slots: instance block, page pool, bundle buffer,
  attribute buffer and the two MMU fault pages. The recorded program reproduces
  6,333 trace accesses with 0 differences.
- The program expects the unit counts, Falcon capabilities and context size that
  the reference run read on this card (KNOWN). Another answer stops the stage
  before any engine write.
- `src/gr/Runner.cpp` runs the ops. `tests/test_gr_runner` replays the same
  6,333 trace accesses through it with 0 differences and tests expect, poll, idle,
  hook and slot failures. Runner and generated data compile for Haiku kernel mode
  (data object about 100 KB).
- The generated op tables are build output and are not stored in the repository.

Design choice: one verified description (the Python model), one mechanical
recording, one small interpreter. There is no second hand-written copy of the
6,000 accesses in C++.

Open for the native stage: Port adapter over NativeIo with the write policy
(the program itself is the allow-list: op index, address, value), instance-memory
work (context memory, words 0x210 and 0x214, golden image read, channel context
copy, patch list, engine context pointer), the GR runlist, and a larger ledger.
