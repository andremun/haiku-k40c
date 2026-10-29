# S1MEMCONTRACT result

DONE for source/evidence contract. No native execution/hardware run.
Claude's review changes are incorporated: BAR1/gk104/0x1704, explicit guest BAR1
mapping, no BAR2 or separate D1 gate; G1 flush readback observation only.
A7 phase freeze is generated from run7 launch-suite source hashes and checks
byte identity. No A7 source/binary/package was changed.

Contract: docs/S1-MEMORY-CONTRACT.md. Evidence: sources.json/a7-freeze.json.
Generator: tools/memstage/contract.py, no-write --check.
Strict UC request profile is SourceOnly, not measured host DMA coherency.
Selected INST/MMU debug allocations trace to VRAM; two zeroed retained objects
are reserved without importing GM200 register programming.
New resident memory authority/host broker is separate from the unchanged A7
module/client/installer. Same-launch signed completion binding is required.
No current A7 permit or latch can become a general memory capability.
BAR1 candidate uses owned PGD/SPT/instance/data, targeted invalidation and a
positive read/remap/restore test. General host-RAM visibility remains denied.

Runtime implementation follows in arena, faults, upload, MMU, package tasks.
Mandatory scoped fault coverage is implemented before the runnable package.
No intermediate card run; final Claude review and explicit user yes still required.
PASS: contract --check, A7 source freeze, full make check and diff check.
