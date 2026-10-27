# Status

Current phase: S1 preparation (plan: docs/S1-PLAN.md)
Current task: S1OWNERTEST (cardless owner load and reload evidence). S1NATIVE is complete in the pending review batch.
Task state: S1NATIVE source/host/link scope DONE. Separate permanent owner and client ABI retain startup/quarantine state and deny DMA publication. Native load/reload remains unverified. Next: cardless owner test. No write stage is authorized.
Last updated: 2026-10-27

Setup from 2026-10-23: task work with Claude Code or Codex (cloud models). Driver card: K40c 0000:04:00.0. The K40c at 0000:03:00.0 runs `llm-server` in mode `one`. See `docs/decisions/003-end-local-agent-experiment.md`.

On 2026-10-26, `make refs`, `make check`, and both probe links passed on the T7610.
The restore helper was fixed for git 2.34's `--no-cone` sparse-pattern line.

Older results and notes: `docs/history/` (do not read it for a task).

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
| ABC1 | HOST WORK PASS (native gate closed by ESC-001 resolution) | 2026-10-16 | A/B/C host implementation, raw-ROM/source/trace checks, typed memory boundary, source-backed bootstrap/controller, native backend object compilation. Three cardless boot timeouts; no matching-kernel link/load, no hardware/S1 claim. See docs/ABC-CARDLESS-OUTCOME.md and escalations/ESC-001.md. |
| ESC-001 | RESOLVED | 2026-10-18 | Native link and load pass on the persistent KVM Haiku hrev60207 guest of `opencode-haiku` (`vm/system.qcow2`, disposable overlay). Exported kernel SHA-256 `2da9a5b9...`, byte-identical to `~/haiku-cross/lib/kernel_x86_64`; both probes link; the cardless probe loads with `k40_os: PASS`, job.exit 0, no panic. Identity probe not run. Evidence: `results/20261018-esc001-native-load/`. Cardless: not K40c evidence. See escalations/ESC-001.md, "Resolution". |
| S1A | DONE (host; probe link not run) | 2026-10-23 | ZM_REG bit 0 for `0x000200`, 0x91 and nv50.c cites, `s1a_accept` 8/8, K40c probe checks memory decode and PMC_BOOT_0. Probe link needs `~/haiku-cross` (T7610). See work/S1A/RESULT.md. |
| S1B | DONE (host; Mesa and VBIOS checks not run here) | 2026-10-23 | Restore helper checks sparse lists, required paths and the full envytools decoder checkout (`envytools_full()`). `devinit_sources.py` reads `nvbios.c` from it, output unchanged. `make check` runs six source and generator checks; three need the VBIOS and follow `.check-skip` A3. See work/S1B/RESULT.md. |
| S1C | DONE (small fixes included in S1B5 macro review) | 2026-10-27 | Correct VGA MMIO evidence and decision 4. Update S1 next steps and work roles. `make check` passes. See work/S1C/RESULT.md. |
| S1D | DONE (small fixes included in S1B5 macro review) | 2026-10-27 | Incorporate ADR 004 and align the board-operation document, plan, and status. `make check` passes. See work/S1D/RESULT.md. |
| S1B5 | ACCEPT (Claude Code, user-supplied review) | 2026-10-27 | Guarded launcher and identity-only Haiku stage pass. PMC_BOOT_0 HARDWARE_VERIFIED. Cardless rerun and host checks pass. See work/S1B5/RESULT.md. |
| S1BOARD | DONE (host only, batched review pending) | 2026-10-27 | Exact ROM policy, IO/CRTC/I2C/GPIO helpers, and host adapter. 20 trace accesses match. make check passes. See work/S1BOARD/RESULT.md. |
| S1B2 | DONE (native host/cardless scope, batched review pending) | 2026-10-27 | DMA32 allocator and ownership/mapping adapter. Cardless aligned readback and cleanup pass. IOVA publication remains closed by default. See work/S1B2/RESULT.md. |
| S1A4 | DONE (host candidate, batched review pending) | 2026-10-27 | Selected preinit lifecycle, one-shot controller, source-backed register helpers; 228 host checks. Physical I2C and readiness remain gated. See work/S1A4/RESULT.md. |
| S1C2 | DONE (source design, batched review pending) | 2026-10-27 | Mode 17, PDB invalidation, discovered routing, software-only group and release obligations; corrected timeout/scratch/DMA claims. See work/S1C2/RESULT.md. |
| S1A6 | DONE (host only, batched review pending) | 2026-10-27 | Deterministic POST input audit, exact board-policy binding, bounded dedicated I2C candidate; 908 wire checks and 10 input-audit tests. Native/hardware gates remain. See work/S1A6/RESULT.md. |
| S1NATIVE | DONE (source/host/native link, batched review pending) | 2026-10-27 | Separate KEEP_LOADED owner, client lease/handle API, one-shot/quarantine retention; 161 host checks and native link pass. No load/reload or DMA claim. See work/S1NATIVE/RESULT.md. |

## Steps for the T7610 after the alignment (2026-10-23)

1. Run `make refs`. It links `.refs` to `~/llm-server/agent-refs`, checks the pinned sources and needs the full envytools checkout `~/haiku-cross/src/envytools` (or `K40_ENVYTOOLS_FULL`).
2. Move the persistent VM disk folder from `opencode-haiku/vm/` to `~/haiku-vm`, or set `HAIKU_PERSISTENT_VM_DIR`.
3. Run `make check` and `make vm-tools-test`.
4. Run `~/llm-server/llm-mode.sh one`, so that no model runs on the driver card. Repeat after each reboot until `llm-server` starts in mode `one` by default.
5. Install Claude Code and Codex. Set the Codex sandbox of `docs/AGENT-SETUP.md`.

## Cardless native gate

The driver links and loads on a cardless KVM Haiku guest (ESC-001, resolved 2026-10-18).
`escalations/ESC-001.md` ("Resolution") and `docs/ABC-CARDLESS-OUTCOME.md` give the commands.
A cardless result is not K40c evidence.
