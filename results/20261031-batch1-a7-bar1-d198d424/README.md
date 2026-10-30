# Combined S1 channel run

Status: pass. 

Command: `python3 tools/memstage/run.py --run-approved-batch1-once`.
Package SHA-256: `1c7d71d55a314a90a9907fb6910771a729dc76ca9b620b121f55f8b26b17f0a4`. See launch.json for commands,
hashes and kernel identity, a7/ for the fresh arm witness and unchanged A7
phase, memory-attestation.json and memory-observations.json for the BAR1 phase.
Raw serial, R5 before/after, trace and teardown are retained.

A pass is HARDWARE_VERIFIED under Haiku only for this finite card/context.
A pass is S1: one host NOP consumed (GP_GET 0->1) on one CE0-runlist channel,
no fault, clean teardown. It is not host payload visibility or Q11 closure.
Approval is consumed. After any stop, report and request a new yes; no retry.

## Claude Code analysis (2026-10-31): S1 PASS

KNOWN / HARDWARE_VERIFIED for this K40c (0000:04:00.0) under Haiku:
- A7 POST and readiness passed; batch-1 memory and BAR1 gates passed.
- One channel (ID 1) on runlist 4 (CE0, from TOP), PBDMA 2, after every unit
  was enabled (0x200 = 0xffffffff, mc/nv04.c:120). GP_PUT = 1 through BAR1.
- GP_GET advanced 0 -> 1 after 3 polls, 10 us (CHANNEL_GET after=1/1).
- No MMU fault, no PBDMA or HCE status, FIFO status only bit 30 (runlist event).
- Teardown complete: stop, preempt, empty runlist, unbind, BAR1 disabled.
- No Policy rejection; all 24 steps in order. The host validator
  (evidence.memory_final, independent encoder) accepted the run:
  memory-observations.json, S1_complete true.
- R5 delta empty; host PCI command 0x0002 after exit; no QEMU left.

Scope: S1 as defined in docs/S1-PLAN.md - the card accepted and consumed one
host no-operation from a native Haiku driver, with no fault and a clean
teardown. Not a compute job, not DMA payload visibility (Q7 open), not Q11.
