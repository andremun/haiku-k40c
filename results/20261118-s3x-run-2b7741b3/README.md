# Combined S3 run with a GR MMU fault and its recovery

Status: pass. 

Command: `K40_MEM_STAGE=s3x python3 tools/memstage/run.py --run-approved-batch1-once`.
Package SHA-256: `2a4f267936f4d7afe3d26ffb7c6440bf38710e2bc92c4159ff0a05943c1296ee`. See launch.json for commands,
hashes and kernel identity, a7/ for the fresh arm witness and unchanged A7
phase, memory-attestation.json and memory-observations.json for the BAR1 phase.
Raw serial, R5 before/after, trace and teardown are retained.

A pass is HARDWARE_VERIFIED under Haiku only for this finite card/context.
A pass is S3x: as S3v with the launch descriptor read-only on purpose: the GR MMU fault of s3v, its record, then the recovery program in the teardown (block, clear, stop, GR reset, empty runlist, allow, unbind); after it no fault pending and GR not busy, clean teardown; no compute result.
It is not host payload visibility or Q11 closure.
Approval is consumed. After any stop, follow decision 012, item 4, or decision 006.
