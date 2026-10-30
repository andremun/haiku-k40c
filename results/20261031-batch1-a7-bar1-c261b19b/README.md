# Combined S1 channel run

Status: failed. native phase failure; stop without retry

Command: `python3 tools/memstage/run.py --run-approved-batch1-once`.
Package SHA-256: `4be2edd3a012c11c082738b1c29bb026a2a30bac3057bb339a0c52a9f326ae6e`. See launch.json for commands,
hashes and kernel identity, a7/ for the fresh arm witness and unchanged A7
phase, memory-attestation.json and memory-observations.json for the BAR1 phase.
Raw serial, R5 before/after, trace and teardown are retained.

A pass is HARDWARE_VERIFIED under Haiku only for this finite card/context.
A pass is S1: one host NOP consumed (GP_GET 0->1) on one CE0-runlist channel,
no fault, clean teardown. It is not host payload visibility or Q11 closure.
Approval is consumed. After any stop, report and request a new yes; no retry.

## Claude Code analysis (2026-10-31)

KNOWN (a7/serial.log): A7 and the batch-1 gates passed; BAR0 mapped whole
(16 MiB); no Policy rejection (IO_REJECT kind=0). All 24 channel steps ran
(step=23): bind, start, runlist 4 commit with pending clear, GP_PUT=1 through
BAR1, stop, preempt, empty runlist, unbind, BAR1 disable (closed=1).
Result: GP_GET stayed 0 while GP_PUT read back 1 (CHANNEL_GET after=0/1).
Channel state 0x11040001 (enabled, runlist 4). No MMU fault, no PBDMA or HCE
status; FIFO status only bit 30 (runlist event). R5 delta empty; bus
mastering off after exit. The progress wait ended at its 100000-poll cap after
145 ms, not the intended 2 s (software defect).

Likely cause (INFERRED): Linux enables every unit after POST,
`0x200 = 0xffffffff` (mc/nv04.c:120; trace line 47330, read back 0xfc37b1ef).
This driver keeps the script's 0xe011212d; units 0x1c2690c2 stay disabled,
probably including the copy engine. Not S1. No retry (ADR 006).
