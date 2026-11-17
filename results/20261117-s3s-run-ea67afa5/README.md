# Combined S3 object-bind run with the register list without the LTC pair

Status: pass. 

Command: `K40_MEM_STAGE=s3s python3 tools/memstage/run.py --run-approved-batch1-once`.
Package SHA-256: `4dd6fef4235a876d40ffbe316fdc101aa6393ab875bf702b2f63e98b53b33b05`. See launch.json for commands,
hashes and kernel identity, a7/ for the fresh arm witness and unchanged A7
phase, memory-attestation.json and memory-observations.json for the BAR1 phase.
Raw serial, R5 before/after, trace and teardown are retained.

A pass is HARDWARE_VERIFIED under Haiku only for this finite card/context.
A pass is S3s: as S3r, with list count 34 (FECS runs every list entry except 0x17e91c and 0x17e920); after the teardown one slow-window read of GP_GET as the last action; object bind consumed (GP_GET 0->1), no fault, clean teardown; no launch.
It is not host payload visibility or Q11 closure.
Approval is consumed. After any stop, follow decision 012, item 4, or decision 006.
