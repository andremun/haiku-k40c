#!/usr/bin/env python3
# Copyright 2026 Mario Andres Munoz.
# Distributed under the terms of the MIT License.
"""Generate the current A7 review entry from validated package evidence.

--check compares exact text without writes, a guest or hardware access.
No command in this document is executed by the generator.
"""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.a7 import build, logging_bench, rehearse

OUTPUT = ROOT / "docs/A7-REVIEW-PACKAGE.md"


def render():
    suite = build.validate()
    native = logging_bench.validate()
    rehearsal = rehearse.validate_evidence(suite)
    inventory = json.loads(build.INVENTORY.read_text())
    artifacts = "\n".join(
        f"| {name} | `{row['sha256']}` | {row['bytes']} |"
        for name, row in sorted(suite["guest_artifacts"].items())
    )
    timings = "\n".join(
        f"| {'Observed' if run['logging_observer'] else 'Plain'} | "
        + " | ".join(
            f"{run['medians_us'][name]:,.1f}"
            for name in ("live_us", "buffered_us", "drain_us")
        )
        + " |"
        for run in native["runs"]
    )
    folders = "\n".join(f"- `{run['folder']}/`" for run in native["runs"])
    return f"""# A7 buffered diagnostics package (2026-10-29)

**Current status: prepared for review. No physical run is approved.**
This fresh package is `build/a7/package-buffer/`. Previous package-i2c is consumed
and remains unchanged. S1 is incomplete. D1 is unapproved.

Review scope: buffered implementation `0b450b1`, closure refresh `210e5ee`, and
the package/evidence completion commit containing this document. See
[change details](A7-BUFFER-REVIEW.md) and
[timeout diagnosis](A7-STARTUP-DIAGNOSIS.md).

## Change and retained limits

POST instruction and I2C diagnostics enter a fixed resident buffer. Condition
counts/last values, requested/actual delays and MMIO timing add no register reads.
The controller returns and revokes the permit before draining. Script records
and timing summaries precede POST_RESULT. Deferred readback/re-arm/readiness
records retain logical order. Startup PASS/FAIL follows the drain.
Buffer/summary overflow and diagnostic clock reversal fail closed.

POST remains bounded by 10 seconds, the startup controller by 15 seconds and the
whole guest by 600 seconds. The owner remains single-shot and retains the arm-only
page on failure. No hardware permissions, register values, intended protocol
delays, sensor response policy, observer mapping proof or R5 rule were expanded.
Removing serial output can change incidental inter-operation gaps. This is an
intentional diagnostic change, not proof of hardware timing equivalence.

## Native cardless measurements

Each case replays the 528 saved run6 instruction records in a native logging-only
probe. Values below are medians in microseconds. Buffering and draining are
measured separately. These are logging mechanics in init_driver context, not
GPU POST timings or the authenticated write callback.

| Cardless mode | Live output us | Buffer insertion us | Deferred drain us |
|---|---:|---:|---:|
{timings}

{folders}

The existing observer and fixed cardless QEMU options were used. No VFIO device,
A7 owner, grant or card permit was supplied. The preliminary observed pre-launch
path failure is retained separately. The user approved resumed cardless validation.
The new measurements use the final buffer header. Host workload was not isolated.
Brief retained host/I2C checks overlapped the observed guest. Timing attribution for the
physical POST timeout remains UNKNOWN until a separately approved physical run.

## Exact package and installation rehearsal

Manifest SHA-256: `{build.sha(build.PUBLIC)}`.
Generated manifest: `work/S1A7BUFFER/package.json`.
Full possible-write list and omissions: `work/S1A7BUFFER/write-inventory.json`.
Native logging binding: `work/S1A7BUFFER/native-logging.json`.
Exact rehearsal binding: `work/S1A7BUFFER/rehearsal.json`.

| Guest artifact | SHA-256 | Bytes |
|---|---|---:|
{artifacts}

Observer SHA-256: `{suite['artifacts']['observer']['sha256']}`.
Guest kernel SHA-256: `{suite['kernel_sha256']}`.
ROM SHA-256: `{suite['rom_sha256']}`.

Exact guest job/binaries passed cardless rehearsal at `{rehearsal['folder']}/`.
The rehearsal binds the job, binaries, kernel and saved captures. It verifies
checked same-inode moves from an unwatched staging folder, final-name loads,
one open with raw B_ERROR, one preparation, no-card refusal before reservation,
and retained Failed owner state across client reload. No POST or DMA ran there.

## Writes and physical observations to review

The inventory has {len(inventory['script'])} possible script-write entries.
It is a possible-write list, not a replay or a claim about the executed path.
Driver writes retain the reviewed preinit, FIFO pair and readiness/scratch scope.
The two flush-address writes to 0x100c10 are explicit driver writes: before POST,
then after POST readback, using a fresh same-run structural witness and retained
zeroed DMA32 page. No payload-publication or DMA-visibility claim is made.

ADR 010 still limits tolerated address NACKs to the exact two sensor writes at
ROM 0xab8d, address 0x4c, registers 0x19/0x0d, value 0x73. At most four attempts
per pair. Only address NACK with clean bounded STOP can retry/continue. All
other errors remain fatal. Both I2C outcomes and cleanup results are retained.

Observe full trace counts against Linux's 560 active/38 skipped reference,
POST_RESULT, POST_WALL_US, POST_DELAY_US/COUNT, POST_MMIO_US/COUNT, POLL_* and
TRACE_END. Check 0x100c10 before/after, timer progress, VRAM 11520 MiB, scratch
result and pending 0x100. TRACE_DUMP_US is outside the controller budget.

## Commands and approval scope

Run only after review and the user's explicit yes for **one** run of this package:

```sh
export K40_VBIOS="$HOME/haiku-cross/vbios/k40c-0000_04_00_0-vbios-80.80.65.00.01.rom"
python3 tools/a7/build.py --check
python3 tools/a7/run.py --host-check
python3 tools/a7/run.py --run-approved-A7-once
```

Before launch, all artifact hashes and the current package must match. The R5
stream must be live. Only 0000:04:00.0 may be assigned, bound to vfio-pci, alone
in its IOMMU group, with writable VFIO group access and no other QEMU guest.
No root, binding change or manual reset is permitted. No extra QEMU options.

One launch consumes approval even if it fails. Preserve the consumed marker.
Any launcher-reported stop requires reporting and a new explicit yes before
another run. Native failure, panic, guest exit, deadline, broken witness or
observer, or disallowed R5 line stops the run. ADR 009's single exact startup
VFIO enabling line is the sole existing narrow allowance. No new allowance.
An already-POSTed refusal stops before arming/POST, but the existing two
interrupt-mask writes precede that decision (src/runtime/PreStart.cpp). It still
consumes the launch approval.

Record commands/hashes, serial, kernel-log delta and allowances, flush writes and
readback, readiness and bus mastering after exit. Any physical result applies to
this card under Haiku only. A7 success is not S1 success.
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = render()
    if args.check:
        if OUTPUT.read_text() != expected:
            raise ValueError("current A7 review document differs")
    else:
        OUTPUT.write_text(expected)


if __name__ == "__main__":
    main()
