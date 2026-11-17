# Combined S3 object-bind run, observed through registers only

Status: failed. new filtered IOMMU/VFIO/PCIe fault indication; stop without retry

Command: `K40_MEM_STAGE=s3p python3 tools/memstage/run.py --run-approved-batch1-once`.
Package SHA-256: `0f7daf07fbe47d098399e3766415d2c81ac059c452c8624a3beef1f75c59d90f`. See launch.json for commands,
hashes and kernel identity, a7/ for the fresh arm witness and unchanged A7
phase, memory-attestation.json and memory-observations.json for the BAR1 phase.
Raw serial, R5 before/after, trace and teardown are retained.

A pass is HARDWARE_VERIFIED under Haiku only for this finite card/context.
A pass is S3p: as S3e, and after GP_PUT status registers only (no BAR1, no slow window) until the teardown ended, each group printed at once; then one slow-window read of GP_GET; object bind consumed (GP_GET 0->1), no fault, clean teardown; no launch.
It is not host payload visibility or Q11 closure.
Approval is consumed. After any stop, follow decision 012, item 4, or decision 006.
