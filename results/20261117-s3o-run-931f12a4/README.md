# Combined S3 object-bind run, observed through BAR0

Status: failed. new filtered IOMMU/VFIO/PCIe fault indication; stop without retry

Command: `K40_MEM_STAGE=s3o python3 tools/memstage/run.py --run-approved-batch1-once`.
Package SHA-256: `f8d3e1df60189dbe503274672369b292b0169821be9ffc782901b2cac8d98f67`. See launch.json for commands,
hashes and kernel identity, a7/ for the fresh arm witness and unchanged A7
phase, memory-attestation.json and memory-observations.json for the BAR1 phase.
Raw serial, R5 before/after, trace and teardown are retained.

A pass is HARDWARE_VERIFIED under Haiku only for this finite card/context.
A pass is S3o: as S3e, and after GP_PUT the progress read through BAR0 status registers and the slow window only, each group printed at once; one BAR1 read of GP_GET as the last action; object bind consumed (GP_GET 0->1), no fault, clean teardown; no launch.
It is not host payload visibility or Q11 closure.
Approval is consumed. After any stop, follow decision 012, item 4, or decision 006.
