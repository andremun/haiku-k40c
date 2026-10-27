# S1D0THREAD result

Host-only correction. No guest or hardware run in this task.

- Add original bounded syscall-stop TGID/KCMP_FILES output to the private
  userspace observer. Compare kernel FD tables, not matching descriptor numbers.
- Require the owned QEMU TGID and a zero comparison before accepting another TID.
  Preserve raw records and log accepted proof metadata separately.
- Retain the normal mapping, permissions, container/generation and close rules.
- Capture exec, unshare and close_range before strace's early path filter.
  Only the initial exact owned-target exec is permitted. Reject later changes.
- Five task-proof tests pass. Real owned host fixtures distinguish shared-table
  pthreads, a private-table thread with the same TGID, and a separate process.
  All ioctls use /dev/null and return ENOTTY. No VFIO success is claimed.
- The guard integration test caught an ordering defect in the first host patch.
  Fix it and preserve both build/check records. No guest retry was consumed.
- Rebuild and pin the final observer, captures and fixed stage source/artifacts.
  All --check records agree. Full make check passes in check-final.log.

Review: docs/D0-TASK-PROOF.md, amended docs/D0-STAGE-REVIEW.md and REVIEW.md here.
The guest binaries, QEMU device options, isolation, fault watcher and watchdog
are unchanged. The first failed physical capture remains unchanged.

Next: S1D0RETRY. The user's 2026-10-28 “Go ahead” authorizes this correction and
one checked retry. A new stop requires another go-ahead. S1 remains incomplete.
