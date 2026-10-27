# S1D0OBSERVER plan

1. Verify/reconstruct exact strace 5.16-0ubuntu3 source and inspect its VFIO ioctl
   decoder and relevant output/lifecycle format. Record hashes outside reference/.
2. Produce a harmless owned-child fixture using only /dev/null. Record actual
   decoded failures; source-check success formatting separately. Never open VFIO.
3. Implement a bounded strict normalization boundary and FD-generation tracking.
   Reject incomplete/restarted/injected/ambiguous records, unsupported operations
   and unknown flags. Never infer syscall success from an entry/announcement.
4. Test decoder formats and model handoff, including unmap returned-size and stale
   descriptor identity. Keep all results host diagnostics, never provider authority.
5. Record exact remaining D0 launcher/probe prerequisites. Run make check, commit
   this task, and continue toward a concrete guarded stage under ADR 008.

Source finding: installed strace lacks VFIO argument decoding entirely. Build a
separate pinned userspace observer with an original narrow decoder include.
Do not retrofit a parser that invents the missing pointee data. The generic
strace behavior remains for other ioctls; success/result handling stays in strace.
