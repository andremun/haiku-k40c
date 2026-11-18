# Combined S3 object-bind run, registers only, with the report

Status: failed. native phase failure; stop without retry

Command: `K40_MEM_STAGE=s3q python3 tools/memstage/run.py --run-approved-batch1-once`.
Package SHA-256: `49cdf005092f1e787faeb1f58fed7f922dc2839efedbdf52e6a698a09b123215`. See launch.json for commands,
hashes and kernel identity, a7/ for the fresh arm witness and unchanged A7
phase, memory-attestation.json and memory-observations.json for the BAR1 phase.
Raw serial, R5 before/after, trace and teardown are retained.

A pass is HARDWARE_VERIFIED under Haiku only for this finite card/context.
A pass is S3q: as S3e, and after GP_PUT status registers only (no BAR1, no slow window), also after the teardown; GP_GET is not read; no fault, engine idle, clean teardown; no proof that the entry was fetched; no launch.
It is not host payload visibility or Q11 closure.
Approval is consumed. After any stop, follow decision 012, item 4, or decision 006.
