# Phases and tasks

This file is the index. The text of a task is in `docs/tasks/<ID>.md`:
read only the file of your task. Do not read the files of other tasks.

Order follows `docs/design/design.md` section 50 and the specification
section 10. Phases A-D run on Ubuntu without touching the GPUs. Each task
is one session. A task is done only when its outputs exist, its checks
pass (`make check`) and `docs/STATUS.md` is updated.

## Success milestones (set 2026-10-07)

The design documents name one goal: a verified compute job. That goal is
far away and has parts that the first plan did not list (S3 below). The
project now has three success milestones. Each one is a result on its
own, and the work may stop at any of them.

| ID | Milestone | Needs | Proof |
|---|---|---|---|
| S1 | The GPU accepts a command. A channel exists, a GPFIFO entry is submitted, and the GPU consumes it. | PCI, MMIO, MC, FB/VRAM, instance memory, MMU, FIFO/PBDMA, runlist and VBIOS bring-up. Omission of GR setup/microcode remains unverified. | The GPFIFO GET pointer of the channel advances to PUT, read from the host, with no relevant fault pending and clean teardown. |
| S2 | The GPU copies a buffer. The copy engine (class `KEPLER_DMA_COPY_A`) copies N bytes between two buffers in VRAM. | S1 and the copy engine (`nvkm/engine/ce/gk104.c`). INFERRED: no firmware and no GR context are needed (the file has no falcon or firmware code). Task C3 must confirm it. | The host reads the destination buffer and it equals the source. |
| S3 | The GPU computes. A compute shader does `output[i] = input[i] + 1`. | S1, the GR engine with FECS/GPCCS firmware and a GR context, the compute class `0xa1c0`, a launch descriptor, and a shader binary in GK110 machine code. The last two are user-space work that Nouveau's kernel driver does not contain: they are in Mesa (`reference/mesa`). Tasks B6, C5 and D5 cover them. | The host reads the output buffer and checks every element. |

S1 is the first success criterion of the project. S2 is the first real
work done by the GPU. S3 is the goal of the design documents.

Before S3 work starts on Haiku, the same job must run on this card under
Linux with Nouveau and Mesa (task C5, in a Linux guest with the card
passed through: `docs/PASSTHROUGH.md`). If it does not run there, there
is no reference for S3 and the project stops at S2.

## Current S1 memory/translation batch (proposed)

A7 now passes under Haiku; see STATUS. The proposed first-batch design and A7
result are reviewed together in [S1-BATCH1-REVIEW.md](S1-BATCH1-REVIEW.md).
This index grants no implementation/run acceptance or hardware permission.

| Task | Purpose | Text |
|---|---|---|
| S1BATCH1PLAN | Prepare combined A7/first-batch design review | [Task](tasks/S1BATCH1PLAN.md) |
| S1MEMCONTRACT | Evidence and operation contract | [Task](tasks/S1MEMCONTRACT.md) |
| S1MEMARENA | Owned VRAM and address ledger | [Task](tasks/S1MEMARENA.md) |
| S1MEMFAULTS | Scoped baselines and diagnostics | [Task](tasks/S1MEMFAULTS.md) |
| S1MEMUPLOAD | Physical VRAM upload/readback | [Task](tasks/S1MEMUPLOAD.md) |
| S1MEMMMU | BAR/MMU bootstrap and scoped witness | [Task](tasks/S1MEMMMU.md) |
| S1MEMPACKAGE | One reviewed experiment package | [Task](tasks/S1MEMPACKAGE.md) |

## Phase A: Ubuntu reference data

| Task | Title | Text |
|---|---|---|
| A1 | Hardware record | `docs/tasks/A1.md` |
| A2 | Root captures | `docs/tasks/A2.md` |

## Phase B: Nouveau dependency extraction

| Task | Title | Text |
|---|---|---|
| B1 | Chipset path and file inventory | `docs/tasks/B1.md` |
| B2 | Call graph | `docs/tasks/B2.md` |
| B3 | MMIO access extraction | `docs/tasks/B3.md` |
| B4 | Linux dependency map | `docs/tasks/B4.md` |
| B5 | Minimum chain to one computation | `docs/tasks/B5.md` |
| B6 | Compute launch path (user-space half) | `docs/tasks/B6.md` |

## Phase C: hardware database and firmware

| Task | Title | Text |
|---|---|---|
| C1 | Register database | `docs/tasks/C1.md` |
| C2 | Firmware | `docs/tasks/C2.md` |
| C3 | Subsystem hardware model | `docs/tasks/C3.md` |
| C3a | Subsystem models, part 1 (mc, bar, imem, mmu, fb, top) | `docs/tasks/C3a.md` |
| C3b | Subsystem models, part 2 (privring, ltc, timer) | `docs/tasks/C3b.md` |
| C3c | Subsystem models, part 3 (fifo) | `docs/tasks/C3c.md` |
| C3d | Subsystem models, part 4 (the channel table) | `docs/tasks/C3d.md` |
| C3e | Subsystem models, part 5 (the GR engine) | `docs/tasks/C3e.md` |
| C4 | Design documents | `docs/tasks/C4.md` |
| C4a | Source provenance of the driver constants | `docs/tasks/C4a.md` |
| C4b | Design documents (MMU, FIFO, GR, firmware) | `docs/tasks/C4b.md` |
| C5 | Reference run under Linux and the first shader binary | `docs/tasks/C5.md` |
| C5a | Shader binary and launch descriptor of the reference run | `docs/tasks/C5a.md` |
| C5b | Summary of the register trace of the reference run | `docs/tasks/C5b.md` |
| C5c | What the trace shows from channel creation to the end of the job | `docs/tasks/C5c.md` |

## Phase D: host-side algorithms and tests

Plain C++17 built with `g++` on Ubuntu. `tests/Makefile` builds and runs
the tests. `make check` runs them.

| Task | Title | Text |
|---|---|---|
| D1 | Register access abstraction | `docs/tasks/D1.md` |
| D2 | GK104 page-table encoding | `docs/tasks/D2.md` |
| D3 | GPFIFO and push-buffer encoding | `docs/tasks/D3.md` |
| D4 | Register-trace comparison tool | `docs/tasks/D4.md` |
| D5 | Launch descriptor and compute method encoding | `docs/tasks/D5.md` |
| D6 | The launch descriptor against the reference run | `docs/tasks/D6.md` |
| R1 | Fix the defects that the external review found in the host code | `docs/tasks/R1.md` |

## Gate: end of phase D

The user reviews phases A-D before any Haiku work. Phases E-N (Haiku PCI
skeleton, MMIO, MC/FB/VRAM, MMU, FIFO/PBDMA, GPFIFO and submission to
milestone S1, copy engine to S2, GR/Falcon and first computation to S3,
interrupts, user-space API) are planned at the gate. They need a Haiku
boot and GPU access. `docs/PASSTHROUGH.md` describes how a test VM can
get one K40c, so that these phases do not need a reboot into Haiku. It
is prepared and not enabled.

## S1 preparation (after the gate, docs/S1-PLAN.md)

| Task | Title | Text |
|---|---|---|
| R1 | Fix the defects that the external review found in the host code | `docs/tasks/R1.md` |
| A3 | Inventory of the card's start-up script as it ran | `docs/tasks/A3.md` |
| S1A | Fix the defects of the scaffold review of 2026-10-21 | `docs/tasks/S1A.md` |
| S1B | Make every generated check run from sources that exist | `docs/tasks/S1B.md` |

## User-directed verification follow-up

| Task | Title | Text |
|---|---|---|
| V1 | Cardless S1 verification and backend boundary | `docs/tasks/V1.md` |
| V2 | Restore verification inputs and reproduce ROM decoding | `docs/tasks/V2.md` |
| ABC1 | User-directed cardless continuation across S1 tracks A/B/C | `docs/tasks/ABC1.md` |

See `docs/S1-VERIFICATION.md` for results, remaining gates and external-input blockers.
