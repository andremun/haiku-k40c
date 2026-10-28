# S1A7RUN: STOPPED before arm grant

The user approved exactly one unchanged package run from commit 8974695.
build.py --check and run.py --host-check passed. The approved launch stopped
with "A7 guest job failed" after 107.88 s. The consumed marker remains intact.
No retry or D1 run occurred.

KNOWN / HARDWARE_VERIFIED under Haiku: B5 identity 0x0f1240a1 and PCI command
0x0007. No arm request or grant was captured. POST and readiness were NOT_REACHED.
0x100c10 before/after values are UNKNOWN. Do not classify this as a verified POST
failure: execution did not reach POST. Exact guest discovery/open error is UNKNOWN.

INFERRED no A7 writes: the unchanged source requires a valid host grant, and the
host issued none. The filtered R5 delta is empty. This is not a full-kernel-log
claim. Host PCI command after guest exit is 0x0002, with mastering disabled.
No QEMU remained. No manual reset, root command or push occurred.

Evidence: results/20261028-a7-post/ (generated summary plus identical raw copies).
Original: results/20261028-a7-fad36717/. S1 remains incomplete.
The next host-only task addresses the four review nits in a new package.
Any subsequent physical launch requires reporting this stop and new approval
under ADR 006 and ADR 008.

Full make check and record_run.py --check pass. Evidence is committed separately
from the requested post-run nits. No second launch is authorized.
