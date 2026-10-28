# Building and testing Haiku kernel code on this machine

The Linux host can compile a Haiku kernel driver, link it, and load it in
a Haiku virtual machine. No GPU is involved. Scripts: `tools/haiku/`.

| Step | Command | Result |
|---|---|---|
| Compile one file | `tools/haiku/kcc -c file.c -o file.o` | Object file, checked against the real Haiku headers |
| Build a driver | `tools/haiku/build-driver.sh NAME a.c b.c` | `build/haiku/NAME` |
| Load it in Haiku | `tools/haiku/vm-test.sh build/haiku/NAME` | The kernel log lines from the load (about 2 minutes) |
| Self-test of the chain | `make haiku-selftest` | Must print `MMIO read16 [BAR2+0x500] = 0xb0c5` |

## Rules

- The VM has no access to the K40c cards. `vm-test.sh` takes no QEMU
  options. Never add host devices (`vfio-pci`, `-device ...,host=`) to it.
  The separate `card_run.py` launcher handles read-only B5 under ADR 005.
- Run one VM test at a time. A test uses 2 CPU threads and 2 GB of memory
  and slows the `llm-server` model on the T7610 while it runs.
- A driver reports through `dprintf`. Everything between `VMTEST-BEGIN`
  and `VMTEST-END` is printed; the full log is `~/haiku-cross/vm/serial.log`.
- `vm-test.sh` exits 0 when the test commands ran, 1 on a timeout and 3 on
  a kernel panic. Exit 0 does not mean the driver is correct: read the log.
- Each test boots from a throw-away snapshot. Nothing persists in the VM.

## What the VM can and cannot show

| It can show | It cannot show |
|---|---|
| The driver compiles against Haiku's headers | Anything about the K40c: no NVIDIA device exists in the VM |
| It links: every kernel symbol it uses exists | Register values, timing or firmware behaviour of the card |
| The kernel loads it; `init_driver` runs; no panic | Interrupts from the card, DMA, VRAM |
| PCI enumeration and MMIO mapping code paths work (on the emulated VGA device `1234:1111`) | |

A result from the VM is at most evidence for the Haiku side of the code.
It never raises a register's status to HARDWARE_VERIFIED or
HAIKU_VERIFIED.

## Driver conventions that the toolchain expects

- Legacy driver interface: `api_version`, `init_hardware`, `init_driver`,
  `uninit_driver`, `publish_devices`, `find_device`. Example:
  `tools/haiku/selftest/hello_pci.c`.
- Kernel add-ons are position-independent code (the compiler default). Do
  not use `-fno-pic` or `-mcmodel=kernel`.
- The link uses `--no-undefined` against `kernel.so`. A function that the
  kernel does not export fails at link time, not at load time.
- devfs loads a driver when its directory under `/dev` is listed. The
  second argument of `vm-test.sh` selects that directory (default `misc`).

## Setup record (in `~/haiku-cross`, not in this repository)

`tools/haiku/setup.sh` builds all of it again from nothing (no root, about
20 minutes, 3.7 GB). It skips the steps that are complete. First done
2026-10-05; built again with the script's steps 2026-10-07 after the
machine was reinstalled, and `make haiku-selftest` passed.

| Part | Detail |
|---|---|
| Haiku source | github.com/haiku/haiku, commit b42b90f5ec2839f8074400c849ee025b50d0f7f1 (2026-10-03), shallow clone |
| Build tools | github.com/haiku/buildtools, commit 8375c2dbeaf109c520798cb234d57f0895463201; GCC 13.3.0, target `x86_64-unknown-haiku` |
| Cross compiler build | In `~/haiku-cross/generated.x86_64`: `../haiku/configure --cross-tools-source ../buildtools --build-cross-tools x86_64`. Run from another directory, it writes the tools there. |
| Host tools without root | `bison`, `flex`, `m4`, `nasm` unpacked from Ubuntu packages into `~/haiku-cross/hosttools` (`source ~/haiku-cross/env.sh`). `nasm` comes from the mirror by URL: `apt-get download` selects an ESM version that needs a login. |
| Test image | Haiku nightly hrev60207 x86_64 (`anyboot`), SHA-256 checked against the published value |
| `kernel.so` | The image's own `/boot/system/kernel_x86_64`, copied out of the running VM and converted with `elfedit --output-type dyn`. It must match the image: replace both together. |
| VM | QEMU 6.2 with KVM, UEFI (OVMF), 2 CPUs, 2 GB, emulated VGA and e1000 |

The scripts find these through `HAIKU_CROSS` (default `~/haiku-cross`),
see `tools/haiku/config.sh`.

Read-only Haiku passthrough is authorized by ADR 005. The user already bound
`0000:04:00.0` to VFIO. The launcher checks binding, group isolation, and access.
The card at `0000:03:00.0` runs `llm-server` and is never passed through.
No agent step changes host binding or uses root.

## Persistent cardless VM

`tools/haiku/` also holds the tools for the persistent Haiku VM that the
`haiku-k40c-llm` and `opencode-haiku` repositories use for their test runs.
This repository owns them (`docs/decisions/001-vm-tools-owner.md`).

| Tool | Use |
|---|---|
| `app_vm.py` | Start, inspect, type into, click and stop the VM. `--kvm` uses KVM with `-cpu host`. The monitor sockets are `monitor.sock` and `monitor.sock.qmp` in the VM folder. |
| `transfer_server.py` | Localhost file service for the guest. `--root` names the work folder, `--results` the results folder. A job log in `logs/` is written once (a retry with the same bytes is accepted). `--max-total` limits all uploads of one run. `--port 0 --port-file FILE` takes a free port. |
| `job.sh` | Run one shell job in the guest and wait for `exit=N`. |
| `cardless_run.py` | Boot a disposable overlay of the VM disk and load a driver probe. |

The VM disk is outside every repository, in `$HAIKU_PERSISTENT_VM_DIR` (default
`~/haiku-vm`): `system.qcow2`, `vars.fd` and, for a first install, the pinned
hrev60207 anyboot ISO. The same rule as for `vm-test.sh` applies: no host device
is ever given to the VM by these tools.


## B5 identity stage with the development card

Build and validate the B5-tagged probe:

```sh
HAIKU_CROSS="$HOME/haiku-cross" bash tools/haiku/build_backend.sh
python3 tools/haiku/probe_stage.py build/haiku/k40_identity_probe --check
python3 tools/haiku/card_run.py --check
```

`--check` reads host inventory and stage metadata. It does not start a guest.
`GPU_BDF` must equal `0000:04:00.0`. Other values fail before launch.
The stage metadata binds the ELF hash, source hashes, and matching guest kernel hash.
`probe_stage.py --check` compares the exact generated metadata without writing.

Run the stage once:

```sh
python3 tools/haiku/card_run.py --timeout 600
```

The default evidence folder is `results/YYYYMMDD-b5-identity/`.
The launcher refuses an existing evidence folder. It saves command, stage,
source commit, host isolation, serial log, HTTP log, and result as the run proceeds.
The disk overlay and copied driver stay under `build/b5/`. The base disk stays unchanged.
`HAIKU_PERSISTENT_VM_DIR` selects the base folder. `HAIKU_OVMF_DIR` selects the firmware folder.
No additional QEMU options are accepted.

The shared launch lock and host QEMU inventory enforce one guest at a time.
Ask before stopping an existing VM. A separate watchdog enforces at most ten minutes,
even if the launcher exits. It signals the exact process through a Linux pidfd.
A panic, hang, failed probe, or unexpected identity ends the run. Stop and report without a modified retry.

B5 reads the PCI command register and refuses mapping if memory decode is off.
It maps BAR0 read-only and reads only PMC_BOOT_0. It never uses the slow window.
A pass is HARDWARE_VERIFIED only for PMC_BOOT_0 under Haiku. It proves no DMA,
bring-up, scheduling, or compute support. Cardless results remain Haiku OS evidence only.

Run host launcher and shared-tool tests with `make vm-tools-test`.
Do not run `scripts/passthrough.sh`, Linux `--gpu`, or a write stage under this permission.

## Cardless native memory adapter check

`build_backend.sh` now also links `build/haiku/k40_memory_probe`.
This C++ probe exercises the native DMA32 allocator and typed memory adapter.
It checks aligned guest physical storage, byte readback, default-denied IOVA publication,
and successful cleanup. It does not enumerate PCI devices or touch a GPU.

```sh
HAIKU_CROSS="$HOME/haiku-cross" bash tools/haiku/build_backend.sh
python3 tools/haiku/cardless_run.py --kvm --driver build/haiku/k40_memory_probe
```

The existing cardless runner installs the binary under its fixed probe filename.
It accepts the probe's `k40_os: PASS` marker. Evidence remains under `build/cardless/`.
A reported stop requires user approval before another run (ADR 006).
The probe's successful path proves native allocation mechanics only.
It does not validate production pool lifetime, quarantine recovery, DMA, or IOVA equality.

## Permanent owner module: build only

S1NATIVE adds `k40_owner_module`, built with the command in
`docs/NATIVE-OWNER.md`. It links against the matching kernel. S1OWNERTEST later loaded it with the
separate owner-client probe described below. It is a kernel module, not a device-node probe. Do not feed
it to cardless_run.py as a legacy driver. Use the owner staging flag below to pair it with the client and strict reload
validation.
The B5 and cardless launcher commands are unchanged.

## Cardless owner module and reload probe

S1OWNERTEST adds a separate owner-client probe and an optional fixed staging mode.
Build the owner with the command in docs/NATIVE-OWNER.md, then build its client:

```sh
HAIKU_CROSS="$HOME/haiku-cross" KCFLAGS='-Werror -Isrc' \
  bash tools/haiku/build-driver.sh k40_owner_probe \
  src/os/OwnerClient.cpp tools/haiku/selftest/owner.cpp
python3 tools/haiku/cardless_run.py --kvm \
  --driver build/haiku/k40_owner_probe --owner-module build/haiku/k40_owner_module
```

The owner flag requires both matching ELF roles. The job uses finddir for the
user nonpackaged add-on path, stages generic/k40c_owner before the client, and
lists the test device directory four times. Empty-device clients unload after
publication, as specified in pinned legacy_drivers.cpp:300-355. The owner remains
a separate KEEP_LOADED module. QEMU options and the base disk are unchanged.

Owner-mode success requires actual ordered init/uninit markers, an advancing
lease, the same retained token, failed startup state and one quarantined record,
plus native host-byte cleanup and denied publication. Missing/malformed reload
evidence is a failure even if another probe printed PASS. Launch evidence records
both ELF hashes, source commit and expected kernel hash. The uploaded guest kernel
must match. A reported stop requires user approval before another run.
This is a cardless lifetime test, not physical DMA or GPU bring-up evidence.

S1OWNERTEST's first prepared run passed in 52.57 seconds. Evidence is in
`results/20261027-owner-reload/`. Both client uninit calls and the reload are
recorded; lease 2 retains token 2, Failed state and one quarantine record.
This validates the tested native owner lifetime, not DMA or GPU readiness.

## Exact A7 installation rehearsal without a card

After building the candidate A7 package, run:

```sh
export K40_VBIOS="$HOME/haiku-cross/vbios/k40c-0000_04_00_0-vbios-80.80.65.00.01.rom"
python3 tools/a7/rehearse.py
python3 tools/a7/rehearse.py --check
python3 tools/a7/build.py --check
```

The rehearsal runs the production guest job generator and its exact owner,
client and identity binaries in a disposable cardless KVM guest. It supplies
no VFIO device, grant key, grant or card permit. It preserves serial, HTTP,
shell, kernel-hash and command evidence under results/*-a7-rehearsal/.

A pass requires three checked installations with unchanged rename inodes,
device-node publication and the specific native no-card refusal before PCI
reservation. Preparation occurs inside the open callback, so shell open must
fail after entering that callback. A missing node or generic open error fails.
The no-card identity-probe failure is expected. No POST or readiness runs.

Build and physical-launcher checks require the saved matching rehearsal binding.
Changed job bytes or binaries require another cardless rehearsal. Failed
cardless rehearsals may be retried under the user's ESC-003 resolution.
Physical A7 still requires Claude review and a separate explicit per-run yes.
See docs/A7-REVIEW-PACKAGE.md and work/S1A7REHEARSAL/REVIEW-RESOLUTION.md.
