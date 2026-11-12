#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Generate the combined implementation-review handoff; --check writes nothing."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.memstage import build, rehearse

OUTPUT = ROOT / "docs/S1-BATCH1-IMPLEMENTATION-REVIEW.md"


def render():
    suite = build.validate_public()
    record = rehearse.validate(suite)
    host = json.loads((ROOT / "work/S1MEMPACKAGE/host-check.json").read_text())
    rows = []
    for phase, group in (
        ("A7", suite["A7"]["artifacts"]),
        ("memory", suite["artifacts"]),
    ):
        for role, info in sorted(group.items()):
            rows.append(f'| {phase}/{role} | {info["bytes"]} | `{info["sha256"]}` |')
    artifacts = "\n".join(rows)
    tests = "\n".join(
        "- " + value for name, value in sorted(host["compiled_exercises"].items())
    )
    loads = "\n".join(
        f"- {name}: {value}" for name, value in sorted(record["load_counts"].items())
    )
    return f"""# First-batch implementation review: A7 plus owned BAR1 memory

Prepared 2026-10-30 on main. Final review requested; no card launch authorized.
The six-task implementation follows Claude's accepted plan and amendments.
S1 remains incomplete. Q7 and Q11 remain open.

## Review boundary

Review S1MEMCONTRACT (`259dfb6`), S1MEMARENA (`d9b91b5`), S1MEMFAULTS
(`f86fe60`), S1MEMUPLOAD (`fd9ef5e`), S1MEMMMU (`07eea1c`) and the final
S1MEMPACKAGE commit reported at handoff. Its exact sources are bound in
`work/S1MEMPACKAGE/package.json`, SHA-256 `{build.sha(build.PUBLIC)}`.
Compiled plan SHA-256: `{suite['plan_sha256']}`.

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
The resident journal has 4096 records and the arena 32 records.

## Artifacts

| Phase/role | Bytes | SHA-256 |
|---|---:|---|
{artifacts}

Guest kernel: `{suite['kernel_sha256']}`.
ROM: `{suite['rom_sha256']}`.
The package includes the pinned verifier's zlib notice. Source/licensing records
identify consulted Nouveau, Haiku and QEMU material. QMP uses the pinned QEMU 6.2
upstream schema baseline; full running kernel source identity is unestablished.

## Checks and cardless evidence

Actual crypto/session verification: {host['signature_cases']} public-test-key cases.
{tests}

Native modules/clients link with no undefined symbols against the matching
kernel. Full repository checks pass as recorded in the task result.
Exact combined rehearsal: `{record['folder']}`. Its source/job/binary/kernel
binding is in `work/S1MEMPACKAGE/rehearsal.json`.
No VFIO device, private key read or grant is used. G0 and memory open return the
actual B_ENTRY_NOT_FOUND (`0x80006003`); A7 retains its existing B_ERROR
(`0xffffffff`). Install hashes/sizes and same-inode moves pass. No driver is
loaded from a partial/staging name. Real load counts:

{loads}

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
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    text = render()
    if args.check:
        if OUTPUT.read_text() != text:
            raise ValueError("review package differs")
    else:
        OUTPUT.write_text(text)


if __name__ == "__main__":
    main()
