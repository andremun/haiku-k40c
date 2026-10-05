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
  A test on the real card is a user step (phases E and later).
- Run one VM test at a time. A test uses 2 CPU threads and 2 GB of memory
  and slows the language model while it runs.
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

## Setup record (done 2026-10-05, in `~/haiku-cross`, not in this repository)

| Part | Detail |
|---|---|
| Haiku source | github.com/haiku/haiku, commit b42b90f5ec2839f8074400c849ee025b50d0f7f1 (2026-10-03), shallow clone |
| Build tools | github.com/haiku/buildtools, commit 8375c2dbeaf109c520798cb234d57f0895463201; GCC 13.3.0, target `x86_64-unknown-haiku` |
| Cross compiler build | `haiku/configure --cross-tools-source ../buildtools --build-cross-tools x86_64` |
| Host tools without root | `bison`, `flex`, `m4`, `nasm` unpacked from Ubuntu packages into `~/haiku-cross/hosttools` (`source ~/haiku-cross/env.sh`) |
| Test image | Haiku nightly hrev60207 x86_64 (`anyboot`), SHA-256 checked against the published value |
| `kernel.so` | The image's own `/boot/system/kernel_x86_64`, copied out of the running VM and converted with `elfedit --output-type dyn`. It must match the image: replace both together. |
| VM | QEMU 6.2 with KVM, UEFI (OVMF), 2 CPUs, 2 GB, emulated VGA and e1000 |

The scripts find these through `HAIKU_CROSS` (default `~/haiku-cross`),
see `tools/haiku/config.sh`.

GPU passthrough is possible on this machine but is not set up: each K40c
is alone in its IOMMU group (0000:04:00.0 in group 23, 0000:81:00.0 in
group 2). It needs root and takes a card away from the language model.
