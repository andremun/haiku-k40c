# Combined S2 copy run

Status: pass. 

Command: `K40_MEM_STAGE=s2 python3 tools/memstage/run.py --run-approved-batch1-once`.
Package SHA-256: `18b6f8c0abf4bc2416c0fc947bdc68993df3c74d39d5c4057e9c203f7ecaf505`. See launch.json for commands,
hashes and kernel identity, a7/ for the fresh arm witness and unchanged A7
phase, memory-attestation.json and memory-observations.json for the BAR1 phase.
Raw serial, R5 before/after, trace and teardown are retained.

A pass is HARDWARE_VERIFIED under Haiku only for this finite card/context.
A pass is S2: after the S1 NOP, one 4096-byte copy between two owned VRAM pages on the same CE0-runlist channel, destination equal to source, no fault, clean teardown; no host DMA payload proof.
It is not host payload visibility or Q11 closure.
Approval is consumed. After any stop, follow decision 012, item 4, or decision 006.
