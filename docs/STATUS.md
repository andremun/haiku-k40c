# Status

Current phase: S1 preparation (plan: docs/S1-PLAN.md)
Current task: none. Wait. The next steps need the user's decisions (docs/S1-PLAN.md, "Scaffold review 2026-10-20").
Task state: WAITING. Host work and checks pass; ESC-001 resolved 2026-10-18 (native link and load pass on a KVM cardless guest). No card stage has run.
Last updated: 2026-10-20

Older results and notes: `docs/STATUS-archive.md` (do not read it for a task).

## Task log

| Task | Result | Date | Notes |
|---|---|---|---|
| A1 | DONE | 2026-10-05 | `hardware/record.json` + `record.md` for 2 GPUs; reworked... |
| A2 | DONE | 2026-10-06 | Added `pci_capabilities`, `interrupt`, `link_capability` to... |
| B1 | DONE | 2026-10-07 | Rework 2: fixed role format (6+ words), class (other-chip... |
| B2 | DONE | 2026-10-08 | Call graph from four roots with function tables: 446 nodes, 704... |
| B3 | DONE | 2026-10-08 | 872 MMIO accesses from 43 files (rd32: 288, wr32: 462, mask: 122).... |
| B6 | DONE | 2026-10-08 | Rework 2: added "gk110": true/false to every setup and launch... |
| B5 | DONE | 2026-10-11 | Rework 2: fixed 12 `make check` failures — subsystems... |
| C1 | DONE | 2026-10-11 | Register database: 462 distinct regs across 14 groups (bar, bus,... |
| C2 | DONE | 2026-10-11 | Firmware manifest: 4 built-in arrays (FECS data/code, GPCCS... |
| D1 | DONE | 2026-10-11 | Register I/O abstraction: `src/hw/RegisterIO.h` + `.cpp`... |
| B4 | DONE | 2026-10-11 | Linux dependency map: 139 symbols called from 70 files, each with... |
| C3a | DONE | 2026-10-11 | Subsystem models for mc, bar, imem, mmu, fb, top: 46... |
| C3b | DONE | 2026-10-11 | Subsystem models for timer (6 members), privring (3 members), ltc... |
| C3c | DONE | 2026-10-12 | Subsystem model for fifo: 48 members (15 main + 33 nested in six... |
| C3d | DONE | 2026-10-12 | Subsystem model for chan: 17 members (8 top-level + 9 nested in... |
| D3 | DONE | 2026-10-12 | GPFIFO push-buffer encoding: `src/fifo/PushBuffer.h` + `.cpp`... |
| D2 | DONE | 2026-10-12 | Page-table encoding and address-space model. Acceptance test 74... |
| D4 | DONE | 2026-10-12 | Register-trace comparison tool: mmiotrace conversion, comparison... |
| C3e | DONE | 2026-10-12 | GR engine subsystem model: 70 members across 5 parts... |
| C4a | DONE | 2026-10-12 | Source provenance: 24 constant lines in 4 files (mmu/fifo); 20... |
| D5 | DONE | 2026-10-12 | Launch descriptor (23 fields, constant buffers) and launch... |
| C4b | DONE | 2026-10-12 | Design documents `docs/04-mmu-design.md` to... |
| C5a | DONE | 2026-10-13 | Shader binary and launch descriptor. `tools/shader_extract.py`... |
| C5b | DONE | 2026-10-13 | Register trace summary: `tools/trace_summary.py` parses... |
| C5c | DONE | 2026-10-13 | `docs/08-compute-launch.md`: 14-step trace analysis, 12+ verified values, consequences and unknowns for Haiku driver. |
| D6 | DONE | 2026-10-13 | `tools/qmd_compare.py`: 155/155 fields match, 0 differences. First driver-vs-card check. |
| R1 | DONE | 2026-10-14 | Fixed 7 defects (F1–F7) from external review: overlap check, unmap page-size match, shift/bounds validation, launch descriptor overflow, push-buffer guards, trace parsing, qmd_compare rewrite. |
| A3 | STOPPED (superseded by the rework below) | 2026-10-15 | Stopped by the scaffold after 17 h, not accepted: the agent read `tools/check_repo.py`, and its explanation of offsets missing from the listing was wrong. Partial work kept on branch `task-a3` only. To rework. |
| V1 | HOST CHECKS PASS (V2) | 2026-10-16 | User-directed recheck of possible mistakes by "Local": 3 helper corrections, freestanding S1 controller (58 host checks), verification gates. Full make check: 220 failures with absent reference trees; pytest/PyYAML and recorded cross-toolchain unavailable. ROM deferred by user. See work/V1/RESULT.md. |
| V2 | DONE (offline scope) | 2026-10-16 | Restored all 5 exact clean source pins; full make check passes (0 failures). Removed pytest success suppression after a failing probe exited 0. Rebuilt pinned nvbios without sudo; fresh decode matches saved output byte for byte. A3 and native backend not implemented. See work/V2/RESULT.md. |
| A3 | DONE (independent rework) | 2026-10-16 | Observed/presentation inventory passes checks; split-line COPY and repeat bookkeeping explained. Raw-ROM supplement: 530 potential starts / 25 opcodes, all observed nonzero offsets covered. Prior rejected branch not used. |
| ABC1 | HOST WORK PASS / NATIVE BLOCKED | 2026-10-16 | A/B/C host implementation, raw-ROM/source/trace checks, typed memory boundary, source-backed bootstrap/controller, native backend object compilation. Three cardless boot timeouts; no matching-kernel link/load, no hardware/S1 claim. See docs/ABC-CARDLESS-OUTCOME.md and escalations/ESC-001.md. |

## V1 handoff (historical; input blockers resolved by V2)

Purpose: revise possible mistakes made by "Local" and approach the
machine-dependent implementation. `docs/S1-VERIFICATION.md` records the
remaining gates. All existing C++ checks and new targeted tests pass on the
host; this is neither native Haiku verification nor GPU evidence. The ROM was subsequently found in `~/mediaflux/vbios/` and verified against
the recorded size/hash; saved decoder output is present. The missing-ROM
blocker is resolved, but fresh decoding/A3 acceptance remains pending. Restore pinned
reference sources and the verification environment before full acceptance.
No hardware, VM, host service or push operations were performed in V1.

### ROM follow-up (2026-10-16)

User provided `~/mediaflux/vbios/`. Offline hash and size match the recorded
capture exactly. Updated the generated input inventory with the explicit ROM
path and documented the saved decoder output hash/warnings in
`reference/vbios/README.md`. No decoder rerun, source validation or card
access occurred. Source/toolchain/dependency blockers from V1 remain.

## V2 current handoff

The missing reference-source and verification-environment blockers are resolved.
Use `tools/restore_verification_refs.py --check` and the isolated PyYAML
environment documented in `work/V2/RESULT.md`. `make check` now passes, including
all positive-input trace/QMD tests. No pytest exit override remains. V1's code
now has repository-wide host-check evidence; its original failed attempt is
retained as history. No native Haiku or GPU result follows from these checks.

The ROM is verified and the independent pinned decoder was rebuilt and run.
Fresh full output equals the saved output, including warnings. A3 inventory
rework is now a feasible next bounded task, but has not started or been accepted.
The native cross-compiler/header/matching-kernel bundle remains absent here.
No GPU, VM, sudo, host driver/service or push operation occurred in V2.

## ABC1 current handoff

See `docs/ABC-CARDLESS-OUTCOME.md` for the actual A/B/C matrix, reproduction
commands and remaining gates; `work/ABC1/RESULT.md` and `evidence.json` retain
checks/hashes and unsuccessful attempts. This work revises possible mistakes
by "Local" and advances toward machine-dependent implementation. It is not
acceptance of the earlier rejected A3 branch or evidence of a working GPU.

The pinned cross compiler and headers are restored under `build/haiku-cross`.
Both native probe configurations and four freestanding core components compile.
B3 host failure tests pass, including cleanup failures. Native linking/loading
is blocked because three disposable TCG guests did not reach their test job;
all watchdogs cleaned up, KVM is absent, and further VM variants stopped under
ESC-001. The matching kernel is not substituted. Existing vm-test.sh is unchanged.

A3 inventory and raw-ROM structural coverage, source cross-reference and trace
interval join pass generated checks. The host interpreter refuses hardware and
default-denies board helpers. B2 actual GPU mapping/publication and C2/C3 full
FIFO/MMU/channel integration still require design/review and subsequent hardware
evidence. A5 decisions and unknown I2C device remain open; A7/B5/card C3 not run.
The v6.8 comparison supplement is incomplete due HTTP 429, not evidence that
selected sources differ. No push, physical GPU access, sudo or host-service
change occurred. Rebuild local committed-source review artifacts with
`python3 tools/review_bundle.py`; external firmware/caches are not bundled.
