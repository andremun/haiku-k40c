# A/B/C cardless work: outcome and machine handoff

2026-10-16. Work was undertaken to revise possible mistakes made by **"Local"**
and move closer to the **machine-dependent implementation**, as requested.
All hardware boundaries below remain explicit. HOST_ONLY/source/native-object
results are not K40c initialization, DMA, readiness or S1 evidence.

## Completed or advanced

| Plan step | Result in this pass | Remaining boundary |
|---|---|---|
| A1/A2 | Existing ROM identity verified; independent pinned decoder rebuilt and saved output reproduced | No new capture needed; decoded warnings remain documented |
| A3 | Independent rework passes reviewer counts, parser regressions and deterministic checks. Split COPY_NV_REG lines and synthetic repeat messages explained from ROM/source | The prescribed presentation inventory is not a bytecode decoder |
| A3/A4 supplement | Raw-ROM conservative structural traversal: 530 potential starts, 25 opcode values, all observed nonzero offsets covered, no structural issues in the selected POST roots | No evaluation of real conditions/helper effects or caller scripts outside POST; no readiness claim |
| A4 | NVIDIA/Nouveau/envytools source cross-reference and executor contract documented; compatibility differences and helper prerequisites recorded | Production helper/environment integration and review still required |
| A5 | Existing safety list retained and corrected: IO has GPU MMIO effects beyond VGA ports | User decisions on GPIO/thermal/I2C and unidentified 0x20 remain; default deny |
| A6 | 20 core opcode semantics plus 5 default-denied board/helper boundaries. Synthetic tests and 128 artificial real-ROM scenarios pass | Host-simulation-only hard gate; no production executor or A7 authorization |
| A7 preparation | Owned-scratch pattern/complement algorithm and alias-injection tests | Actual bring-up, scratch ownership, fault/readiness observations require the card |
| B1 | Existing R1 fixes rechecked; V1's additional corrections remain covered | No assertion that host checks prove driver/hardware behavior |
| B2 | Typed GPA/IOVA/physical-VRAM/GPU-VA separation, bounded writes, publication, submission pins and quarantine ownership | Native/GPU allocation, VMM serialization/mapping and real flush publication adapter not integrated |
| B3 | Native Haiku PCI/module/read-only BAR/host allocation/timing/cleanup code; both probe configurations compile, all four core C++ components compile; native backend has host failure-injection tests | Matching-kernel link/load remains pending; DMA addresses deliberately unverified |
| B4 | Fixed cardless disposable-overlay runner with host watchdog, incremental logs, restricted transfer endpoint and default read-only identity policy | Native load acceptance pending; hardware stage allow-lists/passthrough are not implemented or enabled |
| B5 | Not performed | Actual card identity/survey is a user-reviewed hardware step |
| C1 | Linux load-phase source-anchored survey: six anchors, 1456 chronological domain runs, generated checks | Not full semantic attribution of every write or a minimal-GR-free trace |
| C2 | Ordered integration recipe with domains, ownership, waits, faults, rollback and explicit stop gates | Full MMU/scratch/FIFO/channel recipe needs further integration and review; no guessed sequences substituted |
| C3 | Slow-window access, BAR flush, runlist commit, scratch check and S1 submission orchestration implemented/tested in simulation and cross-compiled | Full memory/FIFO/channel implementation, hardware quiescence and actual S1 pending |

## Important corrections

1. `0x002634` is **channel preemption**, not runlist start. Runlist commit uses
   `0x002270/0x002274`, with pending status at `0x002284 + id*8`.
2. Nouveau's `IO` instruction can write GPU registers and wait even when legacy
   VGA port routing seems irrelevant. It cannot simply be omitted on that basis.
3. The static preflight finds a potential `ZM_REG_GROUP` opcode absent from the
   observed run. Implementing only the 24 observed names would miss it.
4. The named/format-based inventory includes data-table rows. Its counts are
   task-format evidence, not proof of instruction boundaries or reachability.
5. A physical slow-window **read** writes its selector and is not a read-only
   hardware experiment. A BAR flush is separate from CPU ordering and MMU TLB
   invalidation. None of these steps alone proves memory readiness.
6. Release failures retain ownership and cannot produce a clean-teardown result.
   This applies to the host contract and the native OS mechanics.

## Main files

- `docs/DEVINIT-EXECUTOR.md`: compatibility rule, 25-opcode source cross-reference,
  host-only restrictions, missing hardware/helper integration.
- `analysis/devinit_inventory.*`, `analysis/devinit_preflight.json`,
  `analysis/devinit_sources.json`: generated observed/structural/source evidence.
- `docs/MEMORY-CONTRACT.md`, `src/memory/`: allocation ownership/address/publication.
- `src/os/HaikuBackend.*`, `HaikuProbe.c`: native OS mechanics and probes.
- `analysis/load_trace.*`, `docs/S1-RECIPE.md`, `src/runtime/Bootstrap.*`:
  load survey, gated integration recipe and tested source-backed primitives.
- `work/ABC1/RESULT.md`, `evidence.json`: commands, results, hashes and attempts.

## Reproduce host verification

The reference symlinks retain the package's original cache paths. Restore the
exact pins as documented in V2; do not use a different source revision merely
to make generated checks pass. On another user account, the reference paths must
resolve to a readable cache containing those same pins. No source tree is reset
by the restore helper.

```sh
python3 tools/restore_verification_refs.py
python3 -m venv build/verification-venv
build/verification-venv/bin/python -m pip install -r tools/verification-requirements.txt
export K40_VBIOS=/explicit/offline/path/to/the/verified.rom
export K40_DECODED=/explicit/offline/path/to/decoded/all.txt
python3 tools/devinit_inventory.py --check
python3 tools/devinit_preflight.py --check
python3 tools/devinit_sources.py --check
python3 tools/load_trace.py --check
PATH="$PWD/build/verification-venv/bin:$PATH" make check
```

The ROM is 181760 bytes, SHA-256
`aecb0b5fa466f64e2651a551a3cad57cccbdedd929e3996f542201af06ff1f54`.
The complete decoded output's SHA-256 is
`dce802b40173ececd2df0217e9e3adbb816614a64d7c0b0f1d00ad26646df0bf`.
Neither is committed/distributed with the source bundle. V2 documents rebuilding
the pinned decoder. Defaults use the user's `~/mediaflux/vbios/` copy.

The source-version audit supplement is incomplete: public v6.8 source downloads
were rate-limited (HTTP 429), and the stalled Git tag query was stopped. It
records missing sources, never "different" results. Later, when access is
available, `python3 tools/version_comparison.py --fetch` fills the ignored cache;
`--check` is offline and exits 2 while inputs are incomplete. Even completed
upstream comparison would not identify Ubuntu downstream source patches.

## Native build and cardless acceptance

No host sudo is needed. The local cross compiler was rebuilt successfully with
two build jobs at the exact commits already recorded by the package. Caches,
source checkouts, firmware-derived output and virtual disks stay outside Git.

```sh
bash tools/haiku/prepare_cross.sh
bash tools/haiku/prepare_cross.sh --check
bash tools/haiku/build_backend.sh --objects-only
```

These commands establish native-header/object compilation, not linking/loading.
`HAIKU_CROSS` defaults to `build/haiku-cross` in these new helper scripts; export
that same absolute directory when using the older `kcc`/`build-driver.sh` tools.
The original `vm-test.sh` QEMU command is unchanged and remains cardless/KVM-only.

To obtain the exact installed guest kernel using a working cardless guest:

```sh
python3 tools/haiku/cardless_run.py --base /path/to/installed/system.qcow2 --cpus 1 --timeout 600
```

This uses an ephemeral QCOW2 overlay and a copy of the guest's UEFI variables.
It takes no extra QEMU options and can never be given a physical GPU by this
interface. It defaults to TCG. An explicit `--kvm` selects KVM/host CPU only when the
user already has read/write access to `/dev/kvm`; it never uses sudo. On this host `/dev/kvm` is absent even outside the
sandbox. Inspect `build/cardless/RUN/result.json`, `serial.log`, `environment.txt`
and the uploaded kernel. A timeout is not acceptance. Preserve the kernel's
original SHA-256 and matching environment, then convert a copy for linking:

```sh
export HAIKU_CROSS="$PWD/build/haiku-cross"
cp build/cardless/RUN/kernel_x86_64 "$HAIKU_CROSS/lib/kernel_x86_64"
cp "$HAIKU_CROSS/lib/kernel_x86_64" "$HAIKU_CROSS/lib/kernel.so"
elfedit --output-type dyn "$HAIKU_CROSS/lib/kernel.so"
bash tools/haiku/build_backend.sh
python3 tools/haiku/cardless_run.py --base /path/to/installed/system.qcow2 --cpus 1 --driver build/haiku/k40_cardless_probe --timeout 600
```

Acceptance requires `job.exit` zero, matching environment/kernel evidence and
`k40_os: PASS` inside the completed serial-log markers, with no panic. The test
checks a contiguous host allocation, monotonic timer, PCI/module lifecycle and
read-only MMIO on the **emulated VGA**. It does not verify real K40c BAR mapping,
DMA or VRAM. The identity-configured probe is also built but is not authorized
for execution on physical hardware by this task.

On the T7610, use `--kvm --cpus 2` with a known-working cardless base when KVM
is already accessible. This branch is provided for manual validation; it was
not run here and does not authorize GPU assignment.

The current native-run outcome/attempts are recorded in `work/ABC1/RESULT.md`.
A working guest/KVM or manual T7610 kernel export may be needed to close the
native link/load gate; no stub kernel is substituted for a passing result.

## Remaining work

Keep board operations denied until the safety decision and complete helper
implementation. Resolve actual DMA addressing, pre-POST state and MMU scratch/
page-size/BAR/TLB dependencies; serialize and publish real owned tables. Finish
FIFO/channel/RAMFC/routing integration and define evidence for real quiescence.
Then review each first-write stage independently before A7/C3 card experiments.
GR omission, reset recovery, physical memory and actual S1 remain hardware
questions. No S2/S3 or llama GPU execution is claimed.

## Local review artifacts

After committing, `python3 tools/review_bundle.py` creates a source ZIP, an
opaque Git bundle and a revision/hash manifest under ignored `build/review/`.
`--check` verifies the committed revision and artifact hashes without writing.
The Git bundle can be copied manually to another machine; it is not a push.
Caches/virtual disks, the ROM and full decoder output are excluded. Restore
the exact external inputs before rerunning checks; no reviewer implementation
needs to be opened or inspected to use the normal make entry point.
