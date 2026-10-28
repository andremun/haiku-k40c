# S1A7NATIVE: arm-only native integration and review package

ESC-002 is RESOLVED by the supplied Claude review recorded in
CLAUDE-ESC002-REVIEW.md. Its earlier audit remains in FINDINGS.md.

Implemented ArmedReference, independent of Buffer publication/pinning. Native
backing is owned, zeroed, aligned, DMA32 and quarantined for the guest boot.
The one-shot KEEP_LOADED A7 owner retains the platform, inputs and callbacks.
Physical execution requires its private permit; hostSimulation stays false.
PreStart arms before POST, records post-POST readback, then arms again.

The closed launcher obtains fresh same-run structural map/topology coverage and
signs a scoped grant using a single-use host package key. The native verifier
rejects altered, stale or repeated grants. No caller Boolean enables writes.
R5 stops on every new selected-class line. A watchdog bounds the owned guest;
no modified retry is permitted. QEMU exit and host bus-master-disable observation
are the proposed reviewed teardown boundary; no end-of-guest reset is assumed.

Host owner fixtures: 32 scenarios (16 complete), 192 altered grants, seven signed
scope errors, noncanonical signature and I2C/clock failures. Actual native
platform/client boundary tests: 4129/22 assertions with host OS mocks. Eight
launcher tests cover handshake and stop paths. Both native artifacts cross-link
against the matching kernel. Native loading/hardware behavior remain UNKNOWN.

Full make check passes, recorded in make-check-final.log. Initial provenance
failure and its correction are retained in make-check.log and FINDINGS.md.
The review package is docs/A7-REVIEW-PACKAGE.md. package.json records source and
artifact hashes; write-inventory.json lists all 544 possible script-write
locations and separate driver writes. These are possible writes, not a capture.

No A7 guest, GPU write, root command, push or new physical D0 run occurred.
IOVA=GPA stays INFERRED. Payload visibility/coherency remain UNKNOWN. D1 follows
POST and Q7 stays open. Review and explicit yes for ONE A7 run are still required
by amended ADR 008. S1 is incomplete; S2/S3 preparation remains conditional.
