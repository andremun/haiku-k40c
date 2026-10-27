# S1D0PACKAGE findings

- No QEMU guest was running at initial preparation. Host kernel journal access was
  denied to the account; R5 requests a read-only human-started stream. No physical
  run may proceed without the required baseline/monitoring input.
- The D0 native client is memory-only. It checks all 4096 logical bytes, reports
  GPA/extent/token and deliberately consumes the owner latch as Failed to retain
  native backing through detach/reload. Publication is checked denied. It contains
  no PCI/BAR operations. Sixteen host lifecycle checks and native link pass.
- Three owned-child supervisor tests pass. strace -D keeps the actual target at
  Popen.pid; the independent pidfd watchdog targets that process. Tracer death
  invalidates evidence and stops the owned target. No unrelated process is attached.
- First prepared cardless owner reload run passes in 52.38 s. The enlarged owner
  loads; phase 2 retains token 2, Failed state and one quarantined record. Evidence:
  results/20261027-d0-owner-readiness/. No physical DMA or native POST claim.
- The physical D0 observer also needs successful group/container and device-FD
  association, plus device close lifetime. The decoder adds those bounded fields.
  Its path selection now captures every close so anonymous VFIO device-fd closure
  cannot disappear merely because the kernel's descriptor pathname varies.
- First cardless topology fixture passes in 0.31 s. Actual QMP output confirms
  that ramblock Offset is internal ram_addr_t, not HVA/GPA. The parser resolves
  system-RAM ranges from the global FlatView and rejects address holes.
- D0 now binds group viability, container attachment and the exact device FD.
  Close/detach retires coverage. Opaque operations or unproved thread histories
  fail closed. Synthetic success strings remain explicitly labeled in tests.
- The evidence cutoff drains records after QMP queries. Injected late close and
  partial-record tests prevent release. Final shutdown trace must parse completely.
- The package and its self-review are in docs/D0-STAGE-REVIEW.md and REVIEW.md here.
  The physical launcher has not run. R5 remains absent. No general hardware
  permission is missing, and no root command was attempted.
