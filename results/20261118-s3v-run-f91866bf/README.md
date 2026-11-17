# Combined S3 compute run, aligned, with the fault record

Status: failed. native phase failure; stop without retry

Command: `K40_MEM_STAGE=s3v python3 tools/memstage/run.py --run-approved-batch1-once`.
Package SHA-256: `7e5f57d8f9b7f33c91c2a2221f34246e796c378da86c972ecbc0d865033ecd80`. See launch.json for commands,
hashes and kernel identity, a7/ for the fresh arm witness and unchanged A7
phase, memory-attestation.json and memory-observations.json for the BAR1 phase.
Raw serial, R5 before/after, trace and teardown are retained.

A pass is HARDWARE_VERIFIED under Haiku only for this finite card/context.
A pass is S3v: as S3u, and before each result read the MMU fault status; a pending fault stops the poll after one sample with its fault record; one compute job, out[i] = in[i] + 1 for 1024 elements, every element checked by slow-window readback, no fault, clean teardown; no host DMA payload proof.
It is not host payload visibility or Q11 closure.
Approval is consumed. After any stop, follow decision 012, item 4, or decision 006.
