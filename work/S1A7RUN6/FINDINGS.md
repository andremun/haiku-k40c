# Findings

The user supplied Claude's ACCEPT review and direct authorization for one run
of package-i2c on 2026-10-29. The reviewed commit is 2818763. No source or binary
change precedes the launch. D1 is not approved. Any stop ends this approval.

Prelaunch build.py --check and run.py --host-check passed. The real host process
inventory showed no QEMU. VFIO group 23 is owned by mariom1. Exact owner/client/
helper/identity hashes match the four full hashes in the reviewed manifest.
The R5 prerequisite check passed with its live reader. Commands selected the
existing exact-hash private ROM through K40_VBIOS, with no package changes.

The single launch is results/20261029-a7-2aadfd99/. The launcher created
build/a7/package-i2c/consumed.json, binding package SHA-256
 e2a6920582db33493dfaf6d7f39b858c0b205f2baacc3f71b848e128d41ed0e5.
The launch command is python3 tools/a7/run.py --run-approved-A7-once.
No second launch is permitted by this approval.

The one run stopped after 144.8 s with native POST_RESULT 9 (Timeout) at 0x85d6.
There are 490 active and 38 skipped trace entries. The final write's completion
is not established. This is a POST software timeout, not a proven GPU hang.
Which deadline guard fired and why the budget elapsed remain UNKNOWN.

B5 identity/command passed twice. The flush target arm callback succeeded for
candidate 0x15df000, encoded 0x15df0. The 0x20 transaction completed on attempt 1
with primary/cleanup None and Value/ACK phase. No 0xab8d sensor attempt occurred.
Readback/re-arm and all independent readiness checks were NOT_REACHED.
The owner is Failed and retained the reference. No hardware S1 success exists.

R5 before/after are identical, 15998 bytes. Allowed kernel lines are empty.
Teardown confirms command 0x0002 and master disabled. Real host inventory shows
no QEMU. The launcher stopped before the shell uploaded job-output/job.exit.
Raw evidence is preserved. No retry, reset, source fix or new package is made.

Full make check passes in check-final.log. Build --check still confirms the
reviewed source/binaries; run prerequisites correctly remain consumed. The
exact QEMU and tracer PIDs were checked after exit and neither remains.
No source, binary, approval marker or original launcher capture was modified.
