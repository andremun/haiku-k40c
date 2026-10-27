# Self-review of the task-proof correction

No Important finding remains in the prepared host-only correction.
This is a Codex self-review. It does not claim a new Claude acceptance.

- Normalize a TID only from the pinned tracer's syscall-stop proof, with the
  owned process TGID and KCMP_FILES result zero. Do not trust equal FD numbers.
- Capture namespace-splitting/replacement operations before strace's early path
  filter. Reject every such operation except the initial exact target exec.
- Preserve raw trace and retain normal BoundStream mapping/close/error checks.
- Test real shared/private FD tables and a fork with matching FD numbers.
  Keep synthetic successful maps separate from ENOTTY captures.
- Keep guest artifacts and GPU effects unchanged. No GPU write or DMA job is
  enabled. Use the existing isolation, fault checks, lock and actual-child timer.
- Bind the updated source and observer hashes before the one authorized retry.
