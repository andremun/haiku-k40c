# S3GR and S3CTX result (host)

Done by Claude Code on 2026-11-12 in the cloud container. No card run, no link.

Outputs: `tools/gr/tables.py` (Nouveau GR tables), `model.py` (host model of power
gating, engine start, microcode load, golden context), `oracle.py` (trace
comparison, in `make check`), `program.py` (recorded op program, generated data),
`src/gr/Runner.{h,cpp}` (interpreter), `tests/test_gr_runner`.

Result (HOST_ONLY, TRACE_VERIFIED for the access sequence):
- Power gating off: 144 trace accesses (two runs), 0 differences.
- Engine start to FECS ready: 2,166 accesses, 0 differences. Context image 322,048 bytes.
- Golden context: 4,095 accesses, 0 differences.
- Recorded program: 6,253 ops; the native runner reproduces 6,333 trace accesses.
- Kernel-mode compile of runner and data passes.

Not established: anything on the card. The model follows a run of Linux 6.8 on
this card; the Haiku state before the stage differs (no display, no interrupts,
units enabled by the S1 sequence). Rung 4 tests exactly this.

Open: review under REVIEW.md; the interrupt enable of Linux is left out on purpose.
Details: work/S3GR/FINDINGS.md.
