# ABC1 outcome: substantial cardless implementation; native/hardware gates open

2026-10-16 (Australia/Melbourne). Starting revision: `1a7f391`.
User request: complete feasible A/B/C work and report. Purpose: **revise possible
mistakes made by "Local" and approach machine-dependent implementation**.
The independent A3 rework did not use the rejected branch or read the reviewer
implementation. No subagents, host sudo, physical GPU access or push occurred.

## Delivered

- A3 observed/listing inventory rebuilt in four committed steps, deterministic
  checks and parser regressions. Eight disagreements are explained by repeat
  trace bookkeeping and split COPY_NV_REG presentation, with ROM/source proof.
- Raw-ROM structural preflight follows the main/extra POST roots and both
  conditional call/jump alternatives. Generated report: 530 potential starts,
  25 opcode values, no structural issues, every observed nonzero offset covered.
- Three-source cross-reference for observed/potential opcodes, compatibility
  design and a freestanding host-only interpreter: 20 core semantics plus five
  default-denied board/helper operations. Synthetic controls, failure budgets
  and 128 artificial real-ROM scenarios pass. Actual board effects are not
  emulated faithfully and hardware integration is explicitly refused.
- B2 typed ownership/address/publication boundary, quarantining uncertain GPU
  references and preventing release without quiescence. No device address is
  invented from a CPU pointer, host/GPA value or captured address.
- B3 native C OS/backend/probes, 64-bit BAR composition, bounded read-only maps,
  identity-only access policy, contiguous host allocation, timer/log/cleanup.
  Release failures retain ownership and prevent a passing cleanup result.
- Full pinned Haiku cross compiler rebuilt; backend, both probe configurations
  and all four freestanding C++ components compile against actual native headers.
- B4 disposable cardless runner: fixed cardless TCG/explicit-KVM options, restricted transfers,
  separate base/overlay/UEFI variables, incremental logs and host watchdog.
  Three startup attempts timed out; ESC-001 stops further VM variants.
- C1 load survey: six source anchors and 1456 chronological domain runs. Separate
  timestamp join covers 598 devinit intervals, zero skipped intervals with BAR
  accesses. Correlation is not causal attribution or complete helper coverage.
- C2 ordered gated recipe with ownership/address/wait/error/rollback obligations.
- C3 source-backed slow-window access, BAR flush, runlist commit and scratch
  pattern/complement/alias-check algorithm, alongside the existing S1 controller.
- Corrected preemption-vs-runlist, IO helper and TIME-unit mistakes in the plan/
  board documents. Version-comparison supplement explicitly remains incomplete
  after HTTP 429; no false equality/difference result was substituted.
- Reproducible source/kernel-toolchain helpers, source/constant provenance,
  manual machine handoff, and local committed-source review artifact builder.

## Verification commands

Run from this repository root. Build/cache/firmware artifacts stay ignored.
Exact hashes, compiler metadata and native-attempt manifests: `evidence.json`.

| Command | Result / scope |
|---|---|
| `python3 tools/devinit_inventory.py --check` (twice) | Pass; prescribed observed/presentation inventory |
| `python3 tools/devinit_preflight.py --check` | Pass; conservative raw-ROM structural scope |
| `python3 tools/devinit_sources.py --check` | Pass; source IDs/locations/hashes |
| `python3 tools/load_trace.py --check` | Pass; load-phase survey |
| `python3 tools/devinit_trace_join.py --check` | Pass; timestamp interval correlation |
| `python3 tools/provenance.py --check` | Pass; source-backed constant table |
| `PATH="$PWD/build/verification-venv/bin:$PATH" make check` | Full host checks pass; final handoff run recorded in evidence |
| `build/tests/test_devinit` | 33 synthetic checks pass; host simulation only |
| `python3 tests/test_devinit_rom.py` | 128 artificial scenarios pass using the actual ROM; dummy board callbacks; no hardware evidence |
| `build/tests/test_memory` | 39 ownership/publication checks pass |
| `build/tests/test_bootstrap` | 78 bootstrap/scratch/alias checks pass; host simulation only |
| `build/tests/test_s1_experiment` | Existing 58 controller checks pass; host only |
| `build/tests/test_haiku_backend` | 58 host failure-injection checks pass; mock headers are not native ABI evidence |
| `bash tools/haiku/prepare_cross.sh --check` | Exact pinned compiler/source inputs ready |
| `bash tools/haiku/build_backend.sh --objects-only` | Native objects compile with Werror; no kernel link/load claim |
| `bash tools/haiku/build_backend.sh` | Exit 2: matching guest kernel.so absent; no substitute link |
| `python3 tools/haiku/cardless_run.py ...` | Three bounded runs failed startup/job completion; no matching-kernel export or native load evidence |
| `python3 tools/version_comparison.py --check` | Exit 2: v6.8 cache unavailable following HTTP 429; comparison incomplete |
| `python3 tools/s1_verification_inputs.py --rom /explicit/verified/image --check` | Pass; report still marks matching-kernel input incomplete |
| Python compile checks / `git diff --check` | Pass |

All tests of core C++/host OS logic use UBSan through tests/Makefile. Existing
acceptance files are unchanged. No test was made to pass by copying reviewer
logic or suppressing a real failure. Initial parser-format/provenance errors,
a slow trace-name pass, and a misleading-indentation warning in the new host
fixture were corrected; the final source checks pass without warning bypasses.
A3's generated field names include historical "static_instructions" terminology;
the docs explicitly distinguish presentation rows from raw bytecode starts.

## Native attempts and escalation

See `escalations/ESC-001.md`. Attempts 1/2/3 used different memory/device/CPU
configurations but all remained cardless and host-bounded. A queued retry
worker correctly refused to overlap a still-running guest. KVM was verified
absent outside the sandbox. The failure cause remains unknown. This is a native
validation blocker, not evidence that the driver implementation or S1 is infeasible.

Compiler inputs: Haiku `b42b90f5ec2839f8074400c849ee025b50d0f7f1`, buildtools
`8375c2dbeaf109c520798cb234d57f0895463201`. Source refs retain the five exact
pins in reference/MANIFEST.md. No source/kernel patch was needed for the build.
Native kernel extraction or a working T7610 cardless run is the next prerequisite
for --no-undefined linking and actual driver loading.

## Still incomplete

A4/A6 production preinit/helper/register-translation integration and review;
A5 board permissions/device 0x20 identity; B2 actual GPU allocation/VMM/visibility
adapter; B3/B4 native matching-kernel link/load acceptance and hardware-stage
policy; C1 full causal load attribution; C2 complete scratch/page-size/BAR/TLB/
FIFO routing/channel recipe; C3 integration and real quiescence evidence.
No A7/B5/physical C3 experiment occurred. GR-free scheduling, reset recovery,
DMA/VRAM readiness and S1 remain card-dependent. No S2/S3/llama GPU claim.

Full per-track matrix and exact machine reproduction commands:
`docs/ABC-CARDLESS-OUTCOME.md`. Source ZIP/Git-bundle/manifest generation after
commit: `python3 tools/review_bundle.py`, then `--check`. It uses committed HEAD
only and excludes caches, disks, the ROM and full decoded firmware text.

The runner also provides an explicit --kvm branch for a machine where the user
already has access; it fails closed otherwise. This branch is SOURCE_ONLY here
and was not used for any of the three attempts. No fourth VM was started after
escalation. It makes the manual T7610 acceptance path concrete without changing
the original vm-test.sh or allowing arbitrary QEMU/host-device arguments.
