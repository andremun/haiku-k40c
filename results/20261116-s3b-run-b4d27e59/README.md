# Combined S3 compute run

Status: failed. new filtered IOMMU/VFIO/PCIe fault indication; stop without retry

Command: `K40_MEM_STAGE=s3b python3 tools/memstage/run.py --run-approved-batch1-once`.
Package SHA-256: `909b3997ede4c289e1f0a893078345d06fea043486f5b8831c54f8c381c72931`. See launch.json for commands,
hashes and kernel identity, a7/ for the fresh arm witness and unchanged A7
phase, memory-attestation.json and memory-observations.json for the BAR1 phase.
Raw serial, R5 before/after, trace and teardown are retained.

A pass is HARDWARE_VERIFIED under Haiku only for this finite card/context.
A pass is S3: one compute job on the card, out[i] = in[i] + 1 for 1024 elements, every element checked by slow-window readback, no fault, clean teardown; no host DMA payload proof.
It is not host payload visibility or Q11 closure.
Approval is consumed. After any stop, follow decision 012, item 4, or decision 006.
