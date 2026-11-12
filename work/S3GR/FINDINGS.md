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
