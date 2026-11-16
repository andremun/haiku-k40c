# Combined S3 golden-context run

Status: pass. 

Command: `K40_MEM_STAGE=s3a python3 tools/memstage/run.py --run-approved-batch1-once`.
Package SHA-256: `49ec4a094c158b58f108ee43f914c6e5951e7e8e61d76c1a5e8144b683b5d5d0`. See launch.json for commands,
hashes and kernel identity, a7/ for the fresh arm witness and unchanged A7
phase, memory-attestation.json and memory-observations.json for the BAR1 phase.
Raw serial, R5 before/after, trace and teardown are retained.

A pass is HARDWARE_VERIFIED under Haiku only for this finite card/context.
A pass is S3a: GR engine started, FECS and GPCCS running, golden context generated and attached to one channel of the GR runlist, no fault, clean teardown; no compute job.
It is not host payload visibility or Q11 closure.
Approval is consumed. After any stop, follow decision 012, item 4, or decision 006.
