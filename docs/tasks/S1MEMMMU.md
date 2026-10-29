# S1MEMMMU: native gk104 table/BAR1 bootstrap and scoped translation test

## Why and inputs

Depends on contract, arena, faults and upload tasks. Read STATUS, their outputs,
S1-INTEGRATION-CHOICES memory/BAR sections, PageTable.*, Bootstrap.* and selected
pinned GK110B/GK104 MMU/BAR callbacks. Preserve distinctions among physical VRAM,
BAR VA and channel GPU VA. The host AddressSpace model is not kernel-ready.

## Outputs

- Bounded freestanding table serialization and native BAR-context/bootstrap code.
- Source-backed targeted invalidation and per-context reference ledger.
- A concrete safe BAR-context mapping/update witness with exact claimed scope.
- Host oracle/fault tests, source report generator with --check and task work files.

## Work and invariants

Reuse pure encoders only after verifying masks/geometry. Do not link the host
STL/exception AddressSpace implementation into the kernel. Use bounded resident
workspace, explicit ownership and checked table sizes/indices/alignments.
Select one sourced page mode and small-page profile. Initialize absent entries
and preserve invalid large-entry semantics. Verify mode against hardware in the
future stage; a model setting does not program the device.

Build owned instances/tables through the physical bootstrap path. Fast mapping
must not be required to build itself. Use BAR1 only with the gk104 VMM format reusable by the future channel VMM.
Context register 0x1704 is selected by bar/gf100.c:52-58. Explicitly include the
bounded guest BAR1 MMIO mapping in the stage effects. Exclude BAR2 unless S1
is shown to require it and a separate change is reviewed. Discover aperture
bounds. Order bootstrap/enable/flush/waits from selected source. Serialize the
whole PDB-specific invalidation; completion is not global quiescence or data proof.

Design the live witness with distinct owned data pages and address-dependent
patterns. A source-supported remap/invalidate control must distinguish an updated
mapping from an old one. Do not probe unmapped memory. If no safe justified witness
is available, keep the phase non-runnable and report it before package approval.
BAR evidence is scoped to its context/extent/generation; do not promote channel
translation, PBDMA fetch or host-payload visibility from it.

## Checks and limits

Independent table-decode oracle; mutation/overflow/alias tests; wrong profile and
mode; slot exhaustion, invalidation timeout/clock fault; partial enable/cleanup.
Unknown references retain old/new tables and instances. No forced release/reset.
Native link only. Update licensing/provenance and --check reports. make check,
diff check, RESULT <=40 lines, one commit. No VM/card or new runtime permission.
