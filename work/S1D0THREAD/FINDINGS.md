# Findings

- The user said “Go ahead” after the D0 stop report, authorizing this correction
  and one retry. No guest or hardware command has run in this host-only task.
- Read-only KCMP_FILES queries work under the current account. The pinned tracer
  now records caller TGID and table comparison at syscall stops. Only the owned
  QEMU TGID with a zero comparison permits normalization into its FD namespace.
- Four real owned host fixtures distinguish a normal pthread (same table), a
  fork (different TGID), and a thread with CLONE_THREAD but not CLONE_FILES
  (same TGID, unequal table). Every ioctl target is /dev/null and returns ENOTTY.
- A guard fixture exposed strace's early path-type filter. The first patch was
  too late to observe unshare. Moving the original guard before that filter
  fixes capture of both unshare and close_range. Current integration tests pass.
  No VM run or permission was consumed by these host fixtures.
- The parser permits only the initial target exec. Later exec, unshare and
  close_range close the gate. Existing ambiguity and mapping semantics remain.
- Current captured evidence is generation -02. Earlier inert captures remain
  unchanged. task_pins.py binds the final source, binary and generation -02 logs.
- The user restarted R5. D0 --check passes. The approved retry remains unrun.
