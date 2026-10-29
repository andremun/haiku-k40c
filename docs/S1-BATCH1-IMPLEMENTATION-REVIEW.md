# First-batch implementation review: A7 plus owned BAR1 memory

Prepared 2026-10-30 on main. Final review requested; no card launch authorized.
The six-task implementation follows Claude's accepted plan and amendments.
S1 remains incomplete. Q7 and Q11 remain open.

## Review boundary

Review S1MEMCONTRACT (`259dfb6`), S1MEMARENA (`d9b91b5`), S1MEMFAULTS
(`f86fe60`), S1MEMUPLOAD (`fd9ef5e`), S1MEMMMU (`07eea1c`) and the final
S1MEMPACKAGE commit reported at handoff. Its exact sources are bound in
`work/S1MEMPACKAGE/package.json`, SHA-256 `e184660225599a55f982d4c07219d49375938d5673af44aa0887757190619bf9`.
Compiled plan SHA-256: `c1629df417906f28446b8b7e547c6b9ba5a73297f442489189cd4b2c8d99d5ca`.

A7's run7 implementation sources are unchanged. `contract.py --check` compares
them with the launched run7 suite. The new A7 owner embeds a fresh role key/nonce;
the A7 client is also byte-identical to run7. Its job and fixed helper are unchanged.
New code composes that job as a child; it does not borrow A7's inactive permit,
change its allowlist, or reserve the PCI device again.

## Ordered effects and gates

1. A separate read-only G0 driver records raw MC status. Loader reloads can repeat
   that read; all raw values must be zero. This is scoped status coverage, not a
   whole-chip baseline. Reset-time applicability is INFERRED from the selected
   source read semantics. No acknowledgement or interrupt enabling is added.
2. Run unchanged A7 once, with its own fresh owner page, key/nonce and current
   observer mapping witness. Both 0x100c10 writes remain unchanged. The post-POST
   readback is an observation only; there is no G2/D1 echo/publication experiment.
3. Only after checked current A7 completion can the host authorize memory. The
   distinct signed frame binds its compiled plan, nonce, owner challenge/epoch,
   guest BAR resources and the same launch's A7 transcript/witness. Read-only QMP
   query-pci must agree with the native BAR resource fields before the grant.
4. The memory module holds a reference to A7's resident API v2, which retains the
   sole reservation. New CPU views request strong explicit UC: BAR0 read/write
   for 8 MiB, BAR1 read-only for an 8 KiB prefix. The full discovered BAR1 aperture
   bounds the VMM. Requested UC is not independently measured PAT/MTRR evidence.
5. Validate uniform-FBP normal VRAM. Exclude the source 256 KiB head, 1 MiB tail
   and A7 scratch page. Retain two zeroed 128 KiB debug objects, a 64 KiB directory,
   256 KiB SPT, 4 KiB instance and two 4 KiB data pages. No captured allocation
   address is copied. The ledger has no free/reuse operation or DMA proof flags.
6. Write both data pages before verification; repeat complement and original
   patterns. Build the gk104 17/12 VRAM structures through the locked physical
   window. Data PTEs are read-only, kind 0, with no VOL/compression or large table.
7. Select mode 17, invalidate only the owned PDB with PAGE_ALL|HUB_ONLY, then
   enable BAR1 at 0x1704 with the sourced two-flush wait. BAR2/0x1714 is excluded.
   Observe A/B, remap VA0 to B and verify B/B, restore and verify A/B. Each page
   records a checksum after full comparison; hashes alone are not the pass test.
8. On success disable only the owned BAR1 context, record final faults and retain
   everything until guest/VFIO termination. On uncertainty stop writes and retain;
   do not clear faults, restore a foreign pointer or claim safe live reuse.

The memory controller's Reset-labelled snapshot is its own MC-only recheck after
A7; G0 before A7 is the separate preflight. Internal diagnostic phase 2 means
physical VRAM work, not the removed G2/D1 gate. R5 and the original mapping
witness remain supervised through completion. The guest deadline is 600 s;
memory work 30 s; bulk work 5 s; polls 2 s/100000, whichever limit occurs first.
The resident journal has 4096 records and the arena 16 records.

## Artifacts

| Phase/role | Bytes | SHA-256 |
|---|---:|---|
| A7/client | 7552 | `d11b0d3773e8f1a206a98b79b85a1c6e7c73948dbe096001d472ef0ee66ee122` |
| A7/helper | 3888 | `58bec7c51730bf95f541c61c8ed9b8379b97f1c2b335702de0f9542698914977` |
| A7/identity | 8696 | `8c45ec7bf2a2a16f3981431a3d0e5ee3588cfa9df63429ea51b01cc93fdf9d2f` |
| A7/owner | 368672 | `e87cc4b99627ccf52ddcac0000795e419870a41356f5ffc666f6b50ef39f97ac` |
| memory/memory_client | 7560 | `04848c9711e9b373b55e70d1e9b9b8c7d8995b42f69a53c0cffad57d9750172e` |
| memory/memory_helper | 3912 | `bfcd73611a07737593597e7622f93d335455b73a6560f23caad9c450cbe00d3f` |
| memory/memory_owner | 128416 | `6957df0bcb9b34bb6e4f5f70e14d8ff68c94a0f78daed23c8f0b9d350070688e` |
| memory/preflight | 6424 | `e5df732100e12bc34778beee436dd50101bf6140e065d8fc2ca38c1fcbc83ab5` |
| memory/preflight_helper | 3936 | `55ade2fbc1bc0a695a4c5e32a7c33ba18c21fd5c3c4aea54ae4fedc35dcc59d1` |

Guest kernel: `2da9a5b98719b40a61893836fb9c9e393e92e44f470e8af2024e76d50e2d2c62`.
ROM: `aecb0b5fa466f64e2651a551a3cad57cccbdedd929e3996f542201af06ff1f54`.
The package includes the pinned verifier's zlib notice. Source/licensing records
identify consulted Nouveau, Haiku and QEMU material. QMP uses the pinned QEMU 6.2
upstream schema baseline; full running kernel source identity is unestablished.

## Checks and cardless evidence

Actual crypto/session verification: 36 public-test-key cases.
- Memory actual client: 29 checks pass (host mocks only)
- memory experiment: 12 production-controller stop/replay cases pass; HOST_ONLY
- memory faults: 25 bounded baseline/routing/clock cases pass; HOST_ONLY
- memory MMU: 4096 independent encoding cases; 21 lifecycle/fault cases pass; HOST_ONLY
- memory policy: full controller path and independent denials pass; HOST_ONLY
- memory upload: 20 ordering/window/alias/failure cases pass; HOST_ONLY
- VRAM arena: 48 layout/oracle cases; stale/partial/capacity/retention checks pass; HOST_ONLY

Native modules/clients link with no undefined symbols against the matching
kernel. Full repository checks pass as recorded in the task result.
Exact combined rehearsal: `results/20261030-batch1-rehearsal-9feeeeb6`. Its source/job/binary/kernel
binding is in `work/S1MEMPACKAGE/rehearsal.json`.
No VFIO device, private key read or grant is used. G0 and memory open return the
actual B_ENTRY_NOT_FOUND (`0x80006003`); A7 retains its existing B_ERROR
(`0xffffffff`). Install hashes/sizes and same-inode moves pass. No driver is
loaded from a partial/staging name. Real load counts:

- A7_client: 2
- A7_owner: 1
- identity: 2
- memory_client: 2
- memory_owner: 1
- preflight: 2

Forced reload preserves one resident owner per phase and the Failed latch.
This is Haiku installation/lifetime evidence only. The rehearsal does not test
new physical UC mappings, VRAM, MMU, channel fetch or DMA payload visibility.

## Commands after acceptance and one explicit yes

First verify the unchanged package and live host requirements:

```sh
python3 tools/memstage/build.py --check
python3 tools/memstage/run.py --host-check
```

After Claude accepts this package and the user gives one explicit yes, launch
exactly once:

```sh
python3 tools/memstage/run.py --run-approved-batch1-once
```

This is a distinct combined stage, not the old A7 approval/marker. The new
`build/memstage/package/consumed.json` is written before the launch attempt and
must never be removed. No second launch follows any stop, including a parser
false alarm. Report and request a new decision under ADR 006.
R5 must be live in its established form; only 04:00.0 may be passed through,
bound to vfio-pci, alone in its group, with writable user access. No existing
QEMU guest may run. Never use root, change binding, reset manually or push.

## Requested review

Check new authority/continuation gates, CPU BAR mappings and value policy,
retention and failure ordering, all table encodings/flushes, the concrete BAR1
witness, exact rehearsal binding and host teardown. The complete effects and
source catalog are in `work/S1MEMPACKAGE/write-inventory.json` and the phase plan.
A future hardware pass would establish this finite BAR1 experiment on this card
under Haiku. It would not establish S1 success, Q7/Q11 closure or channel/PBDMA
operation. No physical first-batch run has been made in this preparation.
