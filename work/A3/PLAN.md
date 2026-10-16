# A3 independent rework (2026-10-16)
Use the verified mediaflux ROM and fresh pinned decoder output.
Do not use the rejected branch or read the reviewer implementation.
Parse log instruction markers and preserve detail-line provenance.
Parse listing instruction lines, excluding data continuations.
Compare offsets; inspect mismatches in ROM and both pinned decoders.
Generate deterministic JSON/Markdown and check twice.
Test parser edge cases independently of the real capture.
Run full make check and retain exact input hashes and diagnostics.
Report observed execution separately from possible reachability.
