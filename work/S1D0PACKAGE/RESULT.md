# S1D0PACKAGE result

Scope: concrete D0 package, host tests and cardless fixtures. No physical run.

- Build the memory-only D0 client against the matching Haiku kernel. Sixteen
  native lifecycle host checks pass. GPU/PCI operations and publication are absent.
- Preserve the entire native backing in the permanent owner through reload.
  The prepared cardless owner readiness run passes in 52.38 s.
- Add bounded QMP topology parsing, fixed physical launcher, live kernel-log gate,
  strict role/kernel/identity checks and a retained-storage cutoff handshake.
- Bind viable group, container, exact device FD and complete successful mappings.
  Supervise actual QEMU with an independent watchdog and verified tracer pidfd.
- Reject observer death, unsupported histories, holes, late closes, partial output,
  transfer mismatches and new IOMMU/VFIO faults. Parse the complete final trace.
- Preserve first cardless topology fixture (0.31 s) and inert group decoder logs.
  Positive VFIO fixtures in tests are synthetic, not device evidence.
- Keep B5, vm-test.sh and the existing cardless launcher unchanged.
- Source/artifact records and --check commands agree. make check passes in
  work/S1D0PACKAGE/check-final.log. No root, push or physical launch occurred.

Review: docs/D0-STAGE-REVIEW.md, work/S1D0PACKAGE/REVIEW.md and
  docs/S1-PROGRESS-REVIEW-2026-10-27.md. Claude acceptance remains pending.

Next: S1D0RUN. R5 is missing. The user must start the read-only kernel journal
stream because the agent cannot use root. Hardware approval is already supplied.
S1 remains incomplete. Q7, payload visibility, native POST and FIFO consumption
remain unverified. Do not prepare S2/S3 as though S1 had passed.
