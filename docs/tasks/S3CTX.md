# S3CTX: golden context, GR context of one channel, channel on the GR runlist

## Why and inputs

Second part of S3. Sources: `nvkm/engine/gr/ctxgf100.c` (`gf100_grctx_generate`,
`gf100_grctx_generate_main`), `ctxgk104.c`, `ctxgk110.c`, `ctxgk110b.c`,
`gf100.c` (`gf100_gr_chan_new`, `gf100_gr_chan_bind`), `nvkm/engine/fifo/gk104.c`
(engine context pointer), `chan.c` (`nvkm_chan_cctx_bind`). Reference trace: job phase,
steps 6 to 11 of docs/08-compute-launch.md.

## Outputs

- Host model of context generation (mmio list, icmd, mthd, bundle, page pool, attribute buffers).
- The FECS commands (context size, golden save, bind) with waits and error tests.
- Channel on the GR runlist with its engine context pointer; stop, preempt, start around the change.
- Trace oracle for the job phase; work/S3CTX/{PLAN,FINDINGS,RESULT}.md.

## Checks and limits

As S3GR. Rung 4 ends after the golden context and a clean teardown.
