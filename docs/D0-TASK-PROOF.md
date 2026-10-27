# D0 syscall task proof

The first D0 run stopped on a MAP_DMA issued by a different traced task.
The saved capture lacks FD-table proof. It remains a failed run. The new parser
cannot retroactively validate that capture.

The revised pinned observer reads the caller's TGID from proc status while the
caller is stopped by ptrace. It calls Linux KCMP_FILES to compare the caller's
FD table with that TGID's table. The original MIT helper emits the result inside
the syscall arguments. The host requires the TGID to equal the owned QEMU PID
and the comparison to return zero before accepting a different TID.
A matching FD number or thread-group membership alone is insufficient.

[Linux kcmp documentation](https://man7.org/linux/man-pages/man2/kcmp.2.html)
defines KCMP_FILES as a comparison of shared descriptor tables. This is a
read-only query governed by ptrace read-access checks. Failure closes the gate.
The helper uses installed UAPI constants, not guessed GPU registers or commands.

The caller is stopped at entry for mapping and close decoding. Group status
is decoded at the completion stop. The observer captures the actual return value
as before. A proof does not turn a failed or opaque mapping into a success.
The host preserves every raw record and separately logs accepted proof metadata.
It strips only the exact marker before passing the operation to BoundStream.
Mapping intervals, permissions, generations, lifetimes and error rules remain.

The path filter now always retains execve, execveat, unshare and close_range.
Only the initial successful exec of the fixed owned target is permitted.
Any later exec, unshare or close_range fails closed, including failed calls.
This prevents silent replacement or splitting of the owner's FD namespace.
Interrupted, resumed and otherwise ambiguous relevant histories remain rejected.
Unrelated closes retain their existing no-mapping-effect policy.

The helper is built into both the original VFIO decoder and strace's close
decoder. Upstream source remains outside the repository. build.py verifies the
exact original files and generated patch text. Nothing is linked into the driver.
The source/artifact suite and task proof captures have deterministic hash records.

## Validation and limits

Four owned host fixtures use only /dev/null. They exercise normal shared-table
threads, private-table threads, forks, and filter guard capture. All fixture
ioctls return ENOTTY. These are not successful VFIO calls or K40c evidence.
Synthetic successful mapping tests are labeled as such.

The fixed physical command and guest binaries are unchanged. The next approved
attempt writes a fresh `results/YYYYMMDD-d0-mapping-retry-01/` folder. It cannot
overwrite the stopped capture. The user authorized this correction and one retry
with “Go ahead” on 2026-10-28. ADR 006 applies again after any new launcher stop.

A D0 pass would establish structural mapping coverage at one cutoff only.
No provider, physical DMA job, POST or write-stage approval follows from it.
