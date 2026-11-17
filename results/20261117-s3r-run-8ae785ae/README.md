# Combined S3 object-bind run without the register list

Status: failed. MMU fault or PBDMA interrupt pending, or the engine not idle at the end

Command: `K40_MEM_STAGE=s3r python3 tools/memstage/run.py --run-approved-batch1-once`.
Package SHA-256: `1804d5651acc69e01b3f955e8df9616fff93c7b3680fb42427a664df11abf64e`. See launch.json for commands,
hashes and kernel identity, a7/ for the fresh arm witness and unchanged A7
phase, memory-attestation.json and memory-observations.json for the BAR1 phase.
Raw serial, R5 before/after, trace and teardown are retained.

A pass is HARDWARE_VERIFIED under Haiku only for this finite card/context.
A pass is S3r: as S3q, with list count 0 in the channel image (FECS runs no register list at the load); after the teardown one slow-window read of GP_GET as the last action; object bind consumed (GP_GET 0->1), no fault, clean teardown; no launch.
It is not host payload visibility or Q11 closure.
Approval is consumed. After any stop, follow decision 012, item 4, or decision 006.
