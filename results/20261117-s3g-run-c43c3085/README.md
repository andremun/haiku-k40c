# Combined S3 golden-context run with the image printed

Status: failed. native phase failure; stop without retry

Command: `K40_MEM_STAGE=s3g python3 tools/memstage/run.py --run-approved-batch1-once`.
Package SHA-256: `b5867144ae6b586e7be9d350e40abba7ca3a7895da3f3c1fb86f0a36c80bb274`. See launch.json for commands,
hashes and kernel identity, a7/ for the fresh arm witness and unchanged A7
phase, memory-attestation.json and memory-observations.json for the BAR1 phase.
Raw serial, R5 before/after, trace and teardown are retained.

A pass is HARDWARE_VERIFIED under Haiku only for this finite card/context.
A pass is S3g: as S3a, and the golden image (0x4ea00 bytes) read by slow window and printed for the comparison with the Linux reference image; no submission, no fault, clean teardown; no compute job.
It is not host payload visibility or Q11 closure.
Approval is consumed. After any stop, follow decision 012, item 4, or decision 006.
