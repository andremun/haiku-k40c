# Combined S3 object-bind run with the whole register list

Status: pass. 

Command: `K40_MEM_STAGE=s3t python3 tools/memstage/run.py --run-approved-batch1-once`.
Package SHA-256: `f6e9e733ec17e06b483ef6cbc55f1bee9848bdbd280d64db6d7870aa2d30fad2`. See launch.json for commands,
hashes and kernel identity, a7/ for the fresh arm witness and unchanged A7
phase, memory-attestation.json and memory-observations.json for the BAR1 phase.
Raw serial, R5 before/after, trace and teardown are retained.

A pass is HARDWARE_VERIFIED under Haiku only for this finite card/context.
A pass is S3t: as S3r, with the whole register list (36 entries, the LTC entries written after the golden stage); after the teardown one slow-window read of GP_GET as the last action; object bind consumed (GP_GET 0->1), no fault, clean teardown; no launch.
It is not host payload visibility or Q11 closure.
Approval is consumed. After any stop, follow decision 012, item 4, or decision 006.
