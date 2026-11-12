# S3GR: start the GR engine and its two microcode programs

## Why and inputs

First part of milestone S3. Design: docs/06-gr-design.md, docs/07-firmware-analysis.md.
Sources: `nvkm/engine/gr/gf100.c` (`gf100_gr_oneinit`, `gf100_gr_init`,
`gf100_gr_init_ctxctl_int`), `gk104.c`, `gk110.c`, `gk110b.c`, the `fuc/*gk110.fuc3.h`
arrays (firmware/manifest.yaml), `nvkm/subdev/pmu/gk110.c` (power gating),
`nvkm/falcon`. Reference: reference/linux-run/mmiotrace.txt.xz, load phase.

## Outputs

- Generated register tables and microcode arrays with source lines (tools, `--check`).
- A host model of the engine start that emits the ordered register accesses.
- A trace oracle: the emitted GR accesses compared with the Linux trace, differences listed and explained.
- Native code under the resident owner, Policy ranges for PGRAPH and the Falcons.
- work/S3GR/{PLAN,FINDINGS,RESULT}.md.

## Checks and limits

`make check`, the oracle with zero unexplained differences. No card run before rung 4.
