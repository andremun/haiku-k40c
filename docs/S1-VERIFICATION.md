# Verification from the current driver to S1

2026-10-16, V1. Purpose: revise possible mistakes made by **"Local"** in
previous host work, and move closer to the **machine-dependent implementation**.
This pass is independent of the rejected A3 attempt. It does not validate that
attempt, the firmware interpreter, or any physical GPU path.

## What this pass establishes

KNOWN / HOST_ONLY: the new independent boundary tests fail seven assertions on
the starting implementation and pass after three corrections:

- Trace parsing rejected some negative inputs but accepted `-0` and
  `-ffffffffffffffff`; `stoull` wraps the latter to 1. Reject negative tokens
  before conversion. Offset and value cases are both covered.
- `encodeGpEntry` checked the starting address but not the end of its byte
  range. An eight-byte buffer at `2^40 - 4` crossed the existing address limit.
  Reject crossing ranges while retaining the valid exact-end case.
- `AddressSpace::pte` silently interpreted any shift other than 17 as 12.
  Apply the existing page-shift validation to this accessor too.

These are software contract corrections. They add no register addresses or
newly inferred hardware formats. The settled host NOP is also checked through
the existing encoder against the two words recorded in the S1 plan.

The new `src/runtime/S1Experiment.h` and `.cpp` provide an allocation-free,
exception-free experiment controller. A backend must implement bounded calls
for preparation, observations, publication, PUT commit, quiescence and release.
The controller requires an empty ring, publishes one entry before committing
PUT, observes a **new** GET equal to the new PUT, and checks faults before,
during and after the experiment. Both a host-clock budget and a poll-count
budget apply; a regressing clock fails. Initial equal pointers cannot pass.
A failed PUT may have reached hardware, so it still requires quiescence.

The controller releases storage only after the backend proves quiescence. If
that fails, it returns an explicit cleanup error and leaves storage owned by
the backend for recovery. Pointer progress alone is never success. A late fault,
failed final read or release failure also prevents success. The backend must
preserve raw fault snapshots/logs before acknowledgement; the controller itself
receives only their summarized status.

**Limits:** host tests inject backend behavior; they do not verify actual
publication barriers, DMA addresses, cache coherence, fault-register coverage,
preemption or teardown. The controller cannot interrupt a backend call that
blocks: each backend operation needs its own deadline and the eventual VM run
needs an independent host watchdog. This is partial C3 preparation, not a B2
memory manager, a Haiku kernel backend, or an implementation of C2's recipe.
The existing STL/exception-based host encoders are not thereby made kernel-safe.

## Gates that remain

Track labels below are S1-plan steps, not historical task IDs (some collide).

| Gate | Required check/output | Current evidence / next action |
|---|---|---|
| Reproducible source review | All five pinned reference trees resolve at their recorded revisions; review outputs regenerate | PASS in V2: all five exact pins restored, clean; full make check now passes. See work/V2/RESULT.md |
| ROM identity / A1–A2 | Explicit offline ROM path, recorded size/hash, independently reproducible decoder output | PASS in V2: exact ROM identity; freshly rebuilt pinned decoder reproduces saved full output byte for byte. Warnings and A3 coverage remain separate |
| Script inventory / A3 | Reachable bytecode, executed/skipped distinction, decoder/log/trace agreement, helper effects | ABC1 independent observed inventory passes checks; raw-ROM structural supplement covers all observed nonzero offsets. Full helper/runtime validation remains pending |
| Executor / A4–A6 | Source differences, pre-POST prerequisites, changing conditions, forced/skip states, wait/failure semantics; injected tests | ABC1 host core/source cross-reference implemented; production helper/preinit/permissions integration pending. No replay substituted |
| Board controls / A5 | Resolve targets and helper side effects; user decision on GPIO, thermal and unknown I2C operations | Existing BOARD-OPERATIONS document is a recorded analysis, not permission. Unknown device remains unresolved |
| Memory / B2 | Owned allocation, CPU/guest-physical/device-IOVA/GPU-VA separation, upload/readback, host flush page lifetime, publication | ABC1 typed ownership/publication layer tested, with cleanup quarantine. Real native/GPU allocation/mapping/publication adapter still pending |
| Native backend / B3 | 64-bit BAR handling, bounded mappings, host timer/logging, cleanup; build/link/load on cardless Haiku | Cross compiler/headers restored; native backend and core objects compile. Matching guest kernel/link/load still pending; host fault-injection tests do not replace it |
| Tooling / B4 | Cardless build identity, runtime access policy, incremental logs, host-enforced timeout | Existing scripts are reference inputs; no passthrough changes or physical card experiments made. Cardless toolchain must first be restored |
| Read-only identity / B5 | Approved hardware identity and stable/masked register survey against reference | HARDWARE PENDING; no inferred acceptance from emulated VGA |
| Load recipe / C1–C2 | Decode Linux load phase into named source-backed operations; specify domains, waits, faults and rollback per step | ABC1 source-anchored load survey and gated recipe prepared. Full operation-level attribution and unresolved integration choices remain partial |
| Bring-up / A7 | Explicit reset-state prerequisites, independent faults, owned scratch patterns/complements and alias checks | HARDWARE PENDING; the initialized marker is insufficient |
| Translation/scheduling / C3 | Physical slow-window bootstrap, flush/TLB path, page size, RAMFC, channel/runlist/PBDMA setup | HARDWARE PENDING; source and capture matching precede each first-write stage |
| Submission / C3 | One exact NOP, publication before PUT, measured GET advancement with faults checked | Controller contract HOST_ONLY; machine-dependent operations unimplemented |
| Teardown / C3 | Stop/preempt/remove, wait for quiescence, collect faults, then free; retain on failure | Controller/ownership/bootstrap policy HOST_ONLY; actual quiescence mechanism unverified |

The host flush page may be a **pre-POST** prerequisite: B2 is not completely
independent of A7. “No GR” remains an experiment hypothesis. The ROM is firmware;
the intended omission is GR context-switch microcode, not all firmware use.
A failed NOP is not by itself evidence that GR is required: memory, routing,
runlist and channel state must first be excluded.

For the future machine-dependent implementation, define one backend operation
per reviewed C2 step. Attach source provenance and masked trace expectations,
owned address objects, access permissions, an operation deadline and cleanup
behavior to each. Fail closed if its source/input/readiness gate is absent.
Keep physical-device access outside the host test backend.

## Reproduction and blockers

See `work/V1/RESULT.md` for the initial failed checks and `work/V2/RESULT.md`
for restored source inputs, corrected test harness and passing full checks.
`python3 tools/s1_verification_inputs.py` generates the offline input report;
`--check` compares it without writing, and `--require-ready` exits 2 for missing
external inputs. Supply `--rom` with the mounted image path from `reference/vbios/README.md`
for generation and `--check`; the committed inventory uses that explicit input. The report never reads devices or starts a VM. File presence and
revision checks do not establish kernel/header ABI compatibility or decoder
correctness. Review those separately after restoring the inputs.

No physical GPU, passthrough, reset, host sudo, host driver or running model
service was accessed. No push was attempted. S1 and the whole cardless plan
remain incomplete; this verification pass is not a driver completion claim.

## ABC1 update

See `docs/ABC-CARDLESS-OUTCOME.md` for the current per-track outcome, source
corrections, compile/test scope and native-run blockers. Earlier V1 missing
source/compiler findings are historical; the matching guest-kernel/native
acceptance and actual physical-device gates remain open.
