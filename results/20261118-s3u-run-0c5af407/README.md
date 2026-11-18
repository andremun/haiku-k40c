# Combined S3 compute run, aligned, with the whole register list

Status: failed. native phase failure; stop without retry

Command: `K40_MEM_STAGE=s3u python3 tools/memstage/run.py --run-approved-batch1-once`.
Package SHA-256: `d33c24d1a95cb27942e0ee4d20f64caa26bbda5d82b8dd72fc1fa58ab5e0c386`. See launch.json for commands,
hashes and kernel identity, a7/ for the fresh arm witness and unchanged A7
phase, memory-attestation.json and memory-observations.json for the BAR1 phase.
Raw serial, R5 before/after, trace and teardown are retained.

A pass is HARDWARE_VERIFIED under Haiku only for this finite card/context.
A pass is S3u: as S3e with the whole register list (the LTC entries written after the golden stage), then one compute job, out[i] = in[i] + 1 for 1024 elements, every element checked by slow-window readback, no fault, clean teardown; no host DMA payload proof.
It is not host payload visibility or Q11 closure.
Approval is consumed. After any stop, follow decision 012, item 4, or decision 006.
