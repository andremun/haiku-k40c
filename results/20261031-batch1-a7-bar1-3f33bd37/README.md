# Combined S1 channel run

Status: failed. native phase failure; stop without retry

Command: `python3 tools/memstage/run.py --run-approved-batch1-once`.
Package SHA-256: `0ef5c3f4ba77cd4c9aee9f770f6958d53c41c936a263134c033f51aa77a4412d`. See launch.json for commands,
hashes and kernel identity, a7/ for the fresh arm witness and unchanged A7
phase, memory-attestation.json and memory-observations.json for the BAR1 phase.
Raw serial, R5 before/after, trace and teardown are retained.

A pass is HARDWARE_VERIFIED under Haiku only for this finite card/context.
A pass is S1: one host NOP consumed (GP_GET 0->1) on one CE0-runlist channel,
no fault, clean teardown. It is not host payload visibility or Q11 closure.
Approval is consumed. After any stop, report and request a new yes; no retry.

## Claude Code analysis (2026-10-31)

KNOWN (a7/serial.log): A7 POST_RESULT a=0x0 and readiness passed; the
batch-1 memory/BAR1 gates passed. The S1 channel phase found runlist 4,
PBDMA 2, mask 7, runm 0x10, matching Linux (trace 230517-230519). Policy
steps 0-10 ran: channel tables and invalidate, BAR1 USERD hand-over, PBDMA
discovery and mask, 0x2a04, PBDMA2 control, 0x2254.

Stop: `IO_REJECT kind=2 offset=800008`. NativeIo maps only the first 8 MiB
of BAR0; the channel registers start at 0x800000 (fifo/gk104.c:44-77). The
read of 0x800008 was refused, which revokes all further I/O by design, so the
BAR1 context could not be disabled (closure=1). No channel was bound, started
or committed to a runlist. R5 delta empty; host PCI command 0x0002 after exit.
The host simulator had no mapping limit, so it did not catch this.
Not S1 evidence. No retry (ADR 006).
