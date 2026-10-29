# Combined first-batch run

Status: pass. 

Command: `python3 tools/memstage/run.py --run-approved-batch1-once`.
Package SHA-256: `e184660225599a55f982d4c07219d49375938d5673af44aa0887757190619bf9`. See launch.json for commands,
hashes and kernel identity, a7/ for the fresh arm witness and unchanged A7
phase, memory-attestation.json and memory-observations.json for the BAR1 phase.
Raw serial, R5 before/after, trace and teardown are retained.

A pass is HARDWARE_VERIFIED under Haiku only for this finite card/context.
It is not S1 success, host payload visibility, channel/PBDMA proof or Q11 closure.
Approval is consumed. After any stop, report and request a new yes; no retry.
