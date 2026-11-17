# Combined S3 compute run with a writable launch descriptor

Status: pass. 

Command: `K40_MEM_STAGE=s3w python3 tools/memstage/run.py --run-approved-batch1-once`.
Package SHA-256: `0659d24164705bde75fe3244553a16607b6f4d64164b40530542f88379aa4f92`. See launch.json for commands,
hashes and kernel identity, a7/ for the fresh arm witness and unchanged A7
phase, memory-attestation.json and memory-observations.json for the BAR1 phase.
Raw serial, R5 before/after, trace and teardown are retained.

A pass is HARDWARE_VERIFIED under Haiku only for this finite card/context.
A pass is S3w: as S3v, with the launch descriptor (Qmd) mapped writable; one compute job, out[i] = in[i] + 1 for 1024 elements, every element checked by slow-window readback, no fault, clean teardown; no host DMA payload proof.
It is not host payload visibility or Q11 closure.
Approval is consumed. After any stop, follow decision 012, item 4, or decision 006.
