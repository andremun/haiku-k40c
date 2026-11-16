# Combined S1 channel run

Status: pass. 

Command: `K40_MEM_STAGE=s1 python3 tools/memstage/run.py --run-approved-batch1-once`.
Package SHA-256: `487c689d81ebe004dfcf7297d9b4b908fe2990b8cd158cbcf73396e7fd2841bd`. See launch.json for commands,
hashes and kernel identity, a7/ for the fresh arm witness and unchanged A7
phase, memory-attestation.json and memory-observations.json for the BAR1 phase.
Raw serial, R5 before/after, trace and teardown are retained.

A pass is HARDWARE_VERIFIED under Haiku only for this finite card/context.
A pass is S1: one host NOP consumed on one CE0-runlist channel (GP_GET 0->1), no fault, clean teardown; no DMA payload proof.
It is not host payload visibility or Q11 closure.
Approval is consumed. After any stop, follow decision 012, item 4, or decision 006.
