# S3LAUNCH result (host)

Done by Claude Code on 2026-11-12 in the cloud container. No card run, no link.

Outputs: `tools/gr/launch.py` (layout, push buffer, descriptor, constant buffer 7),
`src/gr/Compute.{h,cpp}` (stage), `src/gr/Guard.{h,cpp}` (write rules),
`memnative::Extension`, ledger capacity 32, `Upload::store` and `load`, native
owner stages 2 and 3, package stages `s3a` and `s3b`, validator branch,
`tests/test_gr_compute`, `docs/LADDER-RUN-SHEET.md`.

Result (HOST_ONLY):
- Descriptor equal to the reference run in 154 of 155 fields (the other is our
  constant buffer address).
- Stage test on a simulated card: trace-exact bring-up through Policy and Guard,
  independent decode of the launch, pass and four failure scenarios, four source
  mutations refused. Validator: two report kinds, 14 mutations refused.
- Kernel-mode compile of stage, guard and owner passes. `make check` passes.

Not established: the compute class sequence on the card (SOURCE_ONLY). No package,
link or rehearsal. Rung 6 (timed matrix product) is not prepared.

Open: T7610 build and rehearsal of `s3a` and `s3b`; diagnostic variants; a Linux
check of the same push buffer (rung 1); review under REVIEW.md.
Details: work/S3LAUNCH/PLAN.md and FINDINGS.md.
