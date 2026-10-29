# Approved batch-1 run: A7 and BAR1 pass

2026-10-30. One approved launch of package acb2aca. Result: PASS in
148.54 seconds. No retry. The consumed marker remains.
Capture: `results/20261030-batch1-a7-bar1-ec8db47d/`. Public package SHA-256:
`e184660225599a55f982d4c07219d49375938d5673af44aa0887757190619bf9`. Command:
`python3 tools/memstage/run.py --run-approved-batch1-once`.

## KNOWN / HARDWARE_VERIFIED scope under Haiku

A7 completed POST and readiness with its unchanged run7 code. The timer advanced,
VRAM size was 11520 MiB and scratch passed. The owned host
flush page was armed at `0x15d2000`. Post-POST 0x100c10 readback
was `0x0`; the original re-arm ran. Q11 remains open.

The distinct memory grant passed current A7/mapping/resource checks. Public-key
signature checks and observer replay pass offline. BAR0 requested explicit UC
for its 8 MiB view; BAR1 requested explicit UC/read-only for an 8 KiB prefix of
the discovered 256 MiB aperture. Accepted requests are recorded; effective
PAT/MTRR/cache type was not independently measured.

The source-derived arena retained seven owned objects, including both zeroed
debug allocations and its PGD/SPT/instance. Full physical patterns/complements
passed. The gk104 BAR1 context then verified these complete pages:

| Check | VA 0 | VA 0x1000 |
|---|---|---|
| Initial mapping | A at VRAM 0x81000 | B at VRAM 0x82000 |
| Remap and targeted invalidate | B | B |
| Restore and targeted invalidate | A | B |

Six per-page checksum records follow full word-by-word comparisons. There were
three PDB-specific invalidations and 17 sourced BAR flushes. BAR1 context writes
were `0x800000d3` (enable) and `0x000000d3` (owned enable cleared).
All per-phase selected guest fault snapshots passed, the IO policy reported no
rejection, and all allocations remained staged/referenced/retained through exit.
BAR2 was not used. This witnesses this BAR1 path and mapping update on this card.

## Host closure and limits

The selected R5 stream is byte-identical before/after (15998
bytes each). Delta: zero bytes; allowed kernel lines: none. This is selected-class
coverage, not proof of a clean full kernel log. Owned QEMU/tracer termination
passed. Host PCI command after exit was `0x0002`: bus mastering was off. No manual
reset, binding change or other-card access was performed.

S1 is still incomplete. No channel translation, PBDMA fetch, command submission,
compute job, generic host DMA publication or live reuse/retire contract is proven.
Q7 and Q11 remain open. S2/S3 success prerequisites are not met. Another write
stage/run requires a separately reviewed package and explicit user approval.

## Review inputs

`work/S1BATCH1RUN/report.json` binds the raw captures and deterministic offline
verification. Its `consumed.json` preserves a copy of the launch receipt; the live
marker is unchanged. `launch.json` records the exact command, source/artifact/kernel/ROM
hashes, fixed card and host prerequisites. The immutable `a7/` capture records
its fresh structural witness; `memory-attestation.json`, `pci-before/after.json`
and `memory-observations.json` bind the separate BAR1 phase. Raw serial, observer,
kernel before/after and teardown records are retained unchanged.
