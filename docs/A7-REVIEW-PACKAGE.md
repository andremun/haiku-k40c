# A7 buffered diagnostics package (2026-10-29)

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
| Plain | 900,671.0 | 20.0 | 1,684,176.0 |
| Observed | 8,169,705.0 | 25.5 | 14,996,946.0 |

- `results/20261029-174802-a7-logging-plain/`
- `results/20261029-175152-a7-logging-observed/`

The existing observer and fixed cardless QEMU options were used. No VFIO device,
A7 owner, grant or card permit was supplied. The preliminary observed pre-launch
path failure is retained separately. The user approved resumed cardless validation.
The new measurements use the final buffer header. Host workload was not isolated.
Brief retained host/I2C checks overlapped the observed guest. Timing attribution for the
physical POST timeout remains UNKNOWN until a separately approved physical run.

## Exact package and installation rehearsal

Manifest SHA-256: `a4b47b8a3e8f56d533170b0bccad3e3f037ed03e627b1d16e017248f0b244bdd`.
Generated manifest: `work/S1A7BUFFER/package.json`.
Full possible-write list and omissions: `work/S1A7BUFFER/write-inventory.json`.
Native logging binding: `work/S1A7BUFFER/native-logging.json`.
Exact rehearsal binding: `work/S1A7BUFFER/rehearsal.json`.

| Guest artifact | SHA-256 | Bytes |
|---|---|---:|
| client | `d11b0d3773e8f1a206a98b79b85a1c6e7c73948dbe096001d472ef0ee66ee122` | 7552 |
| helper | `58bec7c51730bf95f541c61c8ed9b8379b97f1c2b335702de0f9542698914977` | 3888 |
| identity | `8c45ec7bf2a2a16f3981431a3d0e5ee3588cfa9df63429ea51b01cc93fdf9d2f` | 8696 |
| owner | `944bdaf424789914a7b8a8b8fe3af272ea1f4d93d387e931d336aa084ce4c087` | 368672 |

Observer SHA-256: `75b7aeed34785c8ac729d68cbca83d256434acb036e336d0adf5a4bdc30bc7a2`.
Guest kernel SHA-256: `2da9a5b98719b40a61893836fb9c9e393e92e44f470e8af2024e76d50e2d2c62`.
ROM SHA-256: `aecb0b5fa466f64e2651a551a3cad57cccbdedd929e3996f542201af06ff1f54`.

Exact guest job/binaries passed cardless rehearsal at `results/20261029-175324-a7-rehearsal/`.
The rehearsal binds the job, binaries, kernel and saved captures. It verifies
checked same-inode moves from an unwatched staging folder, final-name loads,
one open with raw B_ERROR, one preparation, no-card refusal before reservation,
and retained Failed owner state across client reload. No POST or DMA ran there.

## Writes and physical observations to review

The inventory has 544 possible script-write entries.
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
