# Haiku VM: summary for another session

Written 2026-10-15 on `uld-jvnhw22` (Ubuntu 22.04, kernel 6.8, 2 × Xeon E5-2620 v2, 62 GB).
Full record: `docs/HAIKU_ENVIRONMENT.md`. Short guide: `docs/HAIKU_BUILD_TEST.md`.

## In one paragraph

Haiku is not installed on the workstation. Haiku drivers are cross-compiled on
Ubuntu and tested in a throw-away Haiku VM (QEMU + KVM) that boots a nightly
image, downloads the driver, loads it, and prints the kernel log. **That VM has
no GPU.** A Haiku guest that receives the K40c does not exist yet (stage E0 of
`docs/S1-PLAN.md`). No root is needed for any of it.

## What exists

| Item | Value |
|---|---|
| Location | `~/haiku-cross` (12 GB), outside the repo; scripts find it via `HAIKU_CROSS` (`tools/haiku/config.sh`) |
| Rebuild from nothing | `tools/haiku/setup.sh` (no root, ~20 min, skips finished steps) |
| Haiku source (headers) | github.com/haiku/haiku `b42b90f5ec28` (2026-10-03), shallow |
| Cross compiler | GCC 13.3.0 + Binutils 2.41, `x86_64-unknown-haiku-`, in `~/haiku-cross/generated.x86_64/cross-tools-x86_64/bin/` |
| Host tools | bison, flex, m4, nasm unpacked into `~/haiku-cross/hosttools`; `source ~/haiku-cross/env.sh` |
| Test image | nightly `hrev60207` x86_64 anyboot, `~/haiku-cross/vm/…anyboot.iso`, sha256 `4cd0765e…0e35` |
| Kernel to link against | `~/haiku-cross/lib/kernel.so` (pulled from the running image; must match the image) |
| VM | QEMU 6.2, KVM, q35, OVMF UEFI, 2 vCPU, 2 GB, `-snapshot`, std VGA, e1000 user net, no display |

## What it can do

| Capability | How |
|---|---|
| Compile a kernel file | `tools/haiku/kcc -c file.c -o file.o` |
| Build a driver (legacy driver API) | `tools/haiku/build-driver.sh NAME a.c b.c` → `build/haiku/NAME`; `--no-undefined` against the image's kernel catches missing symbols on the host |
| Load a driver and read its log | `tools/haiku/vm-test.sh build/haiku/NAME [dev-subdir]`, ~2 min; output is the kernel log between `VMTEST-BEGIN`/`VMTEST-END` |
| Exit codes | 0 = commands ran (not "driver correct"), 1 = timeout, 3 = kernel panic |
| Prove the whole chain | `make haiku-selftest` must print `MMIO read16 [BAR2+0x500] = 0xb0c5` (PCI find + BAR map + MMIO read on the emulated VGA) |

How a test talks to the guest: HTTP server on host port 8000 (guest sees host
at `10.0.2.2`); keys typed through the QEMU monitor (`tools/haiku/qemu_hmp.py`)
because the image has no remote login; results via `-serial file:~/haiku-cross/vm/serial.log`.

## What it cannot do (yet)

- No GPU, by rule: `vm-test.sh` takes no QEMU options and must not be given host devices.
- Nothing persists between tests; no SSH; only the kernel log comes out.
- Haiku itself is not built from source; headers (source tree) and kernel (image) are close but not the same build.
- One test at a time (2 threads, 2 GB); it slows the local language model while running.

## Related guests

| Guest | Status |
|---|---|
| Ubuntu 24.04 with the K40c (`tools/guest/linux-run.sh --gpu`, SSH port 2222, card `0000:04:00.0` via vfio-pci, Nouveau + Mesa 25.2.8) | Works. Produced `reference/linux-run/` and `reference/linux-run-debug/` |
| Persistent Haiku install from the `haiku-k40c-llm` package (`tools/app_vm.py`: 32 GB qcow2, 4 GB, SSH on 127.0.0.1:2233, native GCC, ran llama.cpp CPU-only) | Uses **TCG (software emulation), not KVM**, so it is slow. Its disk (`haiku-k40c-llm/vm/system.qcow2`) is **not present** on this machine now; it would have to be reinstalled. Plan: reuse its approach with KVM for E0 |
| **Persistent cardless Haiku on KVM (added 2026-10-15)**, from the `opencode-haiku` package: `opencode-haiku/vm/system.qcow2` (32 GiB, GPT: 256 MiB FAT32 ESP + 31.75 GiB BFS), `tools/app_vm.py start --installed --kvm`, QEMU 6.2 `-accel kvm -cpu host`, 2 vCPU, 8 GiB, OVMF, e1000 user net, no SSH (jobs through a localhost HTTP runner), Haiku hrev60207, Node 24, GCC 13.3, Rust 1.94.1 | Works and persists. **KVM verified.** No GPU, none to be added. Full record: `opencode-haiku/docs/KVM-VM.md`. Caveats for reuse: the nightly installer leaves the ESP empty (copy `EFI/BOOT/BOOTX64.EFI` from the live ISO's ESP, see that file); the TCG VM from `haiku-k40c-llm` is still absent. Results of the OpenCode/llama.cpp tests on it: `opencode-haiku/docs/T7610-KVM-RESULTS-20261015.md`. Boot to desktop takes about 1 minute. This VM is a candidate base for stage E0 once a card is allowed (a **new** guest with the card would still be a separate user step) |
| Haiku guest with the K40c | Does not exist. Stage E0 of `docs/S1-PLAN.md` |

## Card and host state that matters

- Development card: K40c `0000:04:00.0`, IOMMU group 23, reserved for vfio-pci at boot. After every reboot run once: `sudo scripts/passthrough.sh attach` (for the chown).
- Model card: K40c `0000:03:00.0` runs `llama-server-one.service`; never touch it.
- The user decided (2026-10-13) the agent may start the Haiku guest with the card, under the limits in `docs/S1-PLAN.md` ("Limits for the agent starting the guest with the card"). Those limits must be in place before any hardware task.
- Known so far: the card is **not initialised** in a guest; the driver must run the VBIOS devinit scripts first. Planned approach is now a semantic devinit executor (not a flat replay). Board operations in the script (GPIO reset, MAX6649 limit writes, unknown I2C device 0x20, VGA ports) await the user's decision.
- No sudo in sessions: give the user exact root commands.
