# Combined S3 object-bind run, aligned with the Linux reference run

Status: failed. new filtered IOMMU/VFIO/PCIe fault indication; stop without retry

Command: `K40_MEM_STAGE=s3e python3 tools/memstage/run.py --run-approved-batch1-once`.
Package SHA-256: `160e2355f6758236fe84f99013f753af8a57903a732da4032dc954e97d9c3040`. See launch.json for commands,
hashes and kernel identity, a7/ for the fresh arm witness and unchanged A7
phase, memory-attestation.json and memory-observations.json for the BAR1 phase.
Raw serial, R5 before/after, trace and teardown are retained.

A pass is HARDWARE_VERIFIED under Haiku only for this finite card/context.
A pass is S3e: as S3c, with the channel's own copy of the golden image, PRIV PTEs for page pool, bundle and register list, and a user channel (RAMFC 0xe4 = 0); object bind consumed (GP_GET 0->1), no fault, clean teardown; no launch.
It is not host payload visibility or Q11 closure.
Approval is consumed. After any stop, follow decision 012, item 4, or decision 006.
