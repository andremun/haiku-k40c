# S1D0THREAD: prove syscall task and shared FD table

Read docs/STATUS.md, work/S1D0RUN/RESULT.md, tools/observer/{binding.py,
normalize.py,build.py,vfio_decode.inc,supervise.py}, and the D0 stage package.
The user authorized correcting the observer and one D0 retry on 2026-10-28.
This task prepares the host-only correction. The next task performs that retry.

Record the plan first. Add original bounded observer output that establishes the
caller's kernel TGID and KCMP_FILES equality with that TGID at each relevant
syscall. The parser requires the owned QEMU PID and a shared table before treating
a different TID as the same FD namespace. Same FD numbers or /proc membership
alone are not proof. Reject proof failures. Preserve the old stopped capture.

Capture and reject exec after initial target exec, unshare and close_range so
an owner cannot replace/split its FD table unnoticed. Keep ambiguous concurrent
records fail-closed. Preserve fixed GPU options, safety checks and deadlines.
Test owned host threads, a distinct process, proof failures and namespace changes.
No guest or hardware run in this task. Rebuild and pin the observer and stage.
Record consulted sources/licenses, amend the stage review, run make check,
write RESULT.md (max 40 lines), and commit this task separately on main.
