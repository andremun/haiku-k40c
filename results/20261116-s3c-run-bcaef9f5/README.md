# Combined S3 object-bind run

Status: failed. new filtered IOMMU/VFIO/PCIe fault indication; stop without retry

Command: `K40_MEM_STAGE=s3c python3 tools/memstage/run.py --run-approved-batch1-once`.
Package SHA-256: `77bf0cd4598c85f6a6bc98e7d0d0382394414ae19f45f3d6a545076629c9f1ff`. See launch.json for commands,
hashes and kernel identity, a7/ for the fresh arm witness and unchanged A7
phase, memory-attestation.json and memory-observations.json for the BAR1 phase.
Raw serial, R5 before/after, trace and teardown are retained.

A pass is HARDWARE_VERIFIED under Haiku only for this finite card/context.
A pass is S3c: as S3a, then one GPFIFO entry of 2 push words (compute object bind) consumed (GP_GET 0->1), no fault, clean teardown; no launch.
It is not host payload visibility or Q11 closure.
Approval is consumed. After any stop, follow decision 012, item 4, or decision 006.
